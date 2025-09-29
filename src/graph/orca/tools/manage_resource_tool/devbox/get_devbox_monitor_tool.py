"""
Get devbox monitor tool for the manage resource agent.
Handles devbox monitoring data retrieval with state management.
"""

from typing import Dict, Any
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from src.utils.sealos.extract_context import extract_sealos_context
from src.models.sealos.devbox.devbox_model import DevboxContext
from src.lib.brain.sealos.devbox.monitor import get_devbox_monitor, BrainDevboxContext


@tool
async def get_devbox_monitor_tool(
    devbox_name: str,
    state: Annotated[dict, InjectedState],
    step: str = "2m",
) -> Dict[str, Any]:
    """
    Get monitoring data for a devbox instance.

    This tool should be invoked strictly for resources of kind 'devbox'.
    When referring to resources, always refer to devbox as 'devbox'.

    Args:
        devbox_name: Name of the devbox to get monitoring data for
        step: Monitoring step interval (default: "2m")

    Returns:
        Dict containing the monitoring data

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """

    context = extract_sealos_context(state, DevboxContext)

    # Convert to brain context
    brain_context = BrainDevboxContext(kubeconfig=context.kubeconfig)

    try:
        # Call the brain API function
        result = get_devbox_monitor(brain_context, devbox_name, step)

        return {
            "action": "get_devbox_monitor",
            "payload": {
                "devbox_name": devbox_name,
                "step": step,
            },
            "success": True,
            "result": result,
            "message": f"Successfully retrieved monitoring data for devbox '{devbox_name}'",
        }
    except Exception as e:
        return {
            "action": "get_devbox_monitor",
            "payload": {
                "devbox_name": devbox_name,
                "step": step,
            },
            "success": False,
            "error": str(e),
            "message": f"Failed to get monitoring data for devbox '{devbox_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the get devbox monitor tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.devbox.get_devbox_monitor_tool

    import asyncio

    async def test_get_devbox_monitor():
        import os
        from dotenv import load_dotenv

        load_dotenv()

        print("Testing get_devbox_monitor_tool...")
        try:
            # Get kubeconfig from environment
            kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
            mock_state = {
                "kubeconfig": kubeconfig,
            }

            result = await get_devbox_monitor_tool.ainvoke(
                {"devbox_name": "test-devbox", "step": "2m", "state": mock_state}
            )
            print("✅ Get devbox monitor tool test successful!")
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ Get devbox monitor tool test failed: {e}")

        print(f"Tool name: {get_devbox_monitor_tool.name}")
        print(f"Tool description: {get_devbox_monitor_tool.description}")

    asyncio.run(test_get_devbox_monitor())
