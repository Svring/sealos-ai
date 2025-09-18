"""
Update launchpad tool for the manage resource agent.
Handles launchpad configuration updates with state management.
"""

from typing import Optional, Dict, Any, Literal
from typing_extensions import Annotated
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langgraph.prebuilt import InjectedState

from src.utils.context_utils import get_state_values
from src.models.sealos.launchpad.launchpad_model import (
    LaunchpadContext,
    LaunchpadUpdatePayload,
    LaunchpadResource,
)
from src.lib.sealos.launchpad.update_launchpad import update_launchpad


@tool
async def update_launchpad_tool(
    launchpadName: str,
    state: Annotated[dict, InjectedState],
    cpu: Optional[Literal[1, 2, 4, 8, 16]] = None,
    memory: Optional[Literal[1, 2, 4, 8, 16, 32]] = None,
    replicas: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Update a launchpad configuration (resource allocation).

    Args:
        launchpadName: Name of the launchpad to update
        state: State containing the region_url and kubeconfig
        cpu: CPU allocation in cores (1, 2, 4, 8, or 16)
        memory: Memory allocation in GB (1, 2, 4, 8, 16, or 32)
        replicas: Number of replicas (1-20)

    Returns:
        Dict containing the update operation result

    Raises:
        ValueError: If required state values are missing or no resource parameters provided
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

    # Create context for the launchpad update
    context = LaunchpadContext(
        kubeconfig=kubeconfig,
        regionUrl=region_url,
    )

    # Create resource configuration only if at least one parameter is provided
    if cpu is not None or memory is not None or replicas is not None:
        # Build resource dict with only provided parameters
        resource_dict = {}
        if cpu is not None:
            resource_dict["cpu"] = cpu
        if memory is not None:
            resource_dict["memory"] = memory
        if replicas is not None:
            resource_dict["replicas"] = replicas

        resource = LaunchpadResource(**resource_dict)

        # Create payload for the launchpad update
        payload = LaunchpadUpdatePayload(
            name=launchpadName,
            resource=resource,
        )
    else:
        raise ValueError("At least one of cpu, memory, or replicas must be provided")

    try:
        # Call the actual update function
        result = update_launchpad(context, payload)

        return {
            "action": "updateLaunchpad",
            "success": True,
            "launchpadName": launchpadName,
            "result": result,
            "message": f"Successfully updated launchpad '{launchpadName}'",
        }
    except Exception as e:
        return {
            "action": "updateLaunchpad",
            "success": False,
            "launchpadName": launchpadName,
            "error": str(e),
            "message": f"Failed to update launchpad '{launchpadName}': {str(e)}",
        }
