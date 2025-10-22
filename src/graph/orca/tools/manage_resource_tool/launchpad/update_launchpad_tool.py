"""
Update launchpad tool for the manage resource agent.
Handles launchpad configuration updates with state management.
"""

from typing import Optional, Dict, Any, Literal, Union
from typing_extensions import Annotated
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from langgraph.prebuilt import InjectedState
from langgraph.types import Command, interrupt

from src.utils.sealos.extract_context import extract_sealos_context
from src.utils.interrupt_utils import (
    handle_interrupt_with_approval,
    create_rejection_response,
)
from src.models.sealos.launchpad.launchpad_model import (
    LaunchpadContext,
)
from src.lib.brain.sealos.launchpad.update import (
    update_launchpad,
    BrainLaunchpadContext,
    LaunchpadUpdateData,
)
from src.lib.brain.sealos.launchpad.get import (
    get_launchpad,
    BrainLaunchpadContext as GetLaunchpadContext,
)


@tool
async def update_launchpad_tool(
    launchpad_name: str,
    state: Annotated[dict, InjectedState],
    cpu: Optional[Union[Literal["0.5", "1", "2", "4", "8", "16"], float, int]] = None,
    memory: Optional[
        Union[Literal["0.5", "1", "2", "4", "8", "16", "32"], float, int]
    ] = None,
    # replicas: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Update an app launchpad configuration (resource allocation).

    This tool should be invoked strictly for resources of kind 'deployment' and 'statefulset'.
    When referring to resources, always refer to launchpad as 'app launchpad'.

    IMPORTANT: Both cpu and memory parameters are necessary for invoking this tool.
    When the user asks for only one resource update, the model should take the
    current value of the other resource field from the resource context.

    CRITICAL: The values proposed by the model can be modified by the user at any time
    during the approval process. The model should keep this in mind and always use the
    actual result from this tool as the true modification applied. For example, if the
    model proposes 2 CPU cores and 2GB memory, but the result shows 2 CPU cores and 4GB
    memory, the model should understand that the user has modified the proposed values.

    IMPORTANT PRINCIPLE: When the user's intention is ambiguous (e.g., "I'd like to update app launchpad"
    instead of "I'd like to update app launchpad to 2c 4g"), the model should still invoke this tool
    with the current resource quota of the app launchpad (which would be sent to the model along with
    the request). This allows the user to modify the data themselves through the approval interface.
    This principle applies to all update operations where users don't specify detailed parameters.

    Args:
        launchpad_name: Name of the app launchpad to update
        cpu: CPU allocation in cores (0.5, 1, 2, 4, 8, or 16) - REQUIRED
        memory: Memory allocation in GB (0.5, 1, 2, 4, 8, 16, or 32) - REQUIRED
        # replicas: Number of replicas (1-20)

    Returns:
        Dict containing the update operation result

    Raises:
        ValueError: If required state values are missing or no resource parameters provided
        requests.RequestException: If the API request fails
    """
    # Handle interrupt with approval and parameter editing
    is_approved, edited_data, response_payload = handle_interrupt_with_approval(
        action="update_launchpad",
        payload={
            "launchpad_name": launchpad_name,
            "cpu": cpu,
            "memory": memory,
        },
        interrupt_func=interrupt,
        original_params={
            "launchpad_name": launchpad_name,
            "cpu": cpu,
            "memory": memory,
        },
    )

    # Check if the operation was approved
    if not is_approved:
        return create_rejection_response(
            action="update_launchpad",
            response_payload=response_payload,
            resource_name="app launchpad",
            operation_type="Update",
        )

    # Extract the edited parameters
    launchpad_name = edited_data.get("launchpad_name", launchpad_name)
    cpu = edited_data.get("cpu", cpu)
    memory = edited_data.get("memory", memory)

    # Convert string values to numbers
    if cpu is not None:
        cpu = float(cpu) if isinstance(cpu, str) else cpu
    if memory is not None:
        memory = float(memory) if isinstance(memory, str) else memory

    context = extract_sealos_context(state, LaunchpadContext)

    # Convert to brain context
    brain_context = BrainLaunchpadContext(kubeconfig=context.kubeconfig)

    # Get current launchpad state before update
    before_update = None
    try:
        get_context = GetLaunchpadContext(kubeconfig=context.kubeconfig)
        before_update = get_launchpad(get_context, launchpad_name)
    except Exception as e:
        print(f"Warning: Could not fetch current launchpad state: {e}")

    # Create update data
    update_data = LaunchpadUpdateData(
        name=launchpad_name,
        cpu=float(cpu) if cpu is not None else None,
        memory=float(memory) if memory is not None else None,
    )

    try:
        # Call the brain API function
        result = update_launchpad(brain_context, update_data)

        return {
            "action": "update_launchpad",
            "payload": {
                **edited_data,
                "before_update": before_update,
            },
            "success": True,
            "approved": True,
            "result": result,
            "message": f"Successfully updated launchpad '{launchpad_name}'",
        }
    except Exception as e:
        return {
            "action": "update_launchpad",
            "payload": {
                **edited_data,
                "before_update": before_update,
            },
            "success": False,
            "approved": True,
            "error": str(e),
            "message": f"Failed to update launchpad '{launchpad_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the update launchpad tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.launchpad.update_launchpad_tool

    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing update_launchpad_tool...")
    try:
        # Get kubeconfig from environment
        kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
        mock_state = {
            "kubeconfig": kubeconfig,
        }

        result = update_launchpad_tool.invoke(
            {
                "launchpad_name": "test-launchpad",
                "cpu": 4,
                "memory": 8,
                "state": mock_state,
            }
        )
        print("✅ Update launchpad tool test successful!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Update launchpad tool test failed: {e}")

    print(f"Tool name: {update_launchpad_tool.name}")
    print(f"Tool description: {update_launchpad_tool.description}")
