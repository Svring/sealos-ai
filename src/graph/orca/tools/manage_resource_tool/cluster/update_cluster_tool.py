"""
Update cluster tool for the manage resource agent.
Handles cluster configuration updates with state management.
"""

from typing import Optional, Dict, Any, Literal
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from langgraph.types import interrupt

from src.utils.sealos.extract_context import extract_sealos_context
from src.utils.interrupt_utils import (
    handle_interrupt_with_approval,
    create_rejection_response,
)
from src.models.sealos.cluster.cluster_model import (
    ClusterContext,
)
from src.lib.brain.sealos.cluster.update import (
    update_cluster,
    BrainClusterContext,
    ClusterUpdateData,
)
from src.lib.brain.sealos.cluster.get import (
    get_cluster,
    BrainClusterContext as GetClusterContext,
)


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

    CRITICAL: The values proposed by the model can be modified by the user at any time
    during the approval process. The model should keep this in mind and always use the
    actual result from this tool as the true modification applied. For example, if the
    model proposes 2 CPU cores and 2GB memory, but the result shows 2 CPU cores and 4GB
    memory, the model should understand that the user has modified the proposed values.

    IMPORTANT PRINCIPLE: When the user's intention is ambiguous (e.g., "I'd like to update database"
    instead of "I'd like to update database to 2c 4g"), the model should still invoke this tool
    with the current resource quota of the database (which would be sent to the model along with
    the request). This allows the user to modify the data themselves through the approval interface.
    This principle applies to all update operations where users don't specify detailed parameters.

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

    # Convert to brain context
    brain_context = BrainClusterContext(kubeconfig=context.kubeconfig)

    # Get current cluster state before update
    before_update = None
    try:
        get_context = GetClusterContext(kubeconfig=context.kubeconfig)
        before_update = get_cluster(get_context, cluster_name)
    except Exception as e:
        print(f"Warning: Could not fetch current cluster state: {e}")

    # Create update data
    update_data = ClusterUpdateData(
        name=cluster_name,
        cpu=cpu,
        memory=memory,
    )

    try:
        # Call the brain API function
        result = update_cluster(brain_context, update_data)

        return {
            "action": "update_cluster",
            "payload": {
                **edited_data,
                "before_update": before_update,
            },
            "success": True,
            "approved": True,
            "result": result,
            "message": f"Successfully updated cluster '{cluster_name}'",
        }
    except Exception as e:
        return {
            "action": "update_cluster",
            "payload": {
                **edited_data,
                "before_update": before_update,
            },
            "success": False,
            "approved": True,
            "error": str(e),
            "message": f"Failed to update cluster '{cluster_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the update cluster tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.cluster.update_cluster_tool

    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing update_cluster_tool...")
    try:
        # Get kubeconfig from environment
        kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
        mock_state = {
            "kubeconfig": kubeconfig,
        }

        result = update_cluster_tool.invoke(
            {
                "cluster_name": "test-cluster",
                "cpu": 4,
                "memory": 8,
                "replicas": 3,
                "storage": 10,
                "state": mock_state,
            }
        )
        print("✅ Update cluster tool test successful!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Update cluster tool test failed: {e}")

    print(f"Tool name: {update_cluster_tool.name}")
    print(f"Tool description: {update_cluster_tool.description}")
