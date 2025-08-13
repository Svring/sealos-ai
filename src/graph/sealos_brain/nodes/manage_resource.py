"""
Manage resource node for the Sealos Brain agent.
Handles resource management operations with tools and actions.
"""

from typing_extensions import Literal
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from langchain_tavily import TavilySearch

from src.provider.backbone_provider import get_sealos_model
from src.utils.context_utils import get_state_values, get_copilot_actions
from copilotkit.langgraph import copilotkit_customize_config
from src.prompts.nodes.manage_resource_prompts import MANAGE_RESOURCE_PROMPT

from src.graph.sealos_brain.state import SealosBrainState


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
