"""
Update cluster tool for the manage resource agent.
Handles cluster configuration updates with state management.
"""

from typing import Optional, Dict, Any, Literal
from typing_extensions import Annotated
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langgraph.prebuilt import InjectedState
from langgraph.types import interrupt

from src.utils.sealos.extract_context import extract_sealos_context
from src.utils.interrupt_utils import (
    handle_interrupt_with_approval,
    create_rejection_response,
)
from src.models.sealos.cluster.cluster_model import (
    ClusterContext,
    ClusterUpdatePayload,
    ClusterResource,
)
from src.lib.sealos.cluster.update_cluster import update_cluster


@tool
async def update_cluster_tool(
    cluster_name: str,
    state: Annotated[dict, InjectedState],
    cpu: Optional[Literal[1, 2, 4, 8]] = None,
    memory: Optional[Literal[1, 2, 4, 8, 16, 32]] = None,
    replicas: Optional[int] = None,
    storage: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Update a database configuration (resource allocation).

    This tool should be invoked strictly for resources of kind 'cluster'.
    When referring to resources, always refer to cluster as 'database'.

    IMPORTANT: All resource parameters (cpu, memory, replicas, storage) are necessary
    for invoking this tool. When the user asks for only one resource update, the model
    should take the current values of the other resource fields from the resource context.

    Args:
        cluster_name: Name of the database to update
        cpu: CPU allocation in cores (1, 2, 4, or 8) - REQUIRED
        memory: Memory allocation in GB (1, 2, 4, 8, 16, or 32) - REQUIRED
        replicas: Number of replicas (1-20) - REQUIRED
        storage: Storage allocation in GB (3-300) - REQUIRED

    Returns:
        Dict containing the update operation result

    Raises:
        ValueError: If required state values are missing or no resource parameters provided
        requests.RequestException: If the API request fails
    """
    # Handle interrupt with approval and parameter editing
    is_approved, edited_data, response_payload = handle_interrupt_with_approval(
        action="update_cluster",
        payload={
            "cluster_name": cluster_name,
            "cpu": cpu,
            "memory": memory,
            "replicas": replicas,
            "storage": storage,
        },
        interrupt_func=interrupt,
        original_params={
            "cluster_name": cluster_name,
            "cpu": cpu,
            "memory": memory,
            "replicas": replicas,
            "storage": storage,
        },
    )

    # Check if the operation was approved
    if not is_approved:
        return create_rejection_response(
            action="update_cluster",
            response_payload=response_payload,
            resource_name="database",
            operation_type="Update",
        )

    # Extract the edited parameters
    cluster_name = edited_data.get("cluster_name", cluster_name)
    cpu = edited_data.get("cpu", cpu)
    memory = edited_data.get("memory", memory)
    replicas = edited_data.get("replicas", replicas)
    storage = edited_data.get("storage", storage)

    context = extract_sealos_context(state, ClusterContext)

    # Create resource configuration only if at least one parameter is provided
    if (
        cpu is not None
        or memory is not None
        or replicas is not None
        or storage is not None
    ):
        # Build resource dict with only provided parameters
        resource_dict = {}
        if cpu is not None:
            resource_dict["cpu"] = cpu
        if memory is not None:
            resource_dict["memory"] = memory
        if replicas is not None:
            resource_dict["replicas"] = replicas
        if storage is not None:
            resource_dict["storage"] = storage

        resource = ClusterResource(**resource_dict)

        # Create payload for the cluster update
        payload = ClusterUpdatePayload(
            name=cluster_name,
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
            "action": "update_cluster",
            "payload": edited_data,
            "success": True,
            "result": result,
            "message": f"Successfully updated cluster '{cluster_name}'",
        }
    except Exception as e:
        return {
            "action": "update_cluster",
            "payload": edited_data,
            "success": False,
            "error": str(e),
            "message": f"Failed to update cluster '{cluster_name}': {str(e)}",
        }
