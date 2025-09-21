"""
Create devbox ports tool for the manage resource agent.
Handles devbox port creation operations with state management.
"""

from typing import Dict, Any, List
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
from src.lib.brain.sealos.devbox.update import (
    update_devbox,
    BrainDevboxContext,
    DevboxUpdateData,
)


@tool
async def create_devbox_ports_tool(
    devbox_name: str,
    ports: List[int],
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Create ports for a devbox instance.

    This tool should be invoked strictly for resources of kind 'devbox'.
    When referring to resources, always refer to devbox as 'devbox'.

    Args:
        devbox_name: Name of the devbox to create ports for
        ports: List of port numbers to create

    Returns:
        Dict containing the port creation operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Handle interrupt with approval and parameter editing
    is_approved, edited_data, response_payload = handle_interrupt_with_approval(
        action="create_devbox_ports",
        payload={
            "devbox_name": devbox_name,
            "ports": ports,
        },
        interrupt_func=interrupt,
        original_params={
            "devbox_name": devbox_name,
            "ports": ports,
        },
    )

    # Check if the operation was approved
    if not is_approved:
        return create_rejection_response(
            action="create_devbox_ports",
            response_payload=response_payload,
            resource_name="devbox",
            operation_type="Create Ports",
        )

    # Extract the edited parameters
    devbox_name = edited_data.get("devbox_name", devbox_name)
    ports = edited_data.get("ports", ports)

    context = extract_sealos_context(state, DevboxContext)

    # Convert to brain context
    brain_context = BrainDevboxContext(kubeconfig=context.kubeconfig)

    # Create update data with ports to create
    update_data = DevboxUpdateData(
        name=devbox_name,
        create_ports=ports,
    )

    try:
        # Call the brain API function
        result = update_devbox(brain_context, update_data)

        return {
            "action": "create_devbox_ports",
            "payload": edited_data,
            "success": True,
            "result": result,
            "message": f"Successfully created ports {ports} for devbox '{devbox_name}'",
        }
    except Exception as e:
        return {
            "action": "create_devbox_ports",
            "payload": edited_data,
            "success": False,
            "error": str(e),
            "message": f"Failed to create ports for devbox '{devbox_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the create devbox ports tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.devbox.create_devbox_ports_tool

    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing create_devbox_ports_tool...")
    try:
        # Get kubeconfig from environment
        kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
        mock_state = {
            "kubeconfig": kubeconfig,
        }

        result = create_devbox_ports_tool.invoke(
            {"devbox_name": "test-devbox", "ports": [8080, 3000], "state": mock_state}
        )
        print("✅ Create devbox ports tool test successful!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Create devbox ports tool test failed: {e}")

    print(f"Tool name: {create_devbox_ports_tool.name}")
    print(f"Tool description: {create_devbox_ports_tool.description}")
