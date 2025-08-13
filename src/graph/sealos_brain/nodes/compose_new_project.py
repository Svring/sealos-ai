"""
Compose new project node for the Sealos Brain agent.
Creates a project plan based on optimized requirements.
"""

from typing_extensions import Literal
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from src.provider.backbone_provider import get_sealos_model
from src.utils.context_utils import get_state_values
from copilotkit.langgraph import (
    copilotkit_customize_config,
    copilotkit_emit_state,
)

from src.graph.sealos_brain.schemas import ProjectPlan
from src.graph.sealos_brain.state import SealosBrainState


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
