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
from src.utils.interrupt_utils import (
    handle_interrupt_with_approval,
    create_rejection_response,
)
from src.models.sealos.devbox.devbox_model import (
    DevboxContext,
    DevboxUpdatePayload,
    DevboxResource,
)
from src.lib.brain.sealos.devbox.update import (
    update_devbox,
    BrainDevboxContext,
    DevboxUpdateData,
)


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

    IMPORTANT: Both cpu and memory parameters are necessary for invoking this tool.
    When the user asks for only one resource update, the model should take the
    current value of the other resource field from the resource context.

    Args:
        devbox_name: Name of the devbox to update
        cpu: CPU allocation in cores (1, 2, 4, 8, or 16) - REQUIRED
        memory: Memory allocation in GB (1, 2, 4, 8, 16, or 32) - REQUIRED

    Returns:
        Dict containing the update operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Handle interrupt with approval and parameter editing
    is_approved, edited_data, response_payload = handle_interrupt_with_approval(
        action="update_devbox",
        payload={
            "devbox_name": devbox_name,
            "cpu": cpu,
            "memory": memory,
        },
        interrupt_func=interrupt,
        original_params={
            "devbox_name": devbox_name,
            "cpu": cpu,
            "memory": memory,
        },
    )

    # Check if the operation was approved
    if not is_approved:
        return create_rejection_response(
            action="update_devbox",
            response_payload=response_payload,
            resource_name="devbox",
            operation_type="Update",
        )

    # Extract the edited parameters
    devbox_name = edited_data.get("devbox_name", devbox_name)
    cpu = edited_data.get("cpu", cpu)
    memory = edited_data.get("memory", memory)

    context = extract_sealos_context(state, DevboxContext)

    # Convert to brain context
    brain_context = BrainDevboxContext(kubeconfig=context.kubeconfig)

    # Create update data
    update_data = DevboxUpdateData(
        name=devbox_name,
        cpu=cpu,
        memory=memory,
    )

    try:
        # Call the brain API function
        result = update_devbox(brain_context, update_data)

        return {
            "action": "update_devbox",
            "payload": edited_data,
            "success": True,
            "result": result,
            "message": f"Successfully updated devbox '{devbox_name}'",
        }
    except Exception as e:
        return {
            "action": "update_devbox",
            "payload": edited_data,
            "success": False,
            "error": str(e),
            "message": f"Failed to update devbox '{devbox_name}': {str(e)}",
        }
