"""
Create launchpad tool for the manage resource agent.
Handles launchpad creation operations with state management.
"""

from typing import Dict, Any, List, Optional
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
from src.lib.brain.sealos.launchpad.create import (
    create_launchpad,
    BrainLaunchpadContext,
    LaunchpadCreateData,
)


class EnvVar(BaseModel):
    """Environment variable model."""

    name: str = Field(..., description="Environment variable name")
    value: str = Field(..., description="Environment variable value")


@tool
async def create_launchpad_tool(
    name: str,
    image: str,
    state: Annotated[dict, InjectedState],
    cpu: int = 1,
    memory: int = 1,
    ports: Optional[List[int]] = None,
    env: Optional[List[EnvVar]] = None,
) -> Dict[str, Any]:
    """
    Create a new app launchpad instance.

    This tool should be invoked strictly for resources of kind 'deployment' and 'statefulset'.
    When referring to resources, always refer to launchpad as 'app launchpad'.

    Args:
        name: Name of the app launchpad to create
        image: Docker image name
        cpu: CPU allocation in cores (default: 1)
        memory: Memory allocation in GB (default: 1)
        ports: Array of port numbers to expose (optional)
        env: Array of environment variables (optional)

    Returns:
        Dict containing the app launchpad creation operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Handle interrupt with approval and parameter editing
    is_approved, edited_data, response_payload = handle_interrupt_with_approval(
        action="create_launchpad",
        payload={
            "name": name,
            "image": image,
            "cpu": cpu,
            "memory": memory,
            "ports": ports or [],
            "env": env or [],
        },
        interrupt_func=interrupt,
        original_params={
            "name": name,
            "image": image,
            "cpu": cpu,
            "memory": memory,
            "ports": ports or [],
            "env": env or [],
        },
    )

    # Check if the operation was approved
    if not is_approved:
        return create_rejection_response(
            action="create_launchpad",
            response_payload=response_payload,
            resource_name="app launchpad",
            operation_type="Create",
        )

    # Extract the edited parameters
    launchpad_name = edited_data.get("name", name)
    image = edited_data.get("image", image)
    cpu = edited_data.get("cpu", cpu)
    memory = edited_data.get("memory", memory)
    ports = edited_data.get("ports", ports or [])
    env = edited_data.get("env", env or [])

    context = extract_sealos_context(state, LaunchpadContext)

    # Convert to brain context
    brain_context = BrainLaunchpadContext(kubeconfig=context.kubeconfig)

    # Convert env_vars to tuples for the API
    env_var_tuples = []
    if env:
        for env_var in env:
            if isinstance(env_var, dict):
                env_var_tuples.append((env_var["name"], env_var["value"]))
            else:
                env_var_tuples.append((env_var.name, env_var.value))

    # Create launchpad data
    create_data = LaunchpadCreateData(
        name=launchpad_name,
        image=image,
        cpu=cpu,
        memory=memory,
        ports=ports,
        env=env_var_tuples,
    )

    try:
        # Call the brain API function
        result = create_launchpad(brain_context, create_data)

        return {
            "action": "create_launchpad",
            "payload": edited_data,
            "success": True,
            "approved": True,
            "result": result,
            "message": f"Successfully created app launchpad '{launchpad_name}' with image '{image}'",
        }
    except Exception as e:
        return {
            "action": "create_launchpad",
            "payload": edited_data,
            "success": False,
            "approved": True,
            "error": str(e),
            "message": f"Failed to create app launchpad '{launchpad_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the create launchpad tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.launchpad.create_launchpad_tool

    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing create_launchpad_tool...")
    try:
        # Get kubeconfig from environment
        kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
        mock_state = {
            "kubeconfig": kubeconfig,
        }

        result = create_launchpad_tool.invoke(
            {
                "name": "test-launchpad",
                "image": "nginx:latest",
                "cpu": 2,
                "memory": 4,
                "ports": [80, 443],
                "env": [
                    EnvVar(name="ENV", value="production"),
                    EnvVar(name="DEBUG", value="false"),
                ],
                "state": mock_state,
            }
        )
        print("✅ Create launchpad tool test successful!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Create launchpad tool test failed: {e}")

    print(f"Tool name: {create_launchpad_tool.name}")
    print(f"Tool description: {create_launchpad_tool.description}")
