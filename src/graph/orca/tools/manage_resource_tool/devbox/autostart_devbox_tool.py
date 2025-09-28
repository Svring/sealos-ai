"""
Autostart devbox tool for the manage resource agent.
Handles devbox autostart operations with state management.
"""

from typing import Dict, Any
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from src.utils.sealos.extract_context import extract_sealos_context
from src.models.sealos.devbox.devbox_model import DevboxContext
from src.lib.brain.sealos.devbox.autostart import (
    devbox_autostart,
    BrainDevboxContext,
)


@tool
async def autostart_devbox_tool(
    devbox_name: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Enable autostart for a devbox instance by executing its predefined entrypoint.sh script.

    This tool executes a predefined entrypoint.sh script based on the devbox's runtime, which
    starts a process listening on a port of the devbox. It is particularly useful for fixing
    network access issues when a devbox is launched (pod active) but the program inside it
    doesn't spawn a process to listen on the port that the external service is exposing.

    **Network Issue Resolution:**
    - If a devbox is paused: network access fails - use start_devbox_tool first
    - If a devbox is started but no process is listening on ports: network access fails - use this autostart tool
    - After executing autostart, wait for a moment as it takes time to take effect

    This tool should be invoked strictly for resources of kind 'devbox'.
    When referring to resources, always refer to devbox as 'devbox'.

    Args:
        devbox_name: Name of the devbox to enable autostart for

    Returns:
        Dict containing the autostart operation result

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Prepare payload for response
    payload = {
        "devbox_name": devbox_name,
    }

    context = extract_sealos_context(state, DevboxContext)

    # Convert to brain context
    brain_context = BrainDevboxContext(kubeconfig=context.kubeconfig)

    try:
        # Call the brain API function
        result = devbox_autostart(brain_context, devbox_name)

        return {
            "action": "autostart_devbox",
            "payload": payload,
            "success": True,
            "result": result,
            "message": f"Successfully enabled autostart for devbox '{devbox_name}'",
        }
    except Exception as e:
        return {
            "action": "autostart_devbox",
            "payload": payload,
            "success": False,
            "error": str(e),
            "message": f"Failed to enable autostart for devbox '{devbox_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the autostart devbox tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.devbox.autostart_devbox_tool

    import asyncio

    async def test_autostart_devbox():
        import os
        from dotenv import load_dotenv

        load_dotenv()

        print("Testing autostart_devbox_tool...")
        try:
            # Get kubeconfig from environment
            kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
            mock_state = {
                "kubeconfig": kubeconfig,
            }

            result = await autostart_devbox_tool.ainvoke(
                {"devbox_name": "test-devbox", "state": mock_state}
            )
            print("✅ Autostart devbox tool test successful!")
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ Autostart devbox tool test failed: {e}")

        print(f"Tool name: {autostart_devbox_tool.name}")
        print(f"Tool description: {autostart_devbox_tool.description}")

    asyncio.run(test_autostart_devbox())
