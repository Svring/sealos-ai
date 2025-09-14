"""
Tools for the propose project agent.
Contains the propose_project tool for generating project proposals.
"""

from typing import Annotated
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import InjectedState
from langchain_core.tools import tool

from src.provider.backbone_provider import get_sealos_model
from src.utils.context_utils import get_state_values
from src.graph.orca.state import OrcaState, ProjectProposal
from src.graph.orca.prompts.propose_project_prompt import PROPOSE_PROJECT_PROMPT
from copilotkit.langgraph import copilotkit_customize_config


@tool
async def propose_project(
    requirement: str,
    state: Annotated[OrcaState, InjectedState],
    config: RunnableConfig,
) -> ProjectProposal:
    """
    Generate a structured project proposal based on user requirements.

    Args:
        requirement: The user's project requirements and goals
        config: The runnable configuration

    Returns:
        ProjectProposal: A structured project proposal with name, description, and resources
    """
    # Extract state data
    (
        messages,
        base_url,
        api_key,
        model_name,
    ) = get_state_values(
        state,
        {
            "messages": [],
            "base_url": None,
            "api_key": None,
            "model_name": None,
        },
    )
    # print("base_url in propose_project tool", base_url)
    # print("api_key in propose_project tool", api_key)
    # print("model_name in propose_project tool", model_name)
    # Get model and create structured output
    modifiedConfig = copilotkit_customize_config(
        config,
        emit_messages=False,  # if you want to disable message streaming
        # emit_tool_calls=False,  # if you want to disable tool call streaming
    )

    model = get_sealos_model(base_url=base_url, api_key=api_key, model_name=model_name)
    structured_model = model.with_structured_output(ProjectProposal)

    # Create the message list with system prompt and requirement
    message_list = [
        SystemMessage(content=PROPOSE_PROJECT_PROMPT),
    ]

    if messages:
        message_list.extend(messages[:-1])

    # Generate project plan
    project_plan: ProjectProposal = await structured_model.ainvoke(
        message_list,
        modifiedConfig,
    )

    return project_plan.model_dump()
