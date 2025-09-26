"""
Get devbox release tool for the manage resource agent.
Handles devbox release status retrieval with state management.
"""

from typing import Dict, Any
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState


@tool
async def get_devbox_release_tool(
    devbox_name: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Display releases of a certain devbox when user asks for viewing releases or wants to release the current devbox.
    This tool displays a panel to allow user viewing and managing their devbox releases.

    A release (or "发版" in Chinese) is a snapshot of a devbox at a certain time point which could be deployed to Sealos to function.
    It's a key component for converting a devbox development environment to a functional deployment.

    User still needs to manage their releases manually when the model has called this tool, thus the model should specify this like
    'you could release your devbox by specifying a unique release tag'.

    If user asks for the model to release devbox with a certain tag, it should gently reject and still show the release UI
    (which is created by calling get_devbox_release_tool) to advise the user to do it manually.

    This tool should be invoked strictly for resources of kind 'devbox'.
    When referring to resources, always refer to devbox as 'devbox'.

    Args:
        devbox_name: Name of the devbox to get release status for

    Returns:
        Dict containing the devbox release status and UI for release management
    """
    # Prepare payload for response
    payload = {
        "devbox_name": devbox_name,
    }

    return {
        "action": "get_devbox_release",
        "payload": payload,
        "success": True,
        "result": payload,
        "message": f"Successfully retrieved release status for devbox '{devbox_name}'",
    }


if __name__ == "__main__":
    # Test the get devbox release tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.devbox.get_devbox_release_tool

    import asyncio

    async def test_get_devbox_release():
        import os
        from dotenv import load_dotenv

        load_dotenv()

        print("Testing get_devbox_release_tool...")
        try:
            # Get kubeconfig from environment
            kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
            mock_state = {
                "kubeconfig": kubeconfig,
            }

            result = await get_devbox_release_tool.ainvoke(
                {"devbox_name": "test-devbox", "state": mock_state}
            )
            print("✅ Get devbox release tool test successful!")
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ Get devbox release tool test failed: {e}")

        print(f"Tool name: {get_devbox_release_tool.name}")
        print(f"Tool description: {get_devbox_release_tool.description}")

    asyncio.run(test_get_devbox_release())
