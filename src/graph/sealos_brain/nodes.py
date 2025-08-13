"""
Nodes (entry, compose, summarize) for the New Project agent.
"""

from typing_extensions import Literal
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from langchain_tavily import TavilySearch

from src.provider.backbone_provider import get_sealos_model
from src.utils.context_utils import get_state_values, get_copilot_actions
from copilotkit.langgraph import (
    copilotkit_customize_config,
    copilotkit_emit_state,
    copilotkit_exit,
)
from src.prompts.sealos_brain_prompts import (
    SUMMARIZE_PROJECT_PROMPT,
    EXISTING_PROJECT_PLAN_TEMPLATE,
    ROUTE_ONLY_EXISTING_PROJECT_PROMPT,
    ROUTE_ONLY_NEW_PROJECT_PROMPT,
    GREETING_MESSAGE_PROMPT,
    PROJECT_BRIEF_GENERATION_PROMPT,
    PROJECT_BRIEF_MODIFICATION_PROMPT,
    MANAGE_RESOURCE_PROMPT,
)

from src.graph.sealos_brain.schemas import ProjectPlan, RouteOnly, ProjectRequirements
from src.graph.sealos_brain.state import SealosBrainState


async def entry_node(
    state: SealosBrainState, config: RunnableConfig
) -> Command[Literal["compose_project_brief", "manage_resource", "__end__"]]:
    await copilotkit_exit(config)

    (
        messages,
        base_url,
        api_key,
        model_name,
        project_context,
        project_plan,
    ) = get_state_values(
        state,
        {
            "messages": [],
            "base_url": None,
            "api_key": None,
            "model": None,
            "project_context": None,
            "project_plan": None,
        },
    )

    print("project_context", project_context)

    has_existing_project = (
        project_plan and hasattr(project_plan, "name") and project_plan.name
    )

    modified_config = copilotkit_customize_config(
        config, emit_messages=False, emit_tool_calls=False
    )

    # STEP 1: Route Decision Only - Use gpt-5-nano for routing
    route_model = get_sealos_model("gpt-4o", base_url, api_key)
    route_structured = route_model.with_structured_output(RouteOnly)

    if has_existing_project:
        route_system = SystemMessage(content=ROUTE_ONLY_EXISTING_PROJECT_PROMPT)

        # Format current project plan details for context
        resources = project_plan.get("resources", {})
        devboxes = getattr(resources, "devboxes", []) if resources else []
        databases = getattr(resources, "databases", []) if resources else []
        buckets = getattr(resources, "buckets", []) if resources else []

        devboxes_summary = (
            ", ".join([f"{box.runtime}" for box in devboxes]) if devboxes else "None"
        )
        databases_summary = (
            ", ".join([f"{db.type}" for db in databases]) if databases else "None"
        )
        buckets_summary = (
            ", ".join([f"{bucket.policy}" for bucket in buckets]) if buckets else "None"
        )

        plan_details = EXISTING_PROJECT_PLAN_TEMPLATE.format(
            project_name=project_plan.get("name", "Unnamed Project"),
            project_description=project_plan.get("description", "No description"),
            project_status=project_plan.get("status", "Unknown"),
            devboxes_summary=devboxes_summary,
            databases_summary=databases_summary,
            buckets_summary=buckets_summary,
        )

        additional_context = SystemMessage(content=plan_details)

        # Add project context from state if available
        if project_context:
            project_context_message = SystemMessage(
                content=f"PROJECT CONTEXT:\n{project_context}"
            )
            route_messages = [
                route_system,
                project_context_message,
                additional_context,
                *messages,
            ]
        else:
            route_messages = [route_system, additional_context, *messages]
    else:
        route_system = SystemMessage(content=ROUTE_ONLY_NEW_PROJECT_PROMPT)

        # Add project context from state if available
        if project_context:
            project_context_message = SystemMessage(
                content=f"PROJECT CONTEXT:\n{project_context}"
            )
            route_messages = [route_system, project_context_message, *messages]
        else:
            route_messages = [route_system, *messages]

    # Get routing decision
    route_decision: RouteOnly = await route_structured.ainvoke(
        route_messages, config=modified_config
    )

    # STEP 2: Generate Content Based on Route
    if route_decision.next_node == "compose_project_brief":
        # Route to the new compose_project_brief node and set project brief status to active
        state["project_brief"] = {"briefs": [], "status": "active"}
        await copilotkit_emit_state(config, state)

        return Command(
            goto="compose_project_brief",
            update={"project_brief": {"briefs": [], "status": "active"}},
        )
    elif route_decision.next_node == "manage_resource":
        # Route to resource management node
        return Command(goto="manage_resource")
    else:
        # Generate greeting message
        content_model = get_sealos_model("gpt-4o", base_url, api_key)

        # Build greeting message list with project context if available
        greeting_messages = [SystemMessage(content=GREETING_MESSAGE_PROMPT)]
        if project_context:
            project_context_message = SystemMessage(
                content=f"PROJECT CONTEXT:\n{project_context}"
            )
            greeting_messages.append(project_context_message)
        greeting_messages.extend(messages)

        greeting_response = await content_model.ainvoke(
            greeting_messages,
            config=modified_config,
        )

        updated_messages = [*messages, AIMessage(content=greeting_response.content)]
        return Command(goto="__end__", update={"messages": updated_messages})


