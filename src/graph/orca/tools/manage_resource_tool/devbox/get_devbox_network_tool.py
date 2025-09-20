"""
Get devbox network tool for the manage resource agent.
Handles devbox network status retrieval with state management.
"""

from typing import Dict, Any
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from src.utils.sealos.extract_context import extract_sealos_context
from src.models.sealos.devbox.devbox_model import DevboxContext
from src.lib.brain.sealos.devbox.network import check_devbox_network, BrainDevboxContext


@tool
async def get_devbox_network_tool(
    devbox_name: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Get network status for a devbox instance.

    This tool should be invoked strictly for resources of kind 'devbox'.
    When referring to resources, always refer to devbox as 'devbox'.

    Args:
        devbox_name: Name of the devbox to get network status for

    Returns:
        Dict containing the network status information

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    context = extract_sealos_context(state, DevboxContext)

    # Convert to brain context
    brain_context = BrainDevboxContext(kubeconfig=context.kubeconfig)

    try:
        # Call the brain API function
        result = check_devbox_network(brain_context, devbox_name)

        return {
            "action": "get_devbox_network",
            "payload": {
                "devbox_name": devbox_name,
            },
            "success": True,
            "result": result,
            "message": f"Successfully retrieved network status for devbox '{devbox_name}'",
        }
    except Exception as e:
        return {
            "action": "get_devbox_network",
            "payload": {
                "devbox_name": devbox_name,
            },
            "success": False,
            "error": str(e),
            "message": f"Failed to get network status for devbox '{devbox_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the get devbox network tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.devbox.get_devbox_network_tool

    import asyncio

    async def test_get_devbox_network():
        print("Testing get_devbox_network_tool...")
        try:
            # Mock state for testing
            mock_state = {
                "kubeconfig": "test-kubeconfig",
            }

            result = await get_devbox_network_tool.ainvoke(
                {"devbox_name": "test-devbox", "state": mock_state}
            )
            print("✅ Get devbox network tool test successful!")
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ Get devbox network tool test failed: {e}")

        print(f"Tool name: {get_devbox_network_tool.name}")
        print(f"Tool description: {get_devbox_network_tool.description}")

    asyncio.run(test_get_devbox_network())
