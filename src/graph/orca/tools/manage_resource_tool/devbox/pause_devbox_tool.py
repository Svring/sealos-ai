"""
Pause devbox tool for the manage resource agent.
Handles devbox pause operations with state management.
"""

from typing import Dict, Any
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from langgraph.types import interrupt

from src.utils.sealos.extract_context import extract_sealos_context
from src.models.sealos.devbox.devbox_model import DevboxContext
from src.lib.sealos.devbox.pause_devbox import pause_devbox


@tool
async def pause_devbox_tool(
    devbox_name: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Pause a devbox instance.

    This tool should be invoked strictly for resources of kind 'devbox'.
    When referring to resources, always refer to devbox as 'devbox'.

    Args:
        devbox_name: Name of the devbox to pause

    Returns:
        Dict containing the pause operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Extract context from state
    approved = interrupt(
        {
            "action": "pause_devbox",
            "payload": {
                "devbox_name": devbox_name,
            },
        }
    )

    # Check if the operation was approved
    if not approved or approved == "false":
        return {
            "action": "pause_devbox",
            "payload": {
                "devbox_name": devbox_name,
            },
            "success": False,
            "error": "Operation rejected by user",
            "message": f"Pause operation for devbox '{devbox_name}' was rejected by user",
        }

    context = extract_sealos_context(state, DevboxContext)

    # Create payload for the devbox pause
    from src.lib.sealos.devbox.pause_devbox import DevboxPausePayload

    payload = DevboxPausePayload(name=devbox_name)

    try:
        # Call the actual pause function
        result = pause_devbox(context, payload)

        return {
            "action": "pause_devbox",
            "payload": {
                "devbox_name": devbox_name,
            },
            "success": True,
            "result": result,
            "message": f"Successfully paused devbox '{devbox_name}'",
        }
    except Exception as e:
        return {
            "action": "pause_devbox",
            "payload": {
                "devbox_name": devbox_name,
            },
            "success": False,
            "error": str(e),
            "message": f"Failed to pause devbox '{devbox_name}': {str(e)}",
        }