async def compose_project_brief(
    state: SealosBrainState, config: RunnableConfig
) -> Command[Literal["compose_new_project"]]:
    """
    Generate project brief requirements based on user input.
    This node creates structured requirement sentences for the project.
    """
    (
        messages,
        base_url,
        api_key,
        model_name,
        project_plan,
    ) = get_state_values(
        state,
        {
            "messages": [],
            "base_url": None,
            "api_key": None,
            "model": None,
            "project_plan": None,
        },
    )

    has_existing_project = (
        project_plan and hasattr(project_plan, "name") and project_plan.name
    )

    modified_config = copilotkit_customize_config(
        config, emit_messages=False, emit_tool_calls=False
    )

    # Use gpt-5-mini for content generation with structured output
    content_model = get_sealos_model("gpt-4o", base_url, api_key)
    structured_content = content_model.with_structured_output(ProjectRequirements)

    # Generate project brief requirements
    if has_existing_project:
        content_prompt = PROJECT_BRIEF_MODIFICATION_PROMPT
    else:
        content_prompt = PROJECT_BRIEF_GENERATION_PROMPT

    requirements_response: ProjectRequirements = await structured_content.ainvoke(
        [SystemMessage(content=content_prompt), *messages], config=modified_config
    )

    # Get the structured requirements list
    requirements_list = requirements_response.requirements

    # Resource minimization and modern tech stack optimization
    optimized_requirements = await _optimize_requirements(
        requirements_list, content_model, modified_config
    )

    state["project_brief"] = {"briefs": optimized_requirements, "status": "completed"}
    # await asyncio.sleep(2)
    state["project_plan"] = {
        "name": project_plan.get("name", "Unnamed Project"),
        "description": project_plan.get("description", "No description"),
        "resources": project_plan.get("resources", {}),
        "status": "active",
    }
    await copilotkit_emit_state(config, state)

    return Command(
        goto="compose_new_project",
        update={
            "project_brief": {"briefs": optimized_requirements, "status": "completed"},
            "project_plan": {
                "name": project_plan.get("name", "Unnamed Project"),
                "description": project_plan.get("description", "No description"),
                "resources": project_plan.get("resources", {}),
                "status": "active",
            },
        },
    )


async def _optimize_requirements(
    requirements: list[str], model, config: RunnableConfig
) -> list[str]:
    """
    Optimize requirements to minimize resources and use modern tech stacks.
    """
    if not requirements:
        return requirements

    # Create optimization prompt
    optimization_prompt = f"""
You are a cloud resource optimization expert. Analyze these project requirements and optimize them to:

1. MINIMIZE RESOURCES: Use the fewest possible DevBoxes, Databases, and Buckets
2. MODERN TECH STACK: Prefer modern technologies over older ones
3. CONSOLIDATE: Combine similar requirements where possible

Current requirements:
{chr(10).join(requirements)}

Optimization rules:
- DevBoxes: Prefer Next.js over PHP, React over jQuery, Node.js over older runtimes
- Databases: Use one database type when possible, prefer PostgreSQL over MySQL
- Buckets: Consolidate storage needs into fewer buckets
- Remove redundant or overlapping requirements
- Keep only essential, non-negotiable requirements

Return 2-6 optimized requirement sentences, one per line, without numbering or bullets.
Focus on what's absolutely necessary for the project to function.
"""

    try:
        # Get optimized requirements from the model
        optimization_response = await model.ainvoke(
            [SystemMessage(content=optimization_prompt)], config=config
        )

        # Split the response into individual requirements
        optimized_text = optimization_response.content.strip()
        optimized_requirements = [
            req.strip()
            for req in optimized_text.split("\n")
            if req.strip()
            and not req.strip().startswith(("-", "•", "*", "1.", "2.", "3."))
        ]

        # Fallback to original requirements if optimization fails
        if not optimized_requirements:
            return requirements

        return optimized_requirements[:6]  # Limit to 6 requirements max

    except Exception:
        # If optimization fails, return original requirements
        return requirements


