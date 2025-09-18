"""
Delete cluster tool for the manage resource agent.
Handles cluster delete operations with state management.
"""

from typing import Dict, Any
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from src.utils.sealos.extract_context import extract_sealos_context
from src.models.sealos.cluster.cluster_model import ClusterContext
from src.lib.sealos.cluster.delete_cluster import delete_cluster


@tool
async def delete_cluster_tool(
    clusterName: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Delete a cluster instance.

    Args:
        clusterName: Name of the cluster to delete
        state: State containing the region_url and kubeconfig

    Returns:
        Dict containing the delete operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Extract context from state
    context = extract_sealos_context(state, ClusterContext)

    # Create payload for the cluster delete
    from src.lib.sealos.cluster.delete_cluster import ClusterDeletePayload

    payload = ClusterDeletePayload(name=clusterName)

    try:
        # Call the actual delete function
        result = delete_cluster(context, payload)

        return {
            "action": "deleteCluster",
            "success": True,
            "clusterName": clusterName,
            "result": result,
            "message": f"Successfully deleted cluster '{clusterName}'",
        }
    except Exception as e:
        return {
            "action": "deleteCluster",
            "success": False,
            "clusterName": clusterName,
            "error": str(e),
            "message": f"Failed to delete cluster '{clusterName}': {str(e)}",
        }
