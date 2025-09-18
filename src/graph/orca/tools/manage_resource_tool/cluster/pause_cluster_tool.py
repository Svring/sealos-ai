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
    clusterName: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Pause a cluster instance.

    Args:
        clusterName: Name of the cluster to pause
        state: State containing the region_url and kubeconfig

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

    payload = ClusterPausePayload(name=clusterName)

    try:
        # Call the actual pause function
        result = pause_cluster(context, payload)

        return {
            "action": "pauseCluster",
            "success": True,
            "clusterName": clusterName,
            "result": result,
            "message": f"Successfully paused cluster '{clusterName}'",
        }
    except Exception as e:
        return {
            "action": "pauseCluster",
            "success": False,
            "clusterName": clusterName,
            "error": str(e),
            "message": f"Failed to pause cluster '{clusterName}': {str(e)}",
        }
