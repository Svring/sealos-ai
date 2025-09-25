"""
Delete cluster tool for the manage resource agent.
Handles cluster deletion operations with state management.
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
from src.lib.brain.sealos.cluster.delete import (
    delete_cluster,
    BrainClusterContext,
)


@tool
async def delete_cluster_tool_new(
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
        Dict containing the database deletion operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Handle interrupt with approval and parameter editing
    is_approved, edited_data, response_payload = handle_interrupt_with_approval(
        action="delete_cluster",
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
            action="delete_cluster",
            response_payload=response_payload,
            resource_name="database",
            operation_type="Delete",
        )

    # Extract the edited parameters
    cluster_name = edited_data.get("cluster_name", cluster_name)

    context = extract_sealos_context(state, ClusterContext)

    # Convert to brain context
    brain_context = BrainClusterContext(kubeconfig=context.kubeconfig)

    try:
        # Call the brain API function
        result = delete_cluster(brain_context, cluster_name)

        return {
            "action": "delete_cluster",
            "payload": edited_data,
            "success": True,
            "approved": True,
            "result": result,
            "message": f"Successfully deleted database '{cluster_name}'",
        }
    except Exception as e:
        return {
            "action": "delete_cluster",
            "payload": edited_data,
            "success": False,
            "approved": True,
            "error": str(e),
            "message": f"Failed to delete database '{cluster_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the delete cluster tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.cluster.delete_cluster_tool_new

    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing delete_cluster_tool_new...")
    try:
        # Get kubeconfig from environment
        kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
        mock_state = {
            "kubeconfig": kubeconfig,
        }

        result = delete_cluster_tool_new.invoke(
            {"cluster_name": "test-cluster", "state": mock_state}
        )
        print("✅ Delete cluster tool test successful!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Delete cluster tool test failed: {e}")

    print(f"Tool name: {delete_cluster_tool_new.name}")
    print(f"Tool description: {delete_cluster_tool_new.description}")
