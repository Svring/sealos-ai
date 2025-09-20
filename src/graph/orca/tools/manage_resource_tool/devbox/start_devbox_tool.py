"""
Start devbox tool for the manage resource agent.
Handles devbox start operations with state management.
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
from src.lib.brain.sealos.devbox.lifecycle import (
    devbox_lifecycle,
    BrainDevboxContext,
    DevboxLifecycleAction,
)


@tool
async def start_devbox_tool(
    devbox_name: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Start a devbox instance.

    This tool should be invoked strictly for resources of kind 'devbox'.
    When referring to resources, always refer to devbox as 'devbox'.

    Args:
        devbox_name: Name of the devbox to start

    Returns:
        Dict containing the start operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Handle interrupt with approval and parameter editing
    is_approved, edited_data, response_payload = handle_interrupt_with_approval(
        action="start_devbox",
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
            action="start_devbox",
            response_payload=response_payload,
            resource_name="devbox",
            operation_type="Start",
        )

    # Extract the edited parameters
    devbox_name = edited_data.get("devbox_name", devbox_name)

    context = extract_sealos_context(state, DevboxContext)

    # Convert to brain context
    brain_context = BrainDevboxContext(kubeconfig=context.kubeconfig)

    # Create lifecycle action
    action = DevboxLifecycleAction(action="start")

    try:
        # Call the brain API function
        result = devbox_lifecycle(brain_context, devbox_name, action)

        return {
            "action": "start_devbox",
            "payload": edited_data,
            "success": True,
            "result": result,
            "message": f"Successfully started devbox '{devbox_name}'",
        }
    except Exception as e:
        return {
            "action": "start_devbox",
            "payload": edited_data,
            "success": False,
            "error": str(e),
            "message": f"Failed to start devbox '{devbox_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the start devbox tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.devbox.start_devbox_tool

    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing start_devbox_tool...")
    try:
        # Get kubeconfig from environment
        kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
        mock_state = {
            "kubeconfig": kubeconfig,
        }

        result = start_devbox_tool.invoke(
            {"devbox_name": "test-devbox", "state": mock_state}
        )
        print("✅ Start devbox tool test successful!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Start devbox tool test failed: {e}")

    print(f"Tool name: {start_devbox_tool.name}")
    print(f"Tool description: {start_devbox_tool.description}")
