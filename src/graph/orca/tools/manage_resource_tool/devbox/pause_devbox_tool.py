"""
Pause devbox tool for the manage resource agent.
Handles devbox pause operations with state management.
"""

from typing import Dict, Any
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from src.utils.sealos.extract_context import extract_sealos_context
from src.models.sealos.devbox.devbox_model import DevboxContext
from src.lib.sealos.devbox.pause_devbox import pause_devbox


@tool
async def pause_devbox_tool(
    devboxName: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Pause a devbox instance.

    Args:
        devboxName: Name of the devbox to pause
        state: State containing the region_url and kubeconfig

    Returns:
        Dict containing the pause operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Extract context from state
    context = extract_sealos_context(state, DevboxContext)

    # Create payload for the devbox pause
    from src.lib.sealos.devbox.pause_devbox import DevboxPausePayload

    payload = DevboxPausePayload(name=devboxName)

    try:
        # Call the actual pause function
        result = pause_devbox(context, payload)

        return {
            "action": "pauseDevbox",
            "success": True,
            "devboxName": devboxName,
            "result": result,
            "message": f"Successfully paused devbox '{devboxName}'",
        }
    except Exception as e:
        return {
            "action": "pauseDevbox",
            "success": False,
            "devboxName": devboxName,
            "error": str(e),
            "message": f"Failed to pause devbox '{devboxName}': {str(e)}",
        }