async def compose_new_project(
    state: SealosBrainState, config: RunnableConfig
) -> Command[Literal["summarize_project"]]:
    (
        project_brief,
        project_plan,
        base_url,
        api_key,
        model_name,
    ) = get_state_values(
        state,
        {
            "project_brief": {"briefs": [], "status": "pending"},
            "project_plan": None,
            "base_url": None,
            "api_key": None,
            "model": None,
        },
    )

    model = get_sealos_model(model_name, base_url, api_key)
    structured = model.with_structured_output(ProjectPlan)

    # Check if there's an existing project plan
    has_existing_project = (
        project_plan and hasattr(project_plan, "name") and project_plan.name
    )

    # Enhanced prompt that focuses on user's request rather than specific technologies
    if has_existing_project:
        enhanced_prompt = f"""You are a Sealos cloud architect modifying an existing project plan. 

EXISTING PROJECT CONTEXT:
- Current Name: {project_plan.get('name', 'Unnamed Project')}
- Current Description: {project_plan.get('description', 'No description')}
- Current Resources: {project_plan.get('resources', 'No resources')}

MODIFICATION REQUIREMENTS:
1. STRICTLY FOLLOW the project brief requirements - they are the new specifications
2. Modify the existing project to align with the new brief while maintaining continuity
3. Keep existing resources that are still relevant to the new brief
4. Add new resources only if explicitly required by the brief
5. Remove resources that are no longer needed based on the new brief
6. Update the project name and description to reflect the new requirements

PROJECT NAMING GUIDELINES:
- Update name to reflect the new purpose from the brief
- Avoid technical terms like "Next.js App", "WordPress Site", "React Dashboard"
- Use descriptive, user-focused names that explain what the project does

PROJECT DESCRIPTION GUIDELINES:
- Update description to match the new brief requirements
- Focus on what users will be able to do with the modified project
- Avoid technical implementation details
- Keep it simple and clear

RESOURCE MODIFICATION GUIDELINES:
- Preserve existing resources that align with the new brief
- Add new resources only if the brief explicitly requires them
- Remove or replace resources that conflict with the new brief
- Maintain minimal resource usage - use as FEW resources as possible

Return structured data with: name, description, and resources arrays. Ensure the plan strictly adheres to the project brief."""
    else:
        enhanced_prompt = """You are a Sealos cloud architect. Design a MINIMAL resource plan using the least resources possible.

CRITICAL REQUIREMENTS:
1. Use as FEW resources as possible. Only add resources if absolutely necessary.
2. Focus on WHAT the user wants to build, not HOW to build it.
3. Avoid mentioning specific brand names, frameworks, or technologies in the project name and description.
4. STRICTLY FOLLOW the project brief requirements - they are the specifications

PROJECT NAMING GUIDELINES:
- Name should describe the PURPOSE or TYPE of project (e.g., "Shopping Site", "Blog Platform", "API Service")
- Avoid technical terms like "Next.js App", "WordPress Site", "React Dashboard"
- Use descriptive, user-focused names that explain what the project does

PROJECT DESCRIPTION GUIDELINES:
- Describe the project's PURPOSE and FUNCTIONALITY based on the brief
- Focus on what users will be able to do with it
- Avoid technical implementation details
- Keep it simple and clear

RESOURCE GUIDELINES:
- DevBoxes: Choose ONE runtime that can handle the entire project
- Databases: Only add if data persistence is explicitly required by the brief. Choose ONE database type maximum
- Buckets: Only add if file/media storage is explicitly mentioned in the brief

Examples of good naming:
- Name: "Shopping Site" (not "Next.js E-commerce App")
- Description: "An online store for selling products with user accounts and order management"
- Name: "Blog Platform" (not "WordPress Blog")
- Description: "A content management system for publishing articles and managing blog posts"

Return structured data with: name, description, and resources arrays. Ensure the plan strictly adheres to the project brief."""

    system = SystemMessage(content=enhanced_prompt)

    modified_config = copilotkit_customize_config(
        config, emit_messages=False, emit_tool_calls=False
    )

    # Join all briefs into a single string for the LLM
    briefs_text = "\n".join(project_brief.get("briefs", []))

    # Prepare context message with emphasis on following the brief
    if has_existing_project:
        context_message = f"""
CRITICAL: The following project brief contains the NEW REQUIREMENTS that must be implemented.
These requirements take priority and should guide all modifications to the existing project.

PROJECT BRIEF (NEW REQUIREMENTS):
{briefs_text}

You must modify the existing project plan to fully satisfy these new requirements while maintaining any existing resources that are still relevant."""
    else:
        context_message = f"""
CRITICAL: The following project brief contains the EXACT REQUIREMENTS that must be implemented.
Every requirement in this brief must be addressed in your resource plan.

PROJECT BRIEF (REQUIREMENTS):
{briefs_text}

You must create a project plan that fully satisfies all these requirements."""

    plan: ProjectPlan = await structured.ainvoke(
        [system, SystemMessage(content=context_message)],
        config=modified_config,
    )

    # current_state = {
    #     **state,
    #     "project_plan": {
    #         "name": plan.name,
    #         "description": plan.description,
    #         "resources": plan.resources,
    #         "status": "completed",
    #     },
    # }
    state["project_plan"] = {
        "name": plan.name,
        "description": plan.description,
        "resources": plan.resources,
        "status": "completed",
    }
    await copilotkit_emit_state(config, state)

    return Command(
        goto="summarize_project",
        update={
            "project_plan": {
                "name": plan.name,
                "description": plan.description,
                "resources": plan.resources,
                "status": "completed",
            }
        },
    )


