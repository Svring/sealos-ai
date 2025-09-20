"""
Start launchpad tool for the manage resource agent.
Handles launchpad start operations with state management.
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
async def start_launchpad_tool(
    launchpad_name: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Start an app launchpad instance.

    This tool should be invoked strictly for resources of kind 'deployment' and 'statefulset'.
    When referring to resources, always refer to launchpad as 'app launchpad'.

    Args:
        launchpad_name: Name of the app launchpad to start

    Returns:
        Dict containing the start operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Handle interrupt with approval and parameter editing
    is_approved, edited_data, response_payload = handle_interrupt_with_approval(
        action="start_launchpad",
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
            action="start_launchpad",
            response_payload=response_payload,
            resource_name="app launchpad",
            operation_type="Start",
        )

    # Extract the edited parameters
    launchpad_name = edited_data.get("launchpad_name", launchpad_name)

    context = extract_sealos_context(state, LaunchpadContext)

    # Convert to brain context
    brain_context = BrainLaunchpadContext(kubeconfig=context.kubeconfig)

    # Create lifecycle action
    action = LaunchpadLifecycleAction(action="start")

    try:
        # Call the brain API function
        result = launchpad_lifecycle(brain_context, launchpad_name, action)

        return {
            "action": "start_launchpad",
            "payload": edited_data,
            "success": True,
            "result": result,
            "message": f"Successfully started launchpad '{launchpad_name}'",
        }
    except Exception as e:
        return {
            "action": "start_launchpad",
            "payload": edited_data,
            "success": False,
            "error": str(e),
            "message": f"Failed to start launchpad '{launchpad_name}': {str(e)}",
        }
