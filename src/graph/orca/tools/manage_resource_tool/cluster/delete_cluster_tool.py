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
    cluster_name: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Delete a database instance.

    This tool should be invoked strictly for resources of kind 'cluster'.
    When referring to resources, always refer to cluster as 'database'.

    Args:
        cluster_name: Name of the database to delete

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

    payload = ClusterDeletePayload(name=cluster_name)

    try:
        # Call the actual delete function
        result = delete_cluster(context, payload)

        return {
            "action": "delete_cluster",
            "payload": {
                "cluster_name": cluster_name,
            },
            "success": True,
            "result": result,
            "message": f"Successfully deleted cluster '{cluster_name}'",
        }
    except Exception as e:
        return {
            "action": "delete_cluster",
            "payload": {
                "cluster_name": cluster_name,
            },
            "success": False,
            "error": str(e),
            "message": f"Failed to delete cluster '{cluster_name}': {str(e)}",
        }
