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
    # Extract context from state
    context = extract_sealos_context(state, LaunchpadContext)

    # Create payload for the launchpad start
    from src.lib.sealos.launchpad.start_launchpad import LaunchpadStartPayload

    payload = LaunchpadStartPayload(name=launchpad_name)

    try:
        # Call the actual start function
        result = start_launchpad(context, payload)

        return {
            "action": "start_launchpad",
            "payload": {
                "launchpad_name": launchpad_name,
            },
            "success": True,
            "result": result,
            "message": f"Successfully started launchpad '{launchpad_name}'",
        }
    except Exception as e:
        return {
            "action": "start_launchpad",
            "payload": {
                "launchpad_name": launchpad_name,
            },
            "success": False,
            "error": str(e),
            "message": f"Failed to start launchpad '{launchpad_name}': {str(e)}",
        }
