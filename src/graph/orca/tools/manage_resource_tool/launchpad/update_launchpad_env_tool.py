"""
Update launchpad environment variables tool for the manage resource agent.
Handles launchpad environment variable update operations with state management.
"""

from typing import Dict, Any, List, Tuple
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
async def update_launchpad_env_tool(
    launchpad_name: str,
    env_vars: List[Tuple[str, str]],
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Update environment variables for an app launchpad instance.

    This tool should be invoked strictly for resources of kind 'deployment' and 'statefulset'.
    When referring to resources, always refer to launchpad as 'app launchpad'.

    Args:
        launchpad_name: Name of the app launchpad to update environment variables for
        env_vars: List of tuples containing (name, value) pairs for environment variables to update

    Returns:
        Dict containing the environment variable update operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Handle interrupt with approval and parameter editing
    is_approved, edited_data, response_payload = handle_interrupt_with_approval(
        action="update_launchpad_env",
        payload={
            "launchpad_name": launchpad_name,
            "env_vars": env_vars,
        },
        interrupt_func=interrupt,
        original_params={
            "launchpad_name": launchpad_name,
            "env_vars": env_vars,
        },
    )

    # Check if the operation was approved
    if not is_approved:
        return create_rejection_response(
            action="update_launchpad_env",
            response_payload=response_payload,
            resource_name="app launchpad",
            operation_type="Update Environment Variables",
        )

    # Extract the edited parameters
    launchpad_name = edited_data.get("launchpad_name", launchpad_name)
    env_vars = edited_data.get("env_vars", env_vars)

    context = extract_sealos_context(state, LaunchpadContext)

    # Convert to brain context
    brain_context = BrainLaunchpadContext(kubeconfig=context.kubeconfig)

    # Create update data with environment variables to update
    update_data = LaunchpadUpdateData(
        name=launchpad_name,
        update_env=env_vars,
    )

    try:
        # Call the brain API function
        result = update_launchpad(brain_context, update_data)

        return {
            "action": "update_launchpad_env",
            "payload": edited_data,
            "success": True,
            "result": result,
            "message": f"Successfully updated environment variables for launchpad '{launchpad_name}'",
        }
    except Exception as e:
        return {
            "action": "update_launchpad_env",
            "payload": edited_data,
            "success": False,
            "error": str(e),
            "message": f"Failed to update environment variables for launchpad '{launchpad_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the update launchpad environment variables tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.launchpad.update_launchpad_env_tool

    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing update_launchpad_env_tool...")
    try:
        # Get kubeconfig from environment
        kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
        mock_state = {
            "kubeconfig": kubeconfig,
        }

        result = update_launchpad_env_tool.invoke(
            {
                "launchpad_name": "test-launchpad",
                "env_vars": [("API_KEY", "new-key"), ("DEBUG", "false")],
                "state": mock_state,
            }
        )
        print("✅ Update launchpad environment variables tool test successful!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Update launchpad environment variables tool test failed: {e}")

    print(f"Tool name: {update_launchpad_env_tool.name}")
    print(f"Tool description: {update_launchpad_env_tool.description}")
