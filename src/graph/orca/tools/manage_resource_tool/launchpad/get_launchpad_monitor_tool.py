"""
Get launchpad monitor tool for the manage resource agent.
Handles launchpad monitoring data retrieval with state management.
"""

from typing import Dict, Any
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
from src.lib.brain.sealos.launchpad.monitor import (
    get_launchpad_monitor,
    BrainLaunchpadContext,
)


@tool
async def get_launchpad_monitor_tool(
    launchpad_name: str,
    state: Annotated[dict, InjectedState],
    step: str = "2m",
) -> Dict[str, Any]:
    """
    Get monitoring data for an app launchpad instance.

    This tool should be invoked strictly for resources of kind 'deployment' and 'statefulset'.
    When referring to resources, always refer to launchpad as 'app launchpad'.

    Args:
        launchpad_name: Name of the app launchpad to get monitoring data for
        step: Monitoring step interval (default: "2m")

    Returns:
        Dict containing the monitoring data

    Raises:
        ValueError: If required state values are missing
        requests.RequestException: If the API request fails
    """
    # Handle interrupt with approval and parameter editing
    is_approved, edited_data, response_payload = handle_interrupt_with_approval(
        action="get_launchpad_monitor",
        payload={
            "launchpad_name": launchpad_name,
            "step": step,
        },
        interrupt_func=interrupt,
        original_params={
            "launchpad_name": launchpad_name,
            "step": step,
        },
    )

    # Check if the operation was approved
    if not is_approved:
        return create_rejection_response(
            action="get_launchpad_monitor",
            response_payload=response_payload,
            resource_name="app launchpad",
            operation_type="Get Monitor",
        )

    # Extract the edited parameters
    launchpad_name = edited_data.get("launchpad_name", launchpad_name)
    step = edited_data.get("step", step)

    context = extract_sealos_context(state, LaunchpadContext)

    # Convert to brain context
    brain_context = BrainLaunchpadContext(kubeconfig=context.kubeconfig)

    try:
        # Call the brain API function
        result = get_launchpad_monitor(brain_context, launchpad_name, step)

        return {
            "action": "get_launchpad_monitor",
            "payload": edited_data,
            "success": True,
            "result": result,
            "message": f"Successfully retrieved monitoring data for launchpad '{launchpad_name}'",
        }
    except Exception as e:
        return {
            "action": "get_launchpad_monitor",
            "payload": edited_data,
            "success": False,
            "error": str(e),
            "message": f"Failed to get monitoring data for launchpad '{launchpad_name}': {str(e)}",
        }


if __name__ == "__main__":
    # Test the get launchpad monitor tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.launchpad.get_launchpad_monitor_tool

    import asyncio

    async def test_get_launchpad_monitor():
        import os
        from dotenv import load_dotenv

        load_dotenv()

        print("Testing get_launchpad_monitor_tool...")
        try:
            # Get kubeconfig from environment
            kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
            mock_state = {
                "kubeconfig": kubeconfig,
            }

            result = await get_launchpad_monitor_tool.ainvoke(
                {
                    "launchpad_name": "test-launchpad",
                    "step": "2m",
                    "state": mock_state,
                }
            )
            print("✅ Get launchpad monitor tool test successful!")
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ Get launchpad monitor tool test failed: {e}")

        print(f"Tool name: {get_launchpad_monitor_tool.name}")
        print(f"Tool description: {get_launchpad_monitor_tool.description}")

    asyncio.run(test_get_launchpad_monitor())
