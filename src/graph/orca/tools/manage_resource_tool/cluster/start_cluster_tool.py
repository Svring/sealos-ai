"""
Start cluster tool for the manage resource agent.
Handles cluster start operations with state management.
"""

from typing import Dict, Any
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from langgraph.types import interrupt

from src.utils.sealos.extract_context import extract_sealos_context
from src.models.sealos.cluster.cluster_model import ClusterContext
from src.lib.sealos.cluster.start_cluster import start_cluster
from src.lib.sealos.cluster.start_cluster import ClusterStartPayload


@tool
async def start_cluster_tool(
    cluster_name: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Start a database instance.

    This tool should be invoked strictly for resources of kind 'cluster'.
    When referring to resources, always refer to cluster as 'database'.

    Args:
        cluster_name: Name of the database to start

    Returns:
        Dict containing the start operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Extract context from state
    approved = interrupt(
        {
            "action": "start_cluster",
            "payload": {
                "cluster_name": cluster_name,
            },
        }
    )

    # Check if the operation was approved
    if not approved or approved == "false":
        return {
            "action": "start_cluster",
            "payload": {
                "cluster_name": cluster_name,
            },
            "success": False,
            "error": "Operation rejected by user",
            "message": f"Start operation for cluster '{cluster_name}' was rejected by user",
        }

    context = extract_sealos_context(state, ClusterContext)

    # Create payload for the cluster start

    payload = ClusterStartPayload(name=cluster_name)

    try:
        # Call the actual start function
        result = start_cluster(context, payload)

        return {
            "action": "start_cluster",
            "payload": {
                "cluster_name": cluster_name,
            },
            "success": True,
            "result": result,
            "message": f"Successfully started cluster '{cluster_name}'",
        }
    except Exception as e:
        return {
            "action": "start_cluster",
            "payload": {
                "cluster_name": cluster_name,
            },
            "success": False,
            "error": str(e),
            "message": f"Failed to start cluster '{cluster_name}': {str(e)}",
        }
