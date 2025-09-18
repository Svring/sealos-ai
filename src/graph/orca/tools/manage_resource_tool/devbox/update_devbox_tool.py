"""
Update devbox tool for the manage resource agent.
Handles devbox configuration updates with state management.
"""

from typing import Optional, Dict, Any, Literal
from typing_extensions import Annotated
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langgraph.prebuilt import InjectedState
from langgraph.types import interrupt

from src.utils.sealos.extract_context import extract_sealos_context
from src.models.sealos.devbox.devbox_model import (
    DevboxContext,
    DevboxUpdatePayload,
    DevboxResource,
)
from src.lib.sealos.devbox.update_devbox import update_devbox


class UpdateDevboxInput(BaseModel):
    """Input model for update devbox tool."""

    devboxName: str = Field(
        ...,
        min_length=1,
        max_length=63,
        pattern=r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$",
        description="Devbox name (must be DNS compliant: lowercase, numbers, hyphens, 1-63 chars)",
    )
    cpu: Optional[Literal[1, 2, 4, 8, 16]] = Field(
        default=None, description="CPU allocation in cores"
    )
    memory: Optional[Literal[1, 2, 4, 8, 16, 32]] = Field(
        default=None, description="Memory allocation in GB"
    )


@tool
async def update_devbox_tool(
    devbox_name: str,
    state: Annotated[dict, InjectedState],
    cpu: Optional[Literal[1, 2, 4, 8, 16]] = None,
    memory: Optional[Literal[1, 2, 4, 8, 16, 32]] = None,
) -> Dict[str, Any]:
    """
    Update a devbox configuration (resource allocation).

    This tool should be invoked strictly for resources of kind 'devbox'.
    When referring to resources, always refer to devbox as 'devbox'.

    Args:
        devbox_name: Name of the devbox to update
        cpu: CPU allocation in cores (1, 2, 4, 8, or 16)
        memory: Memory allocation in GB (1, 2, 4, 8, 16, or 32)

    Returns:
        Dict containing the update operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Extract context from state
    approved = interrupt(
        {
            "action": "update_devbox",
            "payload": {
                "devbox_name": devbox_name,
                "cpu": cpu,
                "memory": memory,
            },
        }
    )

    # Check if the operation was approved
    if not approved or approved == "false":
        return {
            "action": "update_devbox",
            "payload": {
                "devbox_name": devbox_name,
                "cpu": cpu,
                "memory": memory,
            },
            "success": False,
            "error": "Operation rejected by user",
            "message": f"Update operation for devbox '{devbox_name}' was rejected by user",
        }

    context = extract_sealos_context(state, DevboxContext)

    # Create resource configuration only if at least one parameter is provided
    if cpu is not None or memory is not None:
        # Build resource dict with only provided parameters
        resource_dict = {}
        if cpu is not None:
            resource_dict["cpu"] = cpu
        if memory is not None:
            resource_dict["memory"] = memory

        resource = DevboxResource(**resource_dict)

        # Create payload for the devbox update
        payload = DevboxUpdatePayload(
            name=devbox_name,
            resource=resource,
        )
    else:
        raise ValueError("At least one of cpu or memory must be provided")

    try:
        # Call the actual update function
        result = update_devbox(context, payload)

        return {
            "action": "update_devbox",
            "payload": {
                "devbox_name": devbox_name,
                "cpu": cpu,
                "memory": memory,
            },
            "success": True,
            "result": result,
            "message": f"Successfully updated devbox '{devbox_name}'",
        }
    except Exception as e:
        return {
            "action": "update_devbox",
            "payload": {
                "devbox_name": devbox_name,
                "cpu": cpu,
                "memory": memory,
            },
            "success": False,
            "error": str(e),
            "message": f"Failed to update devbox '{devbox_name}': {str(e)}",
        }
