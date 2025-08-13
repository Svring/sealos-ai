"""
Summarize project node for the Sealos Brain agent.
Generates a final summary of the project plan with resource details.
"""

from typing_extensions import Literal
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from src.provider.backbone_provider import get_sealos_model
from src.utils.context_utils import get_state_values
from copilotkit.langgraph import copilotkit_customize_config
from src.prompts.nodes.summarize_project_prompts import SUMMARIZE_PROJECT_PROMPT

from src.graph.sealos_brain.state import SealosBrainState


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
