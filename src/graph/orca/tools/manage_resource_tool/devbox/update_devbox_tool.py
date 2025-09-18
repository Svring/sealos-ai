"""
Update devbox tool for the manage resource agent.
Handles devbox configuration updates with state management.
"""

from typing import Optional, Dict, Any, Literal
from typing_extensions import Annotated
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langgraph.prebuilt import InjectedState

from src.utils.context_utils import get_state_values
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
    devboxName: str,
    state: Annotated[dict, InjectedState],
    cpu: Optional[Literal[1, 2, 4, 8, 16]] = None,
    memory: Optional[Literal[1, 2, 4, 8, 16, 32]] = None,
) -> Dict[str, Any]:
    """
    Update a devbox configuration (resource allocation).

    Args:
        devboxName: Name of the devbox to update
        state: State containing the region_url and kubeconfig
        cpu: CPU allocation in cores (1, 2, 4, 8, or 16)
        memory: Memory allocation in GB (1, 2, 4, 8, 16, or 32)
        state: State containing the region_url and kubeconfig

    Returns:
        Dict containing the update operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Extract state data from config
    (
        region_url,
        kubeconfig,
    ) = get_state_values(
        state,
        {
            "region_url": None,
            "kubeconfig": None,
        },
    )

    if not region_url:
        raise ValueError("region_url is required in state")
    if not kubeconfig:
        raise ValueError("kubeconfig is required in state")

    # Create context for the devbox update
    context = DevboxContext(
        kubeconfig=kubeconfig,
        regionUrl=region_url,
    )

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
            name=devboxName,
            resource=resource,
        )
    else:
        raise ValueError("At least one of cpu or memory must be provided")

    try:
        # Call the actual update function
        result = update_devbox(context, payload)

        return {
            "action": "updateDevbox",
            "success": True,
            "devboxName": devboxName,
            "result": result,
            "message": f"Successfully updated devbox '{devboxName}'",
        }
    except Exception as e:
        return {
            "action": "updateDevbox",
            "success": False,
            "devboxName": devboxName,
            "error": str(e),
            "message": f"Failed to update devbox '{devboxName}': {str(e)}",
        }
