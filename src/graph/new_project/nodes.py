"""
Nodes (entry, compose, summarize) for the New Project agent.
"""

from typing_extensions import Literal
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from src.provider.backbone_provider import get_sealos_model
from src.utils.context_utils import get_state_values
from copilotkit.langgraph import copilotkit_customize_config
from src.prompts.new_project_prompt import (
    ENTRY_NODE_EXISTING_PROJECT_PROMPT,
    ENTRY_NODE_NEW_PROJECT_PROMPT,
    COMPOSE_NEW_PROJECT_PROMPT,
    SUMMARIZE_PROJECT_PROMPT,
)

from .schemas import ProjectPlan, RouteDecision
from .state import SealosAIState


async def entry_node(
    state: SealosAIState, config: RunnableConfig
) -> Command[Literal["compose_new_project", "__end__"]]:
    (
        messages,
        base_url,
        api_key,
        model_name,
        project,
    ) = get_state_values(
        state,
        {
            "messages": [],
            "base_url": None,
            "api_key": None,
            "model": None,
            "project": None,
        },
    )

    model = get_sealos_model(model_name, base_url, api_key)
    structured = model.with_structured_output(RouteDecision)

    has_existing_project = project and hasattr(project, "name") and project.name
    if has_existing_project:
        system = SystemMessage(content=ENTRY_NODE_EXISTING_PROJECT_PROMPT)
    else:
        system = SystemMessage(content=ENTRY_NODE_NEW_PROJECT_PROMPT)

    modified_config = copilotkit_customize_config(
        config, emit_messages=False, emit_tool_calls=False
    )

    decision: RouteDecision = await structured.ainvoke(
        [system, *messages], config=modified_config
    )

    if decision.next_node == "compose_new_project":
        return Command(
            goto="compose_new_project", update={"project_brief": decision.info}
        )
    else:
        updated_messages = [*messages, AIMessage(content=decision.info)]
        return Command(goto="__end__", update={"messages": updated_messages})


async def compose_new_project(
    state: SealosAIState, config: RunnableConfig
) -> Command[Literal["summarize_project"]]:
    (
        project_brief,
        base_url,
        api_key,
        model_name,
    ) = get_state_values(
        state,
        {
            "project_brief": "",
            "base_url": None,
            "api_key": None,
            "model": None,
        },
    )

    model = get_sealos_model(model_name, base_url, api_key)
    structured = model.with_structured_output(ProjectPlan)

    system = SystemMessage(content=COMPOSE_NEW_PROJECT_PROMPT)

    modified_config = copilotkit_customize_config(
        config, emit_messages=False, emit_tool_calls=False
    )

    plan: ProjectPlan = await structured.ainvoke(
        [system, SystemMessage(content=f"Project brief: {project_brief}")],
        config=modified_config,
    )

    return Command(
        goto="summarize_project",
        update={
            "project": {
                "name": plan.name,
                "description": plan.description,
                "resources": plan.resources,
            }
        },
    )


async def summarize_project(
    state: SealosAIState, config: RunnableConfig
) -> Command[Literal["__end__"]]:
    (
        project_brief,
        project,
        base_url,
        api_key,
        model_name,
    ) = get_state_values(
        state,
        {
            "project_brief": "",
            "project": {"name": "", "description": "", "resources": None},
            "base_url": None,
            "api_key": None,
            "model": None,
        },
    )

    model = get_sealos_model(model_name, base_url, api_key)

    system = SystemMessage(content=SUMMARIZE_PROJECT_PROMPT)

    # Format resources for better readability
    resources = project.get("resources")
    if resources and hasattr(resources, "devboxes"):
        devboxes = resources.devboxes or []
        databases = resources.databases or []
        buckets = resources.buckets or []
    else:
        devboxes = []
        databases = []
        buckets = []

    summary_prompt = f"""
Project Brief: {project_brief}

RECOMMENDED SEALOS RESOURCE PLAN:
Project Name: {project.get('name', 'Unnamed Project')}
Description: {project.get('description', 'No description provided')}

DevBoxes (Development Environments):
{chr(10).join([f"- {box.runtime}: {box.description}" for box in devboxes]) if devboxes else "- None recommended"}

Databases:
{chr(10).join([f"- {db.type}: {db.description}" for db in databases]) if databases else "- None recommended"}

Object Storage Buckets:
{chr(10).join([f"- {bucket.policy} policy: {bucket.description}" for bucket in buckets]) if buckets else "- None recommended"}

Provide a comprehensive summary explaining the rationale and usage guidance.
"""

    modified_config = copilotkit_customize_config(
        config, emit_messages=False, emit_tool_calls=False
    )

    summary = await model.ainvoke(
        [system, SystemMessage(content=summary_prompt)], config=modified_config
    )

    return Command(
        goto="__end__", update={"messages": [AIMessage(content=summary.content)]}
    )