async def summarize_project(
    state: SealosBrainState, config: RunnableConfig
) -> Command[Literal["__end__"]]:
    (
        project_brief,
        project_plan,
        base_url,
        api_key,
        model_name,
    ) = get_state_values(
        state,
        {
            "project_brief": {"briefs": [], "status": "pending"},
            "project_plan": {
                "name": "",
                "description": "",
                "resources": None,
                "status": "pending",
            },
            "base_url": None,
            "api_key": None,
            "model": None,
        },
    )

    model = get_sealos_model(model_name, base_url, api_key)

    system = SystemMessage(content=SUMMARIZE_PROJECT_PROMPT)

    # Format resources for better readability
    resources = project_plan.get("resources")
    if resources and hasattr(resources, "devboxes"):
        devboxes = resources.devboxes or []
        databases = resources.databases or []
        buckets = resources.buckets or []
    else:
        devboxes = []
        databases = []
        buckets = []

    # Join all briefs into a single string
    briefs_text = "\n".join(project_brief.get("briefs", []))

    summary_prompt = f"""
Project Brief: {briefs_text}

RECOMMENDED SEALOS RESOURCE PLAN:
Project Name: {project_plan.get('name', 'Unnamed Project')}
Description: {project_plan.get('description', 'No description provided')}

DevBoxes (Development Environments):
{chr(10).join([f"- {box.runtime}: {box.description}" for box in devboxes]) if devboxes else "- None recommended"}

Databases:
{chr(10).join([f"- {db.type}: {db.description}" for db in databases]) if databases else "- None recommended"}

Object Storage Buckets:
{chr(10).join([f"- {bucket.policy} policy: {bucket.description}" for bucket in buckets]) if buckets else "- None recommended"}

Provide a sentence explaining the rationale and specific usage guidance, for example, devbox could be the main development environment, database could be the main database, etc.

After the explanation, add a simple sentence encouraging the user to press the create button to deploy this project and continue chatting to refine the plan further.
"""

    modified_config = copilotkit_customize_config(
        config, emit_messages=False, emit_tool_calls=False
    )

    summary = await model.ainvoke(
        [system, SystemMessage(content=summary_prompt)], config=modified_config
    )

    # Mark project brief and plan as completed
    return Command(
        goto="__end__",
        update={
            "messages": [AIMessage(content=summary.content)],
        },
    )


# Tools for the resource management node
tool = TavilySearch(max_results=2)
tools = [tool]


async def manage_resource(
    state: SealosBrainState, config: RunnableConfig
) -> Command[Literal["tool_node", "__end__"]]:
    """
    Resource management node based on the Sealos AI functionality.
    Handles model binding, system prompts, Sealos context, and tool calls.
    """
    # Extract state data
    (
        messages,
        base_url,
        api_key,
        model_name,
        project_context,
    ) = get_state_values(
        state,
        {
            "messages": [],
            "base_url": None,
            "api_key": None,
            "model": None,
            "project_context": None,
        },
    )

    model = get_sealos_model(model_name, base_url, api_key)

    all_tools = tools + get_copilot_actions(state)

    model_with_tools = model.bind_tools(all_tools, parallel_tool_calls=False)

    # Build messages with system prompt for resource management
    system_message = SystemMessage(content=MANAGE_RESOURCE_PROMPT)

    modified_config = copilotkit_customize_config(
        config, emit_messages=False, emit_tool_calls=False
    )

    # Build message list with project context if available
    message_list = [system_message]
    if project_context:
        project_context_message = SystemMessage(
            content=f"PROJECT CONTEXT:\n{project_context}"
        )
        message_list.append(project_context_message)
    message_list.extend(messages)

    # Get model response
    response = await model_with_tools.ainvoke(message_list, config=modified_config)

    return Command(goto="__end__", update={"messages": response})
