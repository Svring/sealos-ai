"""
Start cluster tool for the manage resource agent.
Handles cluster start operations with state management.
"""

from typing import Dict, Any
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from src.utils.sealos.extract_context import extract_sealos_context
from src.models.sealos.cluster.cluster_model import ClusterContext
from src.lib.sealos.cluster.start_cluster import start_cluster


@tool
async def start_cluster_tool(
    clusterName: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Start a cluster instance.

    Args:
        clusterName: Name of the cluster to start
        state: State containing the region_url and kubeconfig

    Returns:
        Dict containing the start operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Extract context from state
    context = extract_sealos_context(state, ClusterContext)

    # Create payload for the cluster start
    from src.lib.sealos.cluster.start_cluster import ClusterStartPayload

    payload = ClusterStartPayload(name=clusterName)

    try:
        # Call the actual start function
        result = start_cluster(context, payload)

        return {
            "action": "startCluster",
            "success": True,
            "clusterName": clusterName,
            "result": result,
            "message": f"Successfully started cluster '{clusterName}'",
        }
    except Exception as e:
        return {
            "action": "startCluster",
            "success": False,
            "clusterName": clusterName,
            "error": str(e),
            "message": f"Failed to start cluster '{clusterName}': {str(e)}",
        }
