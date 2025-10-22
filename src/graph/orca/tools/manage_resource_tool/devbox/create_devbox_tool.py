"""
Create devbox tool for the manage resource agent.
Handles devbox creation operations with state management.
"""

from typing import Dict, Any, Literal, List, Optional
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
from src.lib.brain.sealos.devbox.create import (
    create_devbox,
    BrainDevboxContext,
    DevboxCreateData,
)


@tool
async def create_devbox_tool(
    name: str,
    state: Annotated[dict, InjectedState],
    runtime: Literal[
        "quarkus",
        "hugo",
        "debian-ssh",
        "vue",
        "rust",
        "nuxt3",
        "gin",
        "mcp",
        "django",
        "ubuntu",
        "docusaurus",
        "vert.x",
        "go",
        "svelte",
        "python",
        "echo",
        "chi",
        "java",
        "react",
        "umi",
        "net",
        "iris",
        "c",
        "next.js",
        "node.js",
        "spring-boot",
        "express.js",
        "flask",
        "cpp",
        "nginx",
        "astro",
        "php",
        "hexo",
        "angular",
        "vitepress",
        "rocket",
    ],
    cpu: int = 2,
    memory: int = 4,
    ports: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Create a new devbox instance.

    This tool should be invoked strictly for resources of kind 'devbox'.
    When referring to resources, always refer to devbox as 'devbox'.

    IMPORTANT: When you call this tool, make sure to add random characters
    to the end of the name you provide to avoid name collisions with existing
    resources. For example, if you want to create a devbox called "my-devbox",
    append something like "my-devbox-abc123" or "my-devbox-xyz789" to make it unique.

    Args:
        name: Name of the devbox to create (add random characters to avoid collisions)
        runtime: Runtime environment name
        cpu: CPU allocation in cores (default: 2)
        memory: Memory allocation in GB (default: 2)
        ports: Array of port numbers to expose (optional)

    Returns:
        Dict containing the devbox creation operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Handle interrupt with approval and parameter editing
    is_approved, edited_data, response_payload = handle_interrupt_with_approval(
        action="create_devbox",
        payload={
            "name": name,
            "runtime": runtime,
            "cpu": cpu,
            "memory": memory,
            "ports": ports or [],
        },
        interrupt_func=interrupt,
        original_params={
            "name": name,
            "runtime": runtime,
            "cpu": cpu,
            "memory": memory,
            "ports": ports or [],
        },
    )

    # Check if the operation was approved
    if not is_approved:
        return create_rejection_response(
            action="create_devbox",
            response_payload=response_payload,
            resource_name="devbox",
            operation_type="Create",
        )

    # Extract the edited parameters
    devbox_name = edited_data.get("name", name)
    runtime = edited_data.get("runtime", runtime)
    cpu = edited_data.get("cpu", cpu)
    memory = edited_data.get("memory", memory)
    ports = edited_data.get("ports", ports or [])

    context = extract_sealos_context(state, DevboxContext)

    # Convert to brain context
    brain_context = BrainDevboxContext(kubeconfig=context.kubeconfig)

    # Create devbox data
    create_data = DevboxCreateData(
        name=devbox_name,
        runtime=runtime,
        cpu=cpu,
        memory=memory,
        ports=ports,
    )

    try:
        # Call the brain API function
        result = create_devbox(brain_context, create_data)

        return {
            "action": "create_devbox",
            "payload": edited_data,
            "success": True,
            "approved": True,
            "result": result,
            "message": f"Successfully created devbox '{devbox_name}' with runtime '{runtime}'",
        }
    except Exception as e:
        return {
            "action": "create_devbox",
            "payload": edited_data,
            "success": False,
            "approved": True,
            "error": str(e),
            "message": f"Failed to create devbox '{devbox_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the create devbox tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.devbox.create_devbox_tool

    import os
    from dotenv import load_dotenv

    load_dotenv()

    print("Testing create_devbox_tool...")
    try:
        # Get kubeconfig from environment
        kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
        mock_state = {
            "kubeconfig": kubeconfig,
        }

        result = create_devbox_tool.invoke(
            {
                "name": "test-devbox",
                "runtime": "python",
                "cpu": 2,
                "memory": 4,
                "ports": [8080, 3000],
                "state": mock_state,
            }
        )
        print("✅ Create devbox tool test successful!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Create devbox tool test failed: {e}")

    print(f"Tool name: {create_devbox_tool.name}")
    print(f"Tool description: {create_devbox_tool.description}")
