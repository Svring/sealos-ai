"""
Project management node for the Orca agent.
Handles project management operations with tools and actions.
"""

from typing import Literal
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from src.provider.backbone_provider import get_sealos_model
from src.utils.context_utils import get_state_values
from src.graph.orca.state import OrcaState
from src.graph.orca.prompts.manage_project_prompt import MANAGE_PROJECT_PROMPT
from src.graph.orca.tools.manage_project_tools import add_resource_to_project


# Tools for the project management node
tools = [add_resource_to_project]


async def manage_project_agent(
    state: OrcaState, config: RunnableConfig
) -> Command[Literal["manage_tool_node", "__end__"]]:
    """
    Project management agent based on the Sealos AI functionality.
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
            "model_name": None,
            "project_context": None,
        },
    )

    # modifiedConfig = copilotkit_customize_config(
    #     config,
    #     emit_messages=False,  # if you want to disable message streaming
    #     # emit_tool_calls=False,  # if you want to disable tool call streaming
    # )

    model = get_sealos_model(base_url=base_url, api_key=api_key, model_name=model_name)

    all_tools = tools

    model_with_tools = model.bind_tools(all_tools, parallel_tool_calls=False)

    # Build messages with system prompt for project management
    system_message = SystemMessage(content=MANAGE_PROJECT_PROMPT)

    # Build message list
    message_list = [system_message] + [SystemMessage(str(project_context))] + messages

    # print(message_list)

    # Get model response
    response = await model_with_tools.ainvoke(message_list)

    return Command(
        goto="__end__",
        update={
            "messages": response,
        },
    )
