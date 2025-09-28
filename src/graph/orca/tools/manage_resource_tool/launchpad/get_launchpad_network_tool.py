"""
Get launchpad network tool for the manage resource agent.
Handles launchpad network status retrieval with state management.
"""

from typing import Dict, Any
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from src.utils.sealos.extract_context import extract_sealos_context
from src.models.sealos.launchpad.launchpad_model import LaunchpadContext
from src.lib.brain.sealos.launchpad.network import (
    check_launchpad_network,
    BrainLaunchpadContext,
)


@tool
async def get_launchpad_network_tool(
    launchpad_name: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Get network status for an app launchpad instance.

    This tool should be invoked strictly for resources of kind 'deployment' and 'statefulset'.
    When referring to resources, always refer to launchpad as 'app launchpad'.

    Args:
        launchpad_name: Name of the app launchpad to get network status for

    Returns:
        Dict containing the network status information

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Prepare payload for response
    payload = {
        "launchpad_name": launchpad_name,
    }

    context = extract_sealos_context(state, LaunchpadContext)

    # Convert to brain context
    brain_context = BrainLaunchpadContext(kubeconfig=context.kubeconfig)

    try:
        # Call the brain API function
        result = check_launchpad_network(brain_context, launchpad_name)

        return {
            "action": "get_launchpad_network",
            "payload": payload,
            "success": True,
            "result": result,
            "message": f"Successfully retrieved network status for launchpad '{launchpad_name}'",
        }
    except Exception as e:
        return {
            "action": "get_launchpad_network",
            "payload": payload,
            "success": False,
            "error": str(e),
            "message": f"Failed to get network status for launchpad '{launchpad_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the get launchpad network tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.launchpad.get_launchpad_network_tool

    import asyncio

    async def test_get_launchpad_network():
        import os
        from dotenv import load_dotenv

        load_dotenv()

        print("Testing get_launchpad_network_tool...")
        try:
            # Get kubeconfig from environment
            kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
            mock_state = {
                "kubeconfig": kubeconfig,
            }

            result = await get_launchpad_network_tool.ainvoke(
                {"launchpad_name": "test-launchpad", "state": mock_state}
            )
            print("✅ Get launchpad network tool test successful!")
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ Get launchpad network tool test failed: {e}")

        print(f"Tool name: {get_launchpad_network_tool.name}")
        print(f"Tool description: {get_launchpad_network_tool.description}")

    asyncio.run(test_get_launchpad_network())
