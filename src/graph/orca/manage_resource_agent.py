"""
Resource management node for the Orca agent.
Handles individual resource management operations with tools and actions.
"""

from typing import Literal
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from src.provider.backbone_provider import get_sealos_model
from src.utils.context_utils import get_state_values
from src.graph.orca.state import OrcaState
from src.graph.orca.prompts.manage_resource_prompt import MANAGE_RESOURCE_PROMPT
from src.graph.orca.tools.manage_resource_tools import (
    updateDevbox,
    devboxLifecycle,
    releaseDevbox,
    deployDevbox,
    updateCluster,
    clusterLifecycle,
    updateLaunchpad,
    launchpadLifecycle,
)

from src.graph.orca.tools.manage_resource_tool.devbox.update_devbox_tool import (
    update_devbox_tool,
)
from src.graph.orca.tools.manage_resource_tool.devbox.start_devbox_tool import (
    start_devbox_tool,
)
from src.graph.orca.tools.manage_resource_tool.devbox.pause_devbox_tool import (
    pause_devbox_tool,
)
from src.graph.orca.tools.manage_resource_tool.devbox.delete_devbox_tool import (
    delete_devbox_tool,
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
from src.graph.orca.tools.manage_resource_tool.cluster.delete_cluster_tool import (
    delete_cluster_tool,
)
from src.graph.orca.tools.manage_resource_tool.launchpad.update_launchpad_tool import (
    update_launchpad_tool,
)
from src.graph.orca.tools.manage_resource_tool.launchpad.start_launchpad_tool import (
    start_launchpad_tool,
)
from src.graph.orca.tools.manage_resource_tool.launchpad.pause_launchpad_tool import (
    pause_launchpad_tool,
)
from src.graph.orca.tools.manage_resource_tool.launchpad.delete_launchpad_tool import (
    delete_launchpad_tool,
)


# Tools for the resource management node
tools = [
    # Devbox tools
    update_devbox_tool,
    start_devbox_tool,
    pause_devbox_tool,
    delete_devbox_tool,
    # Cluster tools
    update_cluster_tool,
    start_cluster_tool,
    pause_cluster_tool,
    delete_cluster_tool,
    # Launchpad tools
    update_launchpad_tool,
    start_launchpad_tool,
    pause_launchpad_tool,
    delete_launchpad_tool,
]


async def manage_resource_agent(
    state: OrcaState, config: RunnableConfig
) -> Command[Literal["manage_resource_tool_node", "__end__"]]:
    """
    Resource management agent based on the Sealos AI functionality.
    Handles model binding, system prompts, Sealos context, and tool calls for individual resource management.
    """
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

    model = get_sealos_model(base_url=base_url, api_key=api_key, model_name=model_name)

    all_tools = tools

    model_with_tools = model.bind_tools(all_tools, parallel_tool_calls=False)

    # Build messages with system prompt for resource management
    system_message = SystemMessage(content=MANAGE_RESOURCE_PROMPT)

    # Build message list
    message_list = [system_message] + [SystemMessage(str(resource_context))] + messages

    # Get model response
    response = await model_with_tools.ainvoke(message_list)

    # Check if the response contains tool calls
    if hasattr(response, "tool_calls") and response.tool_calls:
        return Command(goto="manage_resource_tool_node", update={"messages": response})
    else:
        return Command(
            goto="__end__",
            update={"messages": response},
        )
