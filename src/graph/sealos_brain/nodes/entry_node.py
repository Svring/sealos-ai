"""
Entry node for the Sealos Brain agent.
Handles routing decisions based on user input and project context.
"""

from typing_extensions import Literal
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from src.provider.backbone_provider import get_sealos_model
from src.utils.context_utils import get_state_values, get_copilot_actions
from copilotkit.langgraph import (
    copilotkit_customize_config,
    copilotkit_emit_state,
    copilotkit_exit,
)
from src.prompts.nodes.entry_node_prompts import (
    EXISTING_PROJECT_PLAN_TEMPLATE,
    GREETING_MESSAGE_PROMPT,
    build_routing_prompt_existing_project,
    build_routing_prompt_new_project,
)

from src.graph.sealos_brain.schemas import RouteOnly
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

    # Get available actions for manage_resource node
    copilot_actions = get_copilot_actions(state)
    actions_info = []
    for action in copilot_actions:
        if action.get("type") == "function" and "function" in action:
            func_info = action["function"]
            action_name = func_info.get("name", "Unknown")
            action_description = func_info.get("description", "No description")
            actions_info.append(f"- {action_name}: {action_description}")

    actions_text = "\n".join(actions_info) if actions_info else "No actions available"

    print("Available actions:", actions_text)

    has_existing_project = (
        project_plan and hasattr(project_plan, "name") and project_plan.name
    )

    modified_config = copilotkit_customize_config(
        config, emit_messages=False, emit_tool_calls=False
    )

    route_model = get_sealos_model("gpt-4o-mini", base_url, api_key)
    route_structured = route_model.with_structured_output(RouteOnly)

    if has_existing_project:
        # Build complete routing prompt using centralized function
        routing_prompt = build_routing_prompt_existing_project(
            project_context_available=bool(project_context), actions_text=actions_text
        )
        route_system = SystemMessage(content=routing_prompt)

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
        # Build complete routing prompt using centralized function
        routing_prompt = build_routing_prompt_new_project(
            project_context_available=bool(project_context), actions_text=actions_text
        )
        route_system = SystemMessage(content=routing_prompt)

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

    # If project context is empty but user is asking for project info or action-related requests, delegate to manage_resource
    if not project_context and messages:
        user_message = messages[-1].content.lower()

        # Check for project info keywords
        project_keywords = [
            "my project",
            "my projects",
            "project status",
            "project info",
            "project details",
            "what's running",
            "what's deployed",
            "show me",
            "list",
            "status",
            "running",
            "deployed",
            "devbox",
            "database",
            "bucket",
        ]

        # Check for action-related keywords (based on available actions)
        action_keywords = ["list", "delete", "create", "get", "resources", "projects"]

        if any(
            keyword in user_message for keyword in project_keywords + action_keywords
        ):
            return Command(goto="manage_resource")

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
