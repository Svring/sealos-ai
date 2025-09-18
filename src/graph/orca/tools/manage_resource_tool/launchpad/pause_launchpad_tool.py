"""
Pause launchpad tool for the manage resource agent.
Handles launchpad pause operations with state management.
"""

from typing import Dict, Any
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from src.utils.sealos.extract_context import extract_sealos_context
from src.models.sealos.launchpad.launchpad_model import LaunchpadContext
from src.lib.sealos.launchpad.pause_launchpad import pause_launchpad


@tool
async def pause_launchpad_tool(
    launchpadName: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Pause a launchpad instance.

    Args:
        launchpadName: Name of the launchpad to pause
        state: State containing the region_url and kubeconfig

    Returns:
        Dict containing the pause operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Extract context from state
    context = extract_sealos_context(state, LaunchpadContext)

    # Create payload for the launchpad pause
    from src.lib.sealos.launchpad.pause_launchpad import LaunchpadPausePayload

    payload = LaunchpadPausePayload(name=launchpadName)

    try:
        # Call the actual pause function
        result = pause_launchpad(context, payload)

        return {
            "action": "pauseLaunchpad",
            "success": True,
            "launchpadName": launchpadName,
            "result": result,
            "message": f"Successfully paused launchpad '{launchpadName}'",
        }
    except Exception as e:
        return {
            "action": "pauseLaunchpad",
            "success": False,
            "launchpadName": launchpadName,
            "error": str(e),
            "message": f"Failed to pause launchpad '{launchpadName}': {str(e)}",
        }
