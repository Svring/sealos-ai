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
from src.utils.interrupt_utils import (
    handle_interrupt_with_approval,
    create_rejection_response,
)
from src.models.sealos.cluster.cluster_model import ClusterContext
from src.lib.brain.sealos.cluster.lifecycle import (
    cluster_lifecycle,
    BrainClusterContext,
    ClusterLifecycleAction,
)


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
    # Handle interrupt with approval and parameter editing
    is_approved, edited_data, response_payload = handle_interrupt_with_approval(
        action="start_cluster",
        payload={
            "cluster_name": cluster_name,
        },
        interrupt_func=interrupt,
        original_params={
            "cluster_name": cluster_name,
        },
    )

    # Check if the operation was approved
    if not is_approved:
        return create_rejection_response(
            action="start_cluster",
            response_payload=response_payload,
            resource_name="database",
            operation_type="Start",
        )

    # Extract the edited parameters
    cluster_name = edited_data.get("cluster_name", cluster_name)

    context = extract_sealos_context(state, ClusterContext)

    # Convert to brain context
    brain_context = BrainClusterContext(kubeconfig=context.kubeconfig)

    # Create lifecycle action
    action = ClusterLifecycleAction(action="start")

    try:
        # Call the brain API function
        result = cluster_lifecycle(brain_context, cluster_name, action)

        return {
            "action": "start_cluster",
            "payload": edited_data,
            "success": True,
            "result": result,
            "message": f"Successfully started cluster '{cluster_name}'",
        }
    except Exception as e:
        return {
            "action": "start_cluster",
            "payload": edited_data,
            "success": False,
            "error": str(e),
            "message": f"Failed to start cluster '{cluster_name}': {str(e)}",
        }
