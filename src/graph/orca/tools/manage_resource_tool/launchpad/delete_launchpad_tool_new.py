"""
Delete launchpad tool for the manage resource agent.
Handles launchpad deletion operations with state management.
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
from src.models.sealos.launchpad.launchpad_model import LaunchpadContext
from src.lib.brain.sealos.launchpad.delete import (
    delete_launchpad,
    BrainLaunchpadContext,
)


@tool
async def delete_launchpad_tool_new(
    launchpad_name: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Delete an app launchpad instance.

    This tool should be invoked strictly for resources of kind 'deployment' and 'statefulset'.
    When referring to resources, always refer to launchpad as 'app launchpad'.

    Args:
        launchpad_name: Name of the app launchpad to delete

    Returns:
        Dict containing the app launchpad deletion operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Handle interrupt with approval and parameter editing
    is_approved, edited_data, response_payload = handle_interrupt_with_approval(
        action="delete_launchpad",
        payload={
            "launchpad_name": launchpad_name,
        },
        interrupt_func=interrupt,
        original_params={
            "launchpad_name": launchpad_name,
        },
    )

    # Check if the operation was approved
    if not is_approved:
        return create_rejection_response(
            action="delete_launchpad",
            response_payload=response_payload,
            resource_name="app launchpad",
            operation_type="Delete",
        )

    # Extract the edited parameters
    launchpad_name = edited_data.get("launchpad_name", launchpad_name)

    context = extract_sealos_context(state, LaunchpadContext)

    # Convert to brain context
    brain_context = BrainLaunchpadContext(kubeconfig=context.kubeconfig)

    try:
        # Call the brain API function
        result = delete_launchpad(brain_context, launchpad_name)

        return {
            "action": "delete_launchpad",
            "payload": edited_data,
            "success": True,
            "approved": True,
            "result": result,
            "message": f"Successfully deleted app launchpad '{launchpad_name}'",
        }
    except Exception as e:
        return {
            "action": "delete_launchpad",
            "payload": edited_data,
            "success": False,
            "approved": True,
            "error": str(e),
            "message": f"Failed to delete app launchpad '{launchpad_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the delete launchpad tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.launchpad.delete_launchpad_tool_new

    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing delete_launchpad_tool_new...")
    try:
        # Get kubeconfig from environment
        kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
        mock_state = {
            "kubeconfig": kubeconfig,
        }

        result = delete_launchpad_tool_new.invoke(
            {"launchpad_name": "test-launchpad", "state": mock_state}
        )
        print("✅ Delete launchpad tool test successful!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Delete launchpad tool test failed: {e}")

    print(f"Tool name: {delete_launchpad_tool_new.name}")
    print(f"Tool description: {delete_launchpad_tool_new.description}")
