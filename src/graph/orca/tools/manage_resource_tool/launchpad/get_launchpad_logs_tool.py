"""
Get launchpad logs tool for the manage resource agent.
Handles launchpad logs retrieval with state management.
"""

from typing import Dict, Any
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from src.utils.sealos.extract_context import extract_sealos_context
from src.models.sealos.launchpad.launchpad_model import LaunchpadContext
from src.lib.brain.sealos.launchpad.logs import (
    get_launchpad_logs,
    BrainLaunchpadContext,
)


@tool
async def get_launchpad_logs_tool(
    launchpad_name: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Get logs for an app launchpad instance.

    This tool should be invoked strictly for resources of kind 'deployment' and 'statefulset'.
    When referring to resources, always refer to launchpad as 'app launchpad'.

    Args:
        launchpad_name: Name of the app launchpad to get logs for

    Returns:
        Dict containing the logs information

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    context = extract_sealos_context(state, LaunchpadContext)

    # Convert to brain context
    brain_context = BrainLaunchpadContext(kubeconfig=context.kubeconfig)

    try:
        # Call the brain API function
        result = get_launchpad_logs(brain_context, launchpad_name)

        return {
            "action": "get_launchpad_logs",
            "payload": {
                "launchpad_name": launchpad_name,
            },
            "success": True,
            "result": result,
            "message": f"Successfully retrieved logs for launchpad '{launchpad_name}'",
        }
    except Exception as e:
        return {
            "action": "get_launchpad_logs",
            "payload": {
                "launchpad_name": launchpad_name,
            },
            "success": False,
            "error": str(e),
            "message": f"Failed to get logs for launchpad '{launchpad_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the get launchpad logs tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.launchpad.get_launchpad_logs_tool

    import asyncio

    async def test_get_launchpad_logs():
        print("Testing get_launchpad_logs_tool...")
        try:
            # Mock state for testing
            mock_state = {
                "kubeconfig": "test-kubeconfig",
            }

            result = await get_launchpad_logs_tool.ainvoke(
                {"launchpad_name": "test-launchpad", "state": mock_state}
            )
            print("✅ Get launchpad logs tool test successful!")
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ Get launchpad logs tool test failed: {e}")

        print(f"Tool name: {get_launchpad_logs_tool.name}")
        print(f"Tool description: {get_launchpad_logs_tool.description}")

    asyncio.run(test_get_launchpad_logs())
