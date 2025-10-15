"""
Resource management node for the Orca agent.
Handles individual resource management operations with tools and actions.
"""

import json
from typing import Literal, List, Any
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from src.provider.backbone_provider import get_sealos_model
from src.utils.context_utils import get_state_values
from src.utils.error_utils import extract_error_type_and_construct_message
from src.graph.orca.state import OrcaState
from src.graph.orca.prompts.manage_resource_prompt import MANAGE_RESOURCE_PROMPT

# Note: Individual tool imports are used instead of the manage_resource_tools module

from src.graph.orca.tools.manage_resource_tool.devbox.get_devbox_tool import (
    get_devbox_tool,
)
from src.graph.orca.tools.manage_resource_tool.devbox.get_devbox_monitor_tool import (
    get_devbox_monitor_tool,
)
from src.graph.orca.tools.manage_resource_tool.devbox.deploy_devbox_release_tool import (
    deploy_devbox_release_tool,
)
from src.graph.orca.tools.manage_resource_tool.devbox.get_devbox_release_tool import (
    get_devbox_release_tool,
)
from src.graph.orca.tools.manage_resource_tool.devbox.get_devbox_network_tool import (
    get_devbox_network_tool,
)
from src.graph.orca.tools.manage_resource_tool.devbox.update_devbox_tool import (
    update_devbox_tool,
)
from src.graph.orca.tools.manage_resource_tool.devbox.create_devbox_ports_tool import (
    create_devbox_ports_tool,
)
from src.graph.orca.tools.manage_resource_tool.devbox.delete_devbox_ports_tool import (
    delete_devbox_ports_tool,
)
from src.graph.orca.tools.manage_resource_tool.devbox.start_devbox_tool import (
    start_devbox_tool,
)
from src.graph.orca.tools.manage_resource_tool.devbox.pause_devbox_tool import (
    pause_devbox_tool,
)
from src.graph.orca.tools.manage_resource_tool.devbox.autostart_devbox_tool import (
    autostart_devbox_tool,
)
from src.graph.orca.tools.manage_resource_tool.devbox.restart_devbox_tool import (
    restart_devbox_tool,
)
from src.graph.orca.tools.manage_resource_tool.cluster.get_cluster_tool import (
    get_cluster_tool,
)
from src.graph.orca.tools.manage_resource_tool.cluster.get_cluster_logs_tool import (
    get_cluster_logs_tool,
)
from src.graph.orca.tools.manage_resource_tool.cluster.get_cluster_monitor_tool import (
    get_cluster_monitor_tool,
)
from src.graph.orca.tools.manage_resource_tool.cluster.update_cluster_tool import (
    update_cluster_tool,
)
from src.graph.orca.tools.manage_resource_tool.cluster.start_cluster_tool import (
    start_cluster_tool,
)
from src.graph.orca.tools.manage_resource_tool.cluster.pause_cluster_tool import (
    pause_cluster_tool,
)
from src.graph.orca.tools.manage_resource_tool.cluster.restart_cluster_tool import (
    restart_cluster_tool,
)
from src.graph.orca.tools.manage_resource_tool.launchpad.get_launchpad_tool import (
    get_launchpad_tool,
)
from src.graph.orca.tools.manage_resource_tool.launchpad.get_launchpad_logs_tool import (
    get_launchpad_logs_tool,
)
from src.graph.orca.tools.manage_resource_tool.launchpad.get_launchpad_monitor_tool import (
    get_launchpad_monitor_tool,
)
from src.graph.orca.tools.manage_resource_tool.launchpad.get_launchpad_network_tool import (
    get_launchpad_network_tool,
)
from src.graph.orca.tools.manage_resource_tool.launchpad.update_launchpad_tool import (
    update_launchpad_tool,
)
from src.graph.orca.tools.manage_resource_tool.launchpad.create_launchpad_ports_tool import (
    create_launchpad_ports_tool,
)
from src.graph.orca.tools.manage_resource_tool.launchpad.delete_launchpad_ports_tool import (
    delete_launchpad_ports_tool,
)
from src.graph.orca.tools.manage_resource_tool.launchpad.create_launchpad_env_tool import (
    create_launchpad_env_tool,
)
from src.graph.orca.tools.manage_resource_tool.launchpad.delete_launchpad_env_tool import (
    delete_launchpad_env_tool,
)
from src.graph.orca.tools.manage_resource_tool.launchpad.update_launchpad_env_tool import (
    update_launchpad_env_tool,
)
from src.graph.orca.tools.manage_resource_tool.launchpad.update_launchpad_image_tool import (
    update_launchpad_image_tool,
)
from src.graph.orca.tools.manage_resource_tool.launchpad.update_launchpad_command_tool import (
    update_launchpad_command_tool,
)
from src.graph.orca.tools.manage_resource_tool.launchpad.start_launchpad_tool import (
    start_launchpad_tool,
)
from src.graph.orca.tools.manage_resource_tool.launchpad.pause_launchpad_tool import (
    pause_launchpad_tool,
)
from src.graph.orca.tools.manage_resource_tool.launchpad.restart_launchpad_tool import (
    restart_launchpad_tool,
)


