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

    IMPORTANT: Both cpu and memory parameters are necessary for invoking this tool.
    When the user asks for only one resource update, the model should take the
    current value of the other resource field from the resource context.

    Args:
        launchpad_name: Name of the app launchpad to update
        cpu: CPU allocation in cores (1, 2, 4, 8, or 16) - REQUIRED
        memory: Memory allocation in GB (1, 2, 4, 8, 16, or 32) - REQUIRED
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

    context = extract_sealos_context(state, LaunchpadContext)

    # Convert to brain context
    brain_context = BrainLaunchpadContext(kubeconfig=context.kubeconfig)

    # Create update data
    update_data = LaunchpadUpdateData(
        name=launchpad_name,
        cpu=cpu,
        memory=memory,
    )

    try:
        # Call the brain API function
        result = update_launchpad(brain_context, update_data)

        return {
            "action": "update_launchpad",
            "payload": edited_data,
            "success": True,
            "result": result,
            "message": f"Successfully updated launchpad '{launchpad_name}'",
        }
    except Exception as e:
        return {
            "action": "update_launchpad",
            "payload": edited_data,
            "success": False,
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
