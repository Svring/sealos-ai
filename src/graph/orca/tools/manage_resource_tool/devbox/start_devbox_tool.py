"""
Start devbox tool for the manage resource agent.
Handles devbox start operations with state management.
"""

from typing import Dict, Any
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from src.utils.sealos.extract_context import extract_sealos_context
from src.models.sealos.devbox.devbox_model import DevboxContext
from src.lib.sealos.devbox.start_devbox import start_devbox


@tool
async def start_devbox_tool(
    devboxName: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Start a devbox instance.

    Args:
        devboxName: Name of the devbox to start
        state: State containing the region_url and kubeconfig

    Returns:
        Dict containing the start operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Extract context from state
    context = extract_sealos_context(state, DevboxContext)

    # Create payload for the devbox start
    from src.lib.sealos.devbox.start_devbox import DevboxStartPayload

    payload = DevboxStartPayload(name=devboxName)

    try:
        # Call the actual start function
        result = start_devbox(context, payload)

        return {
            "action": "startDevbox",
            "success": True,
            "devboxName": devboxName,
            "result": result,
            "message": f"Successfully started devbox '{devboxName}'",
        }
    except Exception as e:
        return {
            "action": "startDevbox",
            "success": False,
            "devboxName": devboxName,
            "error": str(e),
            "message": f"Failed to start devbox '{devboxName}': {str(e)}",
        }
