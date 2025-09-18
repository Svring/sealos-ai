"""
Delete launchpad tool for the manage resource agent.
Handles launchpad delete operations with state management.
"""

from typing import Dict, Any
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from langgraph.types import interrupt

from src.utils.sealos.extract_context import extract_sealos_context
from src.models.sealos.launchpad.launchpad_model import LaunchpadContext
from src.lib.sealos.launchpad.delete_launchpad import delete_launchpad


@tool
async def delete_launchpad_tool(
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
        Dict containing the delete operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Extract context from state
    approved = interrupt(
        {
            "action": "delete_launchpad",
            "payload": {
                "launchpad_name": launchpad_name,
            },
        }
    )

    # Check if the operation was approved
    if not approved or approved == "false":
        return {
            "action": "delete_launchpad",
            "payload": {
                "launchpad_name": launchpad_name,
            },
            "success": False,
            "error": "Operation rejected by user",
            "message": f"Delete operation for launchpad '{launchpad_name}' was rejected by user",
        }

    context = extract_sealos_context(state, LaunchpadContext)

    # Create payload for the launchpad delete
    from src.lib.sealos.launchpad.delete_launchpad import LaunchpadDeletePayload

    payload = LaunchpadDeletePayload(name=launchpad_name)

    try:
        # Call the actual delete function
        result = delete_launchpad(context, payload)

        return {
            "action": "delete_launchpad",
            "payload": {
                "launchpad_name": launchpad_name,
            },
            "success": True,
            "result": result,
            "message": f"Successfully deleted launchpad '{launchpad_name}'",
        }
    except Exception as e:
        return {
            "action": "delete_launchpad",
            "payload": {
                "launchpad_name": launchpad_name,
            },
            "success": False,
            "error": str(e),
            "message": f"Failed to delete launchpad '{launchpad_name}': {str(e)}",
        }
