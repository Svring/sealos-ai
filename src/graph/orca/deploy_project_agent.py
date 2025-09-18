"""
Project deployment node for the Orca agent.
Handles project deployment operations with tools and actions.
"""

from typing import Literal
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from src.provider.backbone_provider import get_sealos_model
from src.utils.context_utils import get_state_values
from src.graph.orca.state import OrcaState
from src.graph.orca.prompts.deploy_project_prompt import DEPLOY_PROJECT_PROMPT
from src.graph.orca.tools.deploy_project_tool import deploy_project_tools


async def deploy_project_agent(
    state: OrcaState, config: RunnableConfig
) -> Command[Literal["deploy_project_tool_node", "__end__"]]:
    """
    Project deployment agent based on the Sealos AI functionality.
    Handles model binding, system prompts, and deployment tool calls.
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

    model = get_sealos_model(base_url=base_url, api_key=api_key, model_name=model_name)

    model_with_tools = model.bind_tools(deploy_project_tools)

    # Build system message for project deployment
    system_message = SystemMessage(content=DEPLOY_PROJECT_PROMPT)

    # Build message list
    message_list = [system_message]

    # Add existing messages from state
    if messages:
        message_list.extend(messages)

    # Get model response
    response = await model_with_tools.ainvoke(message_list, config)

    # Check if the response contains tool calls
    if hasattr(response, "tool_calls") and response.tool_calls:
        return Command(goto="deploy_project_tool_node", update={"messages": response})
    else:
        return Command(
            goto="__end__",
            update={"messages": response},
        )
