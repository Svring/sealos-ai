"""
Delete launchpad tool for the manage resource agent.
Handles launchpad delete operations with state management.
"""

from typing import Dict, Any
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from src.utils.sealos.extract_context import extract_sealos_context
from src.models.sealos.launchpad.launchpad_model import LaunchpadContext
from src.lib.sealos.launchpad.delete_launchpad import delete_launchpad


@tool
async def delete_launchpad_tool(
    launchpadName: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Delete a launchpad instance.

    Args:
        launchpadName: Name of the launchpad to delete
        state: State containing the region_url and kubeconfig

    Returns:
        Dict containing the delete operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Extract context from state
    context = extract_sealos_context(state, LaunchpadContext)

    # Create payload for the launchpad delete
    from src.lib.sealos.launchpad.delete_launchpad import LaunchpadDeletePayload

    payload = LaunchpadDeletePayload(name=launchpadName)

    try:
        # Call the actual delete function
        result = delete_launchpad(context, payload)

        return {
            "action": "deleteLaunchpad",
            "success": True,
            "launchpadName": launchpadName,
            "result": result,
            "message": f"Successfully deleted launchpad '{launchpadName}'",
        }
    except Exception as e:
        return {
            "action": "deleteLaunchpad",
            "success": False,
            "launchpadName": launchpadName,
            "error": str(e),
            "message": f"Failed to delete launchpad '{launchpadName}': {str(e)}",
        }
