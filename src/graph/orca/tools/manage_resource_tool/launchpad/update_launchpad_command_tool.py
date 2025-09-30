"""
Update launchpad command tool for the manage resource agent.
Handles launchpad command update operations with state management.
"""

from typing import Dict, Any
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from langgraph.types import interrupt
from pydantic import BaseModel, Field

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
from src.lib.brain.sealos.launchpad.get import (
    get_launchpad,
    BrainLaunchpadContext as GetLaunchpadContext,
)


class LaunchCommand(BaseModel):
    """Launch command model containing both command and arguments."""

    command: str = Field(..., description="Command to execute")
    args: str = Field(..., description="Arguments for the command")


@tool
async def update_launchpad_command_tool(
    launchpad_name: str,
    launch_command: LaunchCommand,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Update the command and arguments for an app launchpad instance.

    This tool should be invoked strictly for resources of kind 'deployment' and 'statefulset'.
    When referring to resources, always refer to launchpad as 'app launchpad'.

    CRITICAL: The model MUST determine the command and args by itself from the user's request
    and call this tool directly WITHOUT asking the user any questions. Do NOT ask the user to specify
    command and args separately. The user can modify the proposed values through the approval interface if needed.

    CRITICAL: The values proposed by the model can be modified by the user at any time
    during the approval process. The model should keep this in mind and always use the
    actual result from this tool as the true modification applied.

    IMPORTANT PRINCIPLE: When the user's intention is ambiguous (e.g., "I'd like to update command"
    instead of "I'd like to update command to python app.py"), the model should still invoke this tool
    with reasonable default values or current command values. This allows the user to modify the data
    themselves through the approval interface.

    CRITICAL: If the user doesn't specify command and args, or if they're empty, the model should
    still call this tool with empty strings for both command and args. The tool will handle empty values
    appropriately and allow the user to modify them through the approval interface.

    Examples of how to determine command and args:
    - User says "set command to python -m app.py" → command="python -m", args="app.py"
    - User says "update to node server.js --port 3000" → command="node", args="server.js --port 3000"
    - User says "change to java -jar myapp.jar" → command="java -jar", args="myapp.jar"

    IMPORTANT: Both command and args must be provided as strings, not lists. For example:
    - Correct: args="app.py"
    - Incorrect: args=["app.py"]

    Args:
        launchpad_name: Name of the app launchpad to update the command for
        launch_command: LaunchCommand object containing both command and args as strings

    Returns:
        Dict containing the command update operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Handle interrupt with approval and parameter editing
    is_approved, edited_data, response_payload = handle_interrupt_with_approval(
        action="update_launchpad_command",
        payload={
            "launchpad_name": launchpad_name,
            "launch_command": launch_command,
        },
        interrupt_func=interrupt,
        original_params={
            "launchpad_name": launchpad_name,
            "launch_command": launch_command,
        },
    )

    # Check if the operation was approved
    if not is_approved:
        return create_rejection_response(
            action="update_launchpad_command",
            response_payload=response_payload,
            resource_name="app launchpad",
            operation_type="Update Command",
        )

    # Extract the edited parameters
    launchpad_name = edited_data.get("launchpad_name", launchpad_name)
    launch_command = edited_data.get("launch_command", launch_command)

    # print(f"launch_command: {launch_command}")

    # Extract command and args from the LaunchCommand object
    if isinstance(launch_command, dict):
        command = launch_command.get("command", "")
        args = launch_command.get("args", "")
    else:
        command = launch_command.command
        args = launch_command.args

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

    # Create update data with new command and args
    update_data = LaunchpadUpdateData(
        name=launchpad_name,
        updateCommand=(command, args),
    )

    try:
        # Call the brain API function
        result = update_launchpad(brain_context, update_data)

        return {
            "action": "update_launchpad_command",
            "payload": {
                **edited_data,
                "before_update": before_update,
            },
            "success": True,
            "approved": True,
            "result": result,
            "message": f"Successfully updated command to '{command} {args}' for launchpad '{launchpad_name}'",
        }
    except Exception as e:
        return {
            "action": "update_launchpad_command",
            "payload": {
                **edited_data,
                "before_update": before_update,
            },
            "success": False,
            "approved": True,
            "error": str(e),
            "message": f"Failed to update command for launchpad '{launchpad_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the update launchpad command tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.launchpad.update_launchpad_command_tool

    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing update_launchpad_command_tool...")
    try:
        # Get kubeconfig from environment
        kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
        mock_state = {
            "kubeconfig": kubeconfig,
        }

        result = update_launchpad_command_tool.invoke(
            {
                "launchpad_name": "test-launchpad",
                "launch_command": LaunchCommand(
                    command="python", args="app.py --port 8080"
                ),
                "state": mock_state,
            }
        )
        print("✅ Update launchpad command tool test successful!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Update launchpad command tool test failed: {e}")

    print(f"Tool name: {update_launchpad_command_tool.name}")
    print(f"Tool description: {update_launchpad_command_tool.description}")
