"""
Get cluster monitor tool for the manage resource agent.
Handles cluster monitoring data retrieval with state management.
"""

from typing import Dict, Any
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from src.utils.sealos.extract_context import extract_sealos_context
from src.models.sealos.cluster.cluster_model import ClusterContext
from src.lib.brain.sealos.cluster.monitor import (
    get_cluster_monitor,
    BrainClusterContext,
)


@tool
async def get_cluster_monitor_tool(
    cluster_name: str,
    db_type: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Get monitoring data for a database instance.

    This tool should be invoked strictly for resources of kind 'cluster'.
    When referring to resources, always refer to cluster as 'database'.

    Args:
        cluster_name: Name of the database to get monitoring data for
        db_type: Database type for monitoring (e.g., "mysql", "postgresql")

    Returns:
        Dict containing the monitoring data

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    context = extract_sealos_context(state, ClusterContext)

    # Convert to brain context
    brain_context = BrainClusterContext(kubeconfig=context.kubeconfig)

    try:
        # Call the brain API function
        result = get_cluster_monitor(brain_context, cluster_name, db_type)

        return {
            "action": "get_cluster_monitor",
            "payload": {
                "cluster_name": cluster_name,
                "db_type": db_type,
            },
            "success": True,
            "result": result,
            "message": f"Successfully retrieved monitoring data for cluster '{cluster_name}'",
        }
    except Exception as e:
        return {
            "action": "get_cluster_monitor",
            "payload": {
                "cluster_name": cluster_name,
                "db_type": db_type,
            },
            "success": False,
            "error": str(e),
            "message": f"Failed to get monitoring data for cluster '{cluster_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the get cluster monitor tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.cluster.get_cluster_monitor_tool

    import asyncio

    async def test_get_cluster_monitor():
        print("Testing get_cluster_monitor_tool...")
        try:
            # Mock state for testing
            mock_state = {
                "kubeconfig": "test-kubeconfig",
            }

            result = await get_cluster_monitor_tool.ainvoke(
                {
                    "cluster_name": "test-cluster",
                    "db_type": "mysql",
                    "state": mock_state,
                }
            )
            print("✅ Get cluster monitor tool test successful!")
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ Get cluster monitor tool test failed: {e}")

        print(f"Tool name: {get_cluster_monitor_tool.name}")
        print(f"Tool description: {get_cluster_monitor_tool.description}")

    asyncio.run(test_get_cluster_monitor())
