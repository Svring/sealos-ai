"""
Update launchpad tool for the manage resource agent.
Handles launchpad configuration updates with state management.
"""

from typing import Optional, Dict, Any, Literal
from typing_extensions import Annotated
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langgraph.prebuilt import InjectedState
from langgraph.types import Command, interrupt

from src.utils.sealos.extract_context import extract_sealos_context
from src.models.sealos.launchpad.launchpad_model import (
    LaunchpadContext,
    LaunchpadUpdatePayload,
    LaunchpadResource,
)
from src.lib.sealos.launchpad.update_launchpad import update_launchpad


@tool
async def update_launchpad_tool(
    launchpad_name: str,
    state: Annotated[dict, InjectedState],
    cpu: Optional[Literal[1, 2, 4, 8, 16]] = None,
    memory: Optional[Literal[1, 2, 4, 8, 16, 32]] = None,
    # replicas: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Update an app launchpad configuration (resource allocation).

    This tool should be invoked strictly for resources of kind 'deployment' and 'statefulset'.
    When referring to resources, always refer to launchpad as 'app launchpad'.

    Args:
        launchpad_name: Name of the app launchpad to update
        cpu: CPU allocation in cores (1, 2, 4, 8, or 16)
        memory: Memory allocation in GB (1, 2, 4, 8, 16, or 32)
        # replicas: Number of replicas (1-20)

    Returns:
        Dict containing the update operation result

    Raises:
        ValueError: If required state values are missing or no resource parameters provided
        requests.RequestException: If the API request fails
    """
    # Extract context from state
    approved = interrupt(
        {
            "action": "update_launchpad",
            "payload": {
                "launchpad_name": launchpad_name,
                "cpu": cpu,
                "memory": memory,
            },
        }
    )

    # Check if the operation was approved
    if not approved or approved == "false":
        return {
            "action": "update_launchpad",
            "payload": {
                "launchpad_name": launchpad_name,
                "cpu": cpu,
                "memory": memory,
            },
            "success": False,
            "error": "Operation rejected by user",
            "message": f"Update operation for launchpad '{launchpad_name}' was rejected by user",
        }

    context = extract_sealos_context(state, LaunchpadContext)

    # Create resource configuration only if at least one parameter is provided
    if cpu is not None or memory is not None:
        # Build resource dict with only provided parameters
        resource_dict = {}
        if cpu is not None:
            resource_dict["cpu"] = cpu
        if memory is not None:
            resource_dict["memory"] = memory

        resource = LaunchpadResource(**resource_dict)

        # Create payload for the launchpad update
        payload = LaunchpadUpdatePayload(
            name=launchpad_name,
            resource=resource,
        )
    else:
        raise ValueError("At least one of cpu or memory must be provided")

    try:
        # Call the actual update function
        result = update_launchpad(context, payload)

        return {
            "action": "update_launchpad",
            "payload": {
                "launchpad_name": launchpad_name,
                "cpu": cpu,
                "memory": memory,
            },
            "success": True,
            "result": result,
            "message": f"Successfully updated launchpad '{launchpad_name}'",
        }
    except Exception as e:
        return {
            "action": "update_launchpad",
            "payload": {
                "launchpad_name": launchpad_name,
                "cpu": cpu,
                "memory": memory,
            },
            "success": False,
            "error": str(e),
            "message": f"Failed to update launchpad '{launchpad_name}': {str(e)}",
        }
