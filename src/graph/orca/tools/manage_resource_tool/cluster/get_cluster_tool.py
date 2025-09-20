"""
Get cluster tool for the manage resource agent.
Handles cluster information retrieval with state management.
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
from src.lib.brain.sealos.cluster.get import get_cluster, BrainClusterContext


@tool
async def get_cluster_tool(
    cluster_name: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Get information for a database instance.

    This tool should be invoked strictly for resources of kind 'cluster'.
    When referring to resources, always refer to cluster as 'database'.

    Args:
        cluster_name: Name of the database to get information for

    Returns:
        Dict containing the cluster information

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Handle interrupt with approval and parameter editing
    is_approved, edited_data, response_payload = handle_interrupt_with_approval(
        action="get_cluster",
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
            action="get_cluster",
            response_payload=response_payload,
            resource_name="database",
            operation_type="Get",
        )

    # Extract the edited parameters
    cluster_name = edited_data.get("cluster_name", cluster_name)

    context = extract_sealos_context(state, ClusterContext)

    # Convert to brain context
    brain_context = BrainClusterContext(kubeconfig=context.kubeconfig)

    try:
        # Call the brain API function
        result = get_cluster(brain_context, cluster_name)

        return {
            "action": "get_cluster",
            "payload": edited_data,
            "success": True,
            "result": result,
            "message": f"Successfully retrieved information for cluster '{cluster_name}'",
        }
    except Exception as e:
        return {
            "action": "get_cluster",
            "payload": edited_data,
            "success": False,
            "error": str(e),
            "message": f"Failed to get information for cluster '{cluster_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the get cluster tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.cluster.get_cluster_tool

    import asyncio

    async def test_get_cluster():
        import os
        from dotenv import load_dotenv

        load_dotenv()

        print("Testing get_cluster_tool...")
        try:
            # Get kubeconfig from environment
            kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
            mock_state = {
                "kubeconfig": kubeconfig,
            }

            result = await get_cluster_tool.ainvoke(
                {"cluster_name": "test-cluster", "state": mock_state}
            )
            print("✅ Get cluster tool test successful!")
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ Get cluster tool test failed: {e}")

        print(f"Tool name: {get_cluster_tool.name}")
        print(f"Tool description: {get_cluster_tool.description}")

    asyncio.run(test_get_cluster())
