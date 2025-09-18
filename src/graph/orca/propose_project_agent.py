"""
Project proposal node for the Orca agent.
Handles project proposal generation with tools and actions.
"""

from typing import Literal
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from src.provider.backbone_provider import get_sealos_model
from src.utils.context_utils import get_state_values, get_copilot_actions
from src.graph.orca.state import OrcaState
from src.graph.orca.tools.propose_project_tools import propose_project
from src.graph.orca.prompts.propose_project_prompt import (
    PROPOSE_PROJECT_REQUIREMENT_PROMPT,
)
from copilotkit.langgraph import copilotkit_customize_config


async def propose_project_agent(
    state: OrcaState, config: RunnableConfig
) -> Command[Literal["propose_tool_node", "__end__"]]:
    """
    Project proposal agent based on the Sealos AI functionality.
    Handles model binding, system prompts, and tool calls.
    """
    # Extract state data
    (
        messages,
        base_url,
        api_key,
        model_name,
        kubeconfig,
    ) = get_state_values(
        state,
        {
            "messages": [],
            "base_url": None,
            "api_key": None,
            "model_name": None,
            "kubeconfig": None,
        },
    )

    print("kubeconfig", kubeconfig)

    modifiedConfig = copilotkit_customize_config(
        config,
        emit_messages=False,  # if you want to disable message streaming
        # emit_tool_calls=False,  # if you want to disable tool call streaming
    )

    model = get_sealos_model(base_url=base_url, api_key=api_key, model_name=model_name)

    # Get copilot actions and add the propose_project tool
    all_tools = [propose_project]
    model_with_tools = model.bind_tools(all_tools, parallel_tool_calls=False)

    # Create the message list with system prompt and existing messages
    message_list = [
        SystemMessage(content=PROPOSE_PROJECT_REQUIREMENT_PROMPT),
    ]

    # Add existing messages from state
    if messages:
        message_list.extend(messages)

    # Get model response
    response = await model_with_tools.ainvoke(message_list, modifiedConfig)

    # Check if the response contains tool calls
    if hasattr(response, "tool_calls") and response.tool_calls:
        return Command(goto="propose_tool_node", update={"messages": response})
    else:
        return Command(
            goto="__end__",
            update={"messages": response},
        )
