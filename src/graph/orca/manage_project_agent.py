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
from src.utils.error_utils import extract_error_type_and_construct_message
from src.graph.orca.state import OrcaState
from src.graph.orca.prompts.manage_project_prompt import MANAGE_PROJECT_PROMPT


# Tools for the project management node
from src.graph.orca.tools.manage_resource_tool.devbox.create_devbox_tool import (
    create_devbox_tool,
)
from src.graph.orca.tools.manage_resource_tool.devbox.delete_devbox_tool import (
    delete_devbox_tool,
)
from src.graph.orca.tools.manage_resource_tool.cluster.create_cluster_tool import (
    create_cluster_tool,
)
from src.graph.orca.tools.manage_resource_tool.cluster.delete_cluster_tool_new import (
    delete_cluster_tool_new,
)
from src.graph.orca.tools.manage_resource_tool.launchpad.create_launchpad_tool import (
    create_launchpad_tool,
)
from src.graph.orca.tools.manage_resource_tool.launchpad.delete_launchpad_tool_new import (
    delete_launchpad_tool_new,
)

# Create and delete tools for project management
CREATE_DELETE_TOOLS = [
    create_devbox_tool,
    delete_devbox_tool,
    create_cluster_tool,
    delete_cluster_tool_new,
    create_launchpad_tool,
    delete_launchpad_tool_new,
]

tools = CREATE_DELETE_TOOLS


async def manage_project_agent(
    state: OrcaState, config: RunnableConfig
) -> Command[Literal["manage_project_tool_node", "__end__"]]:
    """
    Project management agent based on the Sealos AI functionality.
    Handles model binding, system prompts, Sealos context, and tool calls.
    """
    try:
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

        model = get_sealos_model(
            base_url=base_url, api_key=api_key, model_name=model_name
        )

        all_tools = tools

        model_with_tools = model.bind_tools(all_tools, parallel_tool_calls=False)

        # Build messages with system prompt for project management
        system_message = SystemMessage(content=MANAGE_PROJECT_PROMPT)

        # Build message list
        message_list = (
            [system_message] + [SystemMessage(str(project_context))] + messages
        )

        # print(message_list)

        # Get model response
        response = await model_with_tools.ainvoke(message_list)

        # Check if the response contains tool calls
        if hasattr(response, "tool_calls") and response.tool_calls:
            return Command(
                goto="manage_project_tool_node", update={"messages": response}
            )
        else:
            return Command(
                goto="__end__",
                update={"messages": response},
            )

    except Exception as e:
        # Handle any errors that occur during project management processing
        error_str = str(e)
        structured_error_message = extract_error_type_and_construct_message(error_str)
        return Command(
            goto="__end__",
            update={"messages": SystemMessage(content=structured_error_message)},
        )
