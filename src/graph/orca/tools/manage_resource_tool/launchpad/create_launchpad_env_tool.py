"""
Create launchpad environment variables tool for the manage resource agent.
Handles launchpad environment variable creation operations with state management.
"""

from typing import Dict, Any, List
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


class EnvVar(BaseModel):
    """Environment variable model."""

    name: str = Field(..., description="Environment variable name")
    value: str = Field(..., description="Environment variable value")


@tool
async def create_launchpad_env_tool(
    launchpad_name: str,
    env_vars: List[EnvVar],
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Create environment variables for an app launchpad instance.

    This tool should be invoked strictly for resources of kind 'deployment' and 'statefulset'.
    When referring to resources, always refer to launchpad as 'app launchpad'.

    Args:
        launchpad_name: Name of the app launchpad to create environment variables for
        env_vars: List of environment variables to create

    Returns:
        Dict containing the environment variable creation operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Handle interrupt with approval and parameter editing
    is_approved, edited_data, response_payload = handle_interrupt_with_approval(
        action="create_launchpad_env",
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
            action="create_launchpad_env",
            response_payload=response_payload,
            resource_name="app launchpad",
            operation_type="Create Environment Variables",
        )

    # Extract the edited parameters
    launchpad_name = edited_data.get("launchpad_name", launchpad_name)
    env_vars = edited_data.get("env_vars", env_vars)

    context = extract_sealos_context(state, LaunchpadContext)

    # Convert to brain context
    brain_context = BrainLaunchpadContext(kubeconfig=context.kubeconfig)

    # Convert env_vars to tuples for the API
    # env_vars can be either EnvVar objects or dictionaries depending on how the tool is called
    env_var_tuples = []
    for env_var in env_vars:
        if isinstance(env_var, dict):
            env_var_tuples.append((env_var["name"], env_var["value"]))
        else:
            env_var_tuples.append((env_var.name, env_var.value))

    # Create update data with environment variables to create
    update_data = LaunchpadUpdateData(
        name=launchpad_name,
        createEnv=env_var_tuples,
    )

    try:
        # Call the brain API function
        result = update_launchpad(brain_context, update_data)

        return {
            "action": "create_launchpad_env",
            "payload": edited_data,
            "success": True,
            "result": result,
            "message": f"Successfully created environment variables for launchpad '{launchpad_name}'",
        }
    except Exception as e:
        return {
            "action": "create_launchpad_env",
            "payload": edited_data,
            "success": False,
            "error": str(e),
            "message": f"Failed to create environment variables for launchpad '{launchpad_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the create launchpad environment variables tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.launchpad.create_launchpad_env_tool

    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing create_launchpad_env_tool...")
    try:
        # Get kubeconfig from environment
        kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
        mock_state = {
            "kubeconfig": kubeconfig,
        }

        result = create_launchpad_env_tool.invoke(
            {
                "launchpad_name": "test-launchpad",
                "env_vars": [
                    EnvVar(name="API_KEY", value="test-key"),
                    EnvVar(name="DEBUG", value="true"),
                ],
                "state": mock_state,
            }
        )
        print("✅ Create launchpad environment variables tool test successful!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Create launchpad environment variables tool test failed: {e}")

    print(f"Tool name: {create_launchpad_env_tool.name}")
    print(f"Tool description: {create_launchpad_env_tool.description}")
