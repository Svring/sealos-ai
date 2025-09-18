"""
Update cluster tool for the manage resource agent.
Handles cluster configuration updates with state management.
"""

from typing import Optional, Dict, Any, Literal
from typing_extensions import Annotated
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langgraph.prebuilt import InjectedState

from src.utils.context_utils import get_state_values
from src.models.sealos.cluster.cluster_model import (
    ClusterContext,
    ClusterUpdatePayload,
    ClusterResource,
)
from src.lib.sealos.cluster.update_cluster import update_cluster


@tool
async def update_cluster_tool(
    clusterName: str,
    state: Annotated[dict, InjectedState],
    cpu: Optional[Literal[1, 2, 4, 8, 16]] = None,
    memory: Optional[Literal[1, 2, 4, 8, 16, 32]] = None,
    replicas: Optional[int] = None,
    storage: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Update a cluster configuration (resource allocation).

    Args:
        clusterName: Name of the cluster to update
        state: State containing the region_url and kubeconfig
        cpu: CPU allocation in cores (1, 2, 4, 8, or 16)
        memory: Memory allocation in GB (1, 2, 4, 8, 16, or 32)
        replicas: Number of replicas (1-20)
        storage: Storage allocation in GB (3-300)

    Returns:
        Dict containing the update operation result

    Raises:
        ValueError: If required state values are missing or no resource parameters provided
        requests.RequestException: If the API request fails
    """
    # Extract state data from config
    (
        region_url,
        kubeconfig,
    ) = get_state_values(
        state,
        {
            "region_url": None,
            "kubeconfig": None,
        },
    )

    if not region_url:
        raise ValueError("region_url is required in state")
    if not kubeconfig:
        raise ValueError("kubeconfig is required in state")

    # Create context for the cluster update
    context = ClusterContext(
        kubeconfig=kubeconfig,
        regionUrl=region_url,
    )

    # Create resource configuration only if at least one parameter is provided
    if (
        cpu is not None
        or memory is not None
        or replicas is not None
        or storage is not None
    ):
        # Use default values if not provided
        cpu_value = cpu if cpu is not None else 1
        memory_value = memory if memory is not None else 1
        replicas_value = replicas if replicas is not None else 1
        storage_value = storage if storage is not None else 10

        resource = ClusterResource(
            cpu=cpu_value,
            memory=memory_value,
            replicas=replicas_value,
            storage=storage_value,
        )

        # Create payload for the cluster update
        payload = ClusterUpdatePayload(
            name=clusterName,
            resource=resource,
        )
    else:
        raise ValueError(
            "At least one of cpu, memory, replicas, or storage must be provided"
        )

    try:
        # Call the actual update function
        result = update_cluster(context, payload)

        return {
            "action": "updateCluster",
            "success": True,
            "clusterName": clusterName,
            "result": result,
            "message": f"Successfully updated cluster '{clusterName}'",
        }
    except Exception as e:
        return {
            "action": "updateCluster",
            "success": False,
            "clusterName": clusterName,
            "error": str(e),
            "message": f"Failed to update cluster '{clusterName}': {str(e)}",
        }
