"""
Delete devbox tool for the manage resource agent.
Handles devbox delete operations with state management.
"""

from typing import Dict, Any
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from src.utils.sealos.extract_context import extract_sealos_context
from src.models.sealos.devbox.devbox_model import DevboxContext
from src.lib.sealos.devbox.delete_devbox import delete_devbox


@tool
async def delete_devbox_tool(
    devboxName: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Delete a devbox instance.

    Args:
        devboxName: Name of the devbox to delete
        state: State containing the region_url and kubeconfig

    Returns:
        Dict containing the delete operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Extract context from state
    context = extract_sealos_context(state, DevboxContext)

    # Create payload for the devbox delete
    from src.lib.sealos.devbox.delete_devbox import DevboxDeletePayload

    payload = DevboxDeletePayload(name=devboxName)

    try:
        # Call the actual delete function
        result = delete_devbox(context, payload)

        return {
            "action": "deleteDevbox",
            "success": True,
            "devboxName": devboxName,
            "result": result,
            "message": f"Successfully deleted devbox '{devboxName}'",
        }
    except Exception as e:
        return {
            "action": "deleteDevbox",
            "success": False,
            "devboxName": devboxName,
            "error": str(e),
            "message": f"Failed to delete devbox '{devboxName}': {str(e)}",
        }
