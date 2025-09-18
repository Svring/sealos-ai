"""
Pause cluster tool for the manage resource agent.
Handles cluster pause operations with state management.
"""

from typing import Dict, Any
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from src.utils.sealos.extract_context import extract_sealos_context
from src.models.sealos.cluster.cluster_model import ClusterContext
from src.lib.sealos.cluster.pause_cluster import pause_cluster


@tool
async def pause_cluster_tool(
    cluster_name: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Pause a database instance.

    This tool should be invoked strictly for resources of kind 'cluster'.
    When referring to resources, always refer to cluster as 'database'.

    Args:
        cluster_name: Name of the database to pause

    Returns:
        Dict containing the pause operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Extract context from state
    context = extract_sealos_context(state, ClusterContext)

    # Create payload for the cluster pause
    from src.lib.sealos.cluster.pause_cluster import ClusterPausePayload

    payload = ClusterPausePayload(name=cluster_name)

    try:
        # Call the actual pause function
        result = pause_cluster(context, payload)

        return {
            "action": "pause_cluster",
            "payload": {
                "cluster_name": cluster_name,
            },
            "success": True,
            "result": result,
            "message": f"Successfully paused cluster '{cluster_name}'",
        }
    except Exception as e:
        return {
            "action": "pause_cluster",
            "payload": {
                "cluster_name": cluster_name,
            },
            "success": False,
            "error": str(e),
            "message": f"Failed to pause cluster '{cluster_name}': {str(e)}",
        }
