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
from src.lib.sealos.launchpad.pause_launchpad import pause_launchpad


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

    # Create payload for the launchpad pause
    from src.lib.sealos.launchpad.pause_launchpad import LaunchpadPausePayload

    payload = LaunchpadPausePayload(name=launchpad_name)

    try:
        # Call the actual pause function
        result = pause_launchpad(context, payload)

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
