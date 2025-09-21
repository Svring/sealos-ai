"""
Update launchpad image tool for the manage resource agent.
Handles launchpad image update operations with state management.
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
from src.models.sealos.launchpad.launchpad_model import LaunchpadContext
from src.lib.brain.sealos.launchpad.update import (
    update_launchpad,
    BrainLaunchpadContext,
    LaunchpadUpdateData,
)


@tool
async def update_launchpad_image_tool(
    launchpad_name: str,
    image: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Update the image for an app launchpad instance.

    This tool should be invoked strictly for resources of kind 'deployment' and 'statefulset'.
    When referring to resources, always refer to launchpad as 'app launchpad'.

    Args:
        launchpad_name: Name of the app launchpad to update the image for
        image: New image name to update to

    Returns:
        Dict containing the image update operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Handle interrupt with approval and parameter editing
    is_approved, edited_data, response_payload = handle_interrupt_with_approval(
        action="update_launchpad_image",
        payload={
            "launchpad_name": launchpad_name,
            "image": image,
        },
        interrupt_func=interrupt,
        original_params={
            "launchpad_name": launchpad_name,
            "image": image,
        },
    )

    # Check if the operation was approved
    if not is_approved:
        return create_rejection_response(
            action="update_launchpad_image",
            response_payload=response_payload,
            resource_name="app launchpad",
            operation_type="Update Image",
        )

    # Extract the edited parameters
    launchpad_name = edited_data.get("launchpad_name", launchpad_name)
    image = edited_data.get("image", image)

    context = extract_sealos_context(state, LaunchpadContext)

    # Convert to brain context
    brain_context = BrainLaunchpadContext(kubeconfig=context.kubeconfig)

    # Create update data with new image
    update_data = LaunchpadUpdateData(
        name=launchpad_name,
        updateImage=image,
    )

    try:
        # Call the brain API function
        result = update_launchpad(brain_context, update_data)

        return {
            "action": "update_launchpad_image",
            "payload": edited_data,
            "success": True,
            "result": result,
            "message": f"Successfully updated image to '{image}' for launchpad '{launchpad_name}'",
        }
    except Exception as e:
        return {
            "action": "update_launchpad_image",
            "payload": edited_data,
            "success": False,
            "error": str(e),
            "message": f"Failed to update image for launchpad '{launchpad_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the update launchpad image tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.launchpad.update_launchpad_image_tool

    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing update_launchpad_image_tool...")
    try:
        # Get kubeconfig from environment
        kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
        mock_state = {
            "kubeconfig": kubeconfig,
        }

        result = update_launchpad_image_tool.invoke(
            {
                "launchpad_name": "test-launchpad",
                "image": "nginx:latest",
                "state": mock_state,
            }
        )
        print("✅ Update launchpad image tool test successful!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Update launchpad image tool test failed: {e}")

    print(f"Tool name: {update_launchpad_image_tool.name}")
    print(f"Tool description: {update_launchpad_image_tool.description}")
