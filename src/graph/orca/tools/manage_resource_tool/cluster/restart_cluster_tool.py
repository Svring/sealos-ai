"""
Restart cluster tool for the manage resource agent.
Handles cluster restart operations with state management.
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
async def restart_cluster_tool(
    cluster_name: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Restart a database instance.

    This tool restarts a database instance, which can help resolve various issues
    including connection problems, performance issues, or configuration changes
    that require a restart to take effect.

    This tool should be invoked strictly for resources of kind 'cluster'.
    When referring to resources, always refer to cluster as 'database'.

    Args:
        cluster_name: Name of the database to restart

    Returns:
        Dict containing the restart operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Handle interrupt with approval and parameter editing
    is_approved, edited_data, response_payload = handle_interrupt_with_approval(
        action="restart_cluster",
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
            action="restart_cluster",
            response_payload=response_payload,
            resource_name="database",
            operation_type="Restart",
        )

    # Extract the edited parameters
    cluster_name = edited_data.get("cluster_name", cluster_name)

    context = extract_sealos_context(state, ClusterContext)

    # Convert to brain context
    brain_context = BrainClusterContext(kubeconfig=context.kubeconfig)

    # Create lifecycle action
    action = ClusterLifecycleAction(action="restart")

    try:
        # Call the brain API function
        result = cluster_lifecycle(brain_context, cluster_name, action)

        return {
            "action": "restart_cluster",
            "payload": edited_data,
            "success": True,
            "result": result,
            "message": f"Successfully restarted database '{cluster_name}'",
        }
    except Exception as e:
        return {
            "action": "restart_cluster",
            "payload": edited_data,
            "success": False,
            "error": str(e),
            "message": f"Failed to restart database '{cluster_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the restart cluster tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.cluster.restart_cluster_tool

    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing restart_cluster_tool...")
    try:
        # Get kubeconfig from environment
        kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
        mock_state = {
            "kubeconfig": kubeconfig,
        }

        result = restart_cluster_tool.invoke(
            {"cluster_name": "test-cluster", "state": mock_state}
        )
        print("✅ Restart cluster tool test successful!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Restart cluster tool test failed: {e}")

    print(f"Tool name: {restart_cluster_tool.name}")
    print(f"Tool description: {restart_cluster_tool.description}")
