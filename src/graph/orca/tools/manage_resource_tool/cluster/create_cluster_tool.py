"""
Create cluster tool for the manage resource agent.
Handles cluster creation operations with state management.
"""

from typing import Dict, Any, Literal
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
from src.lib.brain.sealos.cluster.create import (
    create_cluster,
    BrainClusterContext,
    ClusterCreateData,
)


@tool
async def create_cluster_tool(
    cluster_name: str,
    state: Annotated[dict, InjectedState],
    type: Literal[
        "postgresql",
        "mongodb",
        "apecloud-mysql",
        "redis",
        "kafka",
        "milvus",
    ],
    cpu: int = 2,
    memory: int = 2,
    storage: int = 10,
    replicas: int = 1,
) -> Dict[str, Any]:
    """
    Create a new database instance.

    This tool should be invoked strictly for resources of kind 'cluster'.
    When referring to resources, always refer to cluster as 'database'.

    Args:
        cluster_name: Name of the database to create
        type: Database type
        cpu: CPU allocation in cores (default: 2)
        memory: Memory allocation in GB (default: 2)
        storage: Storage allocation in GB (default: 10)
        replicas: Number of replicas (default: 1)

    Returns:
        Dict containing the database creation operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Handle interrupt with approval and parameter editing
    is_approved, edited_data, response_payload = handle_interrupt_with_approval(
        action="create_cluster",
        payload={
            "cluster_name": cluster_name,
            "type": type,
            "cpu": cpu,
            "memory": memory,
            "storage": storage,
            "replicas": replicas,
        },
        interrupt_func=interrupt,
        original_params={
            "cluster_name": cluster_name,
            "type": type,
            "cpu": cpu,
            "memory": memory,
            "storage": storage,
            "replicas": replicas,
        },
    )

    # Check if the operation was approved
    if not is_approved:
        return create_rejection_response(
            action="create_cluster",
            response_payload=response_payload,
            resource_name="database",
            operation_type="Create",
        )

    # Extract the edited parameters
    cluster_name = edited_data.get("cluster_name", cluster_name)
    type = edited_data.get("type", type)
    cpu = edited_data.get("cpu", cpu)
    memory = edited_data.get("memory", memory)
    storage = edited_data.get("storage", storage)
    replicas = edited_data.get("replicas", replicas)

    context = extract_sealos_context(state, ClusterContext)

    # Convert to brain context
    brain_context = BrainClusterContext(kubeconfig=context.kubeconfig)

    # Create cluster data
    create_data = ClusterCreateData(
        name=cluster_name,
        type=type,
        cpu=cpu,
        memory=memory,
        storage=storage,
        replicas=replicas,
    )

    try:
        # Call the brain API function
        result = create_cluster(brain_context, create_data)

        return {
            "action": "create_cluster",
            "payload": edited_data,
            "success": True,
            "approved": True,
            "result": result,
            "message": f"Successfully created database '{cluster_name}' of type '{type}'",
        }
    except Exception as e:
        return {
            "action": "create_cluster",
            "payload": edited_data,
            "success": False,
            "approved": True,
            "error": str(e),
            "message": f"Failed to create database '{cluster_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the create cluster tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.cluster.create_cluster_tool

    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing create_cluster_tool...")
    try:
        # Get kubeconfig from environment
        kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
        mock_state = {
            "kubeconfig": kubeconfig,
        }

        result = create_cluster_tool.invoke(
            {
                "cluster_name": "test-cluster",
                "type": "postgresql",
                "cpu": 2,
                "memory": 4,
                "storage": 20,
                "replicas": 1,
                "state": mock_state,
            }
        )
        print("✅ Create cluster tool test successful!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Create cluster tool test failed: {e}")

    print(f"Tool name: {create_cluster_tool.name}")
    print(f"Tool description: {create_cluster_tool.description}")
