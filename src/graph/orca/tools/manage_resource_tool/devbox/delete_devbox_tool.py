"""
Delete devbox tool for the manage resource agent.
Handles devbox delete operations with state management.
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
from src.models.sealos.devbox.devbox_model import DevboxContext
from src.lib.sealos.devbox.delete_devbox import delete_devbox


@tool
async def delete_devbox_tool(
    devbox_name: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Delete a devbox instance.

    This tool should be invoked strictly for resources of kind 'devbox'.
    When referring to resources, always refer to devbox as 'devbox'.

    Args:
        devbox_name: Name of the devbox to delete

    Returns:
        Dict containing the delete operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Handle interrupt with approval and parameter editing
    is_approved, edited_data, response_payload = handle_interrupt_with_approval(
        action="delete_devbox",
        payload={
            "devbox_name": devbox_name,
        },
        interrupt_func=interrupt,
        original_params={
            "devbox_name": devbox_name,
        },
    )

    # Check if the operation was approved
    if not is_approved:
        return create_rejection_response(
            action="delete_devbox",
            response_payload=response_payload,
            resource_name="devbox",
            operation_type="Delete",
        )

    # Extract the edited parameters
    devbox_name = edited_data.get("devbox_name", devbox_name)

    context = extract_sealos_context(state, DevboxContext)

    # Create payload for the devbox delete
    from src.lib.sealos.devbox.delete_devbox import DevboxDeletePayload

    payload = DevboxDeletePayload(name=devbox_name)

    try:
        # Call the actual delete function
        result = delete_devbox(context, payload)

        return {
            "action": "delete_devbox",
            "payload": edited_data,
            "success": True,
            "result": result,
            "message": f"Successfully deleted devbox '{devbox_name}'",
        }
    except Exception as e:
        return {
            "action": "delete_devbox",
            "payload": edited_data,
            "success": False,
            "error": str(e),
            "message": f"Failed to delete devbox '{devbox_name}': {str(e)}",
        }
