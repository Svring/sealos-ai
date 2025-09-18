"""
Start launchpad tool for the manage resource agent.
Handles launchpad start operations with state management.
"""

from typing import Dict, Any
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from src.utils.sealos.extract_context import extract_sealos_context
from src.models.sealos.launchpad.launchpad_model import LaunchpadContext
from src.lib.sealos.launchpad.start_launchpad import start_launchpad


@tool
async def start_launchpad_tool(
    launchpadName: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Start a launchpad instance.

    Args:
        launchpadName: Name of the launchpad to start
        state: State containing the region_url and kubeconfig

    Returns:
        Dict containing the start operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Extract context from state
    context = extract_sealos_context(state, LaunchpadContext)

    # Create payload for the launchpad start
    from src.lib.sealos.launchpad.start_launchpad import LaunchpadStartPayload

    payload = LaunchpadStartPayload(name=launchpadName)

    try:
        # Call the actual start function
        result = start_launchpad(context, payload)

        return {
            "action": "startLaunchpad",
            "success": True,
            "launchpadName": launchpadName,
            "result": result,
            "message": f"Successfully started launchpad '{launchpadName}'",
        }
    except Exception as e:
        return {
            "action": "startLaunchpad",
            "success": False,
            "launchpadName": launchpadName,
            "error": str(e),
            "message": f"Failed to start launchpad '{launchpadName}': {str(e)}",
        }
