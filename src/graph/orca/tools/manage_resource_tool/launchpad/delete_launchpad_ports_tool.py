"""
Delete launchpad ports tool for the manage resource agent.
Handles launchpad port deletion operations with state management.
"""

from typing import Dict, Any, List
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from langgraph.types import interrupt

from src.utils.sealos.extract_context import extract_sealos_context
from src.utils.interrupt_utils import (
    handle_interrupt_with_approval,
    create_rejection_response,
)
from src.models.sealos.launchpad.launchpad_model import LaunchpadContext
from src.lib.brain.sealos.launchpad.update import (
    update_launchpad,
    BrainLaunchpadContext,
    LaunchpadUpdateData,
)


@tool
async def delete_launchpad_ports_tool(
    launchpad_name: str,
    ports: List[int],
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Delete ports from an app launchpad instance.

    This tool should be invoked strictly for resources of kind 'deployment' and 'statefulset'.
    When referring to resources, always refer to launchpad as 'app launchpad'.

    Args:
        launchpad_name: Name of the app launchpad to delete ports from
        ports: List of port numbers to delete

    Returns:
        Dict containing the port deletion operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Handle interrupt with approval and parameter editing
    is_approved, edited_data, response_payload = handle_interrupt_with_approval(
        action="delete_launchpad_ports",
        payload={
            "launchpad_name": launchpad_name,
            "ports": ports,
        },
        interrupt_func=interrupt,
        original_params={
            "launchpad_name": launchpad_name,
            "ports": ports,
        },
    )

    # Check if the operation was approved
    if not is_approved:
        return create_rejection_response(
            action="delete_launchpad_ports",
            response_payload=response_payload,
            resource_name="app launchpad",
            operation_type="Delete Ports",
        )

    # Extract the edited parameters
    launchpad_name = edited_data.get("launchpad_name", launchpad_name)
    ports = edited_data.get("ports", ports)

    context = extract_sealos_context(state, LaunchpadContext)

    # Convert to brain context
    brain_context = BrainLaunchpadContext(kubeconfig=context.kubeconfig)

    # Create update data with ports to delete
    update_data = LaunchpadUpdateData(
        name=launchpad_name,
        deletePorts=ports,
    )

    try:
        # Call the brain API function
        result = update_launchpad(brain_context, update_data)

        return {
            "action": "delete_launchpad_ports",
            "payload": edited_data,
            "success": True,
            "result": result,
            "message": f"Successfully deleted ports {ports} from launchpad '{launchpad_name}'",
        }
    except Exception as e:
        return {
            "action": "delete_launchpad_ports",
            "payload": edited_data,
            "success": False,
            "error": str(e),
            "message": f"Failed to delete ports from launchpad '{launchpad_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the delete launchpad ports tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.launchpad.delete_launchpad_ports_tool

    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing delete_launchpad_ports_tool...")
    try:
        # Get kubeconfig from environment
        kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
        mock_state = {
            "kubeconfig": kubeconfig,
        }

        result = delete_launchpad_ports_tool.invoke(
            {
                "launchpad_name": "test-launchpad",
                "ports": [8080, 3000],
                "state": mock_state,
            }
        )
        print("✅ Delete launchpad ports tool test successful!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Delete launchpad ports tool test failed: {e}")

    print(f"Tool name: {delete_launchpad_ports_tool.name}")
    print(f"Tool description: {delete_launchpad_ports_tool.description}")
