"""
Pause launchpad tool for the manage resource agent.
Handles launchpad pause operations with state management.
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
from src.lib.brain.sealos.launchpad.lifecycle import (
    launchpad_lifecycle,
    BrainLaunchpadContext,
    LaunchpadLifecycleAction,
)


@tool
async def pause_launchpad_tool(
    launchpad_name: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Pause an app launchpad instance.

    This tool should be invoked strictly for resources of kind 'deployment' and 'statefulset'.
    When referring to resources, always refer to launchpad as 'app launchpad'.

    Args:
        launchpad_name: Name of the app launchpad to pause

    Returns:
        Dict containing the pause operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Handle interrupt with approval and parameter editing
    is_approved, edited_data, response_payload = handle_interrupt_with_approval(
        action="pause_launchpad",
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
            action="pause_launchpad",
            response_payload=response_payload,
            resource_name="app launchpad",
            operation_type="Pause",
        )

    # Extract the edited parameters
    launchpad_name = edited_data.get("launchpad_name", launchpad_name)

    context = extract_sealos_context(state, LaunchpadContext)

    # Convert to brain context
    brain_context = BrainLaunchpadContext(kubeconfig=context.kubeconfig)

    # Create lifecycle action
    action = LaunchpadLifecycleAction(action="pause")

    try:
        # Call the brain API function
        result = launchpad_lifecycle(brain_context, launchpad_name, action)

        return {
            "action": "pause_launchpad",
            "payload": edited_data,
            "success": True,
            "result": result,
            "message": f"Successfully paused launchpad '{launchpad_name}'",
        }
    except Exception as e:
        return {
            "action": "pause_launchpad",
            "payload": edited_data,
            "success": False,
            "error": str(e),
            "message": f"Failed to pause launchpad '{launchpad_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the pause launchpad tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.launchpad.pause_launchpad_tool

    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing pause_launchpad_tool...")
    try:
        # Get kubeconfig from environment
        kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
        mock_state = {
            "kubeconfig": kubeconfig,
        }

        result = pause_launchpad_tool.invoke(
            {"launchpad_name": "test-launchpad", "state": mock_state}
        )
        print("✅ Pause launchpad tool test successful!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Pause launchpad tool test failed: {e}")

    print(f"Tool name: {pause_launchpad_tool.name}")
    print(f"Tool description: {pause_launchpad_tool.description}")