# Tool sets for different resource types
DEVBOX_TOOLS = [
    get_devbox_tool,
    get_devbox_monitor_tool,
    deploy_devbox_release_tool,
    get_devbox_release_tool,
    get_devbox_network_tool,
    update_devbox_tool,
    create_devbox_ports_tool,
    delete_devbox_ports_tool,
    start_devbox_tool,
    pause_devbox_tool,
    restart_devbox_tool,
    autostart_devbox_tool,
]

CLUSTER_TOOLS = [
    get_cluster_tool,
    get_cluster_logs_tool,
    get_cluster_monitor_tool,
    update_cluster_tool,
    start_cluster_tool,
    pause_cluster_tool,
    restart_cluster_tool,
]

LAUNCHPAD_TOOLS = [
    get_launchpad_tool,
    get_launchpad_logs_tool,
    get_launchpad_monitor_tool,
    get_launchpad_network_tool,
    update_launchpad_tool,
    create_launchpad_ports_tool,
    delete_launchpad_ports_tool,
    create_launchpad_env_tool,
    delete_launchpad_env_tool,
    update_launchpad_env_tool,
    update_launchpad_image_tool,
    update_launchpad_command_tool,
    start_launchpad_tool,
    pause_launchpad_tool,
    restart_launchpad_tool,
]

tools = [
    *DEVBOX_TOOLS,
    *CLUSTER_TOOLS,
    *LAUNCHPAD_TOOLS,
]


def get_tools_for_resource_type(resource_context: Any) -> List[Any]:
    """
    Get the appropriate tools based on the resource type from resource_context.

    Args:
        resource_context: The resource context containing name, resourceType, and type fields

    Returns:
        List of tools appropriate for the resource type
    """
    if not resource_context:
        # If no resource context, return all tools as fallback
        return DEVBOX_TOOLS + CLUSTER_TOOLS + LAUNCHPAD_TOOLS

    # Try to parse resource_context if it's a string
    if isinstance(resource_context, str):
        try:
            resource_context = json.loads(resource_context)
        except (json.JSONDecodeError, TypeError):
            # If parsing fails, return all tools as fallback
            return DEVBOX_TOOLS + CLUSTER_TOOLS + LAUNCHPAD_TOOLS

    # Extract resourceType from the context
    resource_type = None
    if isinstance(resource_context, dict):
        resource_type = resource_context.get("resourceType") or resource_context.get(
            "resource_type"
        )

    # Map resource types to tool sets
    if resource_type:
        resource_type_lower = resource_type.lower()

        if resource_type_lower == "devbox":
            return DEVBOX_TOOLS
        elif resource_type_lower == "cluster":
            return CLUSTER_TOOLS
        elif resource_type_lower in ["deployment", "statefulset"]:
            # deployment and statefulset use launchpad tools
            return LAUNCHPAD_TOOLS

    # If resource type is not recognized, return all tools as fallback
    return DEVBOX_TOOLS + CLUSTER_TOOLS + LAUNCHPAD_TOOLS


async def manage_resource_agent(
    state: OrcaState, config: RunnableConfig
) -> Command[Literal["manage_resource_tool_node", "__end__"]]:
    """
    Resource management agent based on the Sealos AI functionality.
    Handles model binding, system prompts, Sealos context, and tool calls for individual resource management.
    Dynamically selects tools based on the resource type from resource_context.
    """
    try:
        # Extract state data
        (
            messages,
            base_url,
            api_key,
            model_name,
            resource_context,
        ) = get_state_values(
            state,
            {
                "messages": [],
                "base_url": None,
                "api_key": None,
                "model_name": None,
                "resource_context": None,
            },
        )

        model = get_sealos_model(
            base_url=base_url, api_key=api_key, model_name=model_name
        )

        # Dynamically select tools based on resource type
        selected_tools = get_tools_for_resource_type(resource_context)

        model_with_tools = model.bind_tools(selected_tools, parallel_tool_calls=False)

        # Build messages with system prompt for resource management
        system_message = SystemMessage(content=MANAGE_RESOURCE_PROMPT)

        # Build message list
        context_emphasis = SystemMessage(
            content="IMPORTANT: The next message contains the newest resource context. Pay close attention to it as it reflects the current state of the resource, including any recent modifications like added ports, changed environment variables, or updated configurations. Always use this latest context when answering questions or making decisions."
        )

        message_list = (
            [system_message]
            + [context_emphasis]
            + [SystemMessage(str(resource_context))]
            + messages
        )

        # Get model response
        response = await model_with_tools.ainvoke(message_list)

        # Check if the response contains tool calls
        if hasattr(response, "tool_calls") and response.tool_calls:
            return Command(
                goto="manage_resource_tool_node", update={"messages": response}
            )
        else:
            return Command(
                goto="__end__",
                update={"messages": response},
            )

    except Exception as e:
        # Handle any errors that occur during resource management processing
        error_str = str(e)
        structured_error_message = extract_error_type_and_construct_message(error_str)
        return Command(
            goto="__end__",
            update={"messages": SystemMessage(content=structured_error_message)},
        )
