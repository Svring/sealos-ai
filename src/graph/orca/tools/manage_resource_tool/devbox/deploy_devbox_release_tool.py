"""
Deploy devbox release tool for the manage resource agent.
Handles devbox release deployment with state management.
"""

from typing import Dict, Any
from typing_extensions import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState


@tool
async def deploy_devbox_release_tool(
    devbox_name: str,
    release_tag: str,
    state: Annotated[dict, InjectedState],
) -> Dict[str, Any]:
    """
    Display UI for deploying a release to Sealos.
    In the UI, the user could choose to update an existing deployment (deployed by previous release and could be updated to a new release)
    or creating a new deployment from a release, thus deploy_devbox_release_tool requires a tag as parameter.

    This tool should be invoked strictly for resources of kind 'devbox'.
    When referring to resources, always refer to devbox as 'devbox'.

    Args:
        devbox_name: Name of the devbox to deploy release for
        release_tag: Tag/version of the release to deploy

    Returns:
        Dict containing the devbox release deployment UI and result
    """
    # Prepare payload for response
    payload = {
        "devbox_name": devbox_name,
        "release_tag": release_tag,
    }

    return {
        "action": "deploy_devbox_release",
        "payload": payload,
        "success": True,
        "result": payload,
        "message": f"Successfully deployed release '{release_tag}' for devbox '{devbox_name}'",
    }


if __name__ == "__main__":
    # Test the deploy devbox release tool
    # Run with: python -m src.graph.orca.tools.manage_resource_tool.devbox.deploy_devbox_release_tool

    import asyncio

    async def test_deploy_devbox_release():
        import os
        from dotenv import load_dotenv

        load_dotenv()

        print("Testing deploy_devbox_release_tool...")
        try:
            # Get kubeconfig from environment
            kubeconfig = os.getenv("BJA_KC", "test-kubeconfig")
            mock_state = {
                "kubeconfig": kubeconfig,
            }

            result = await deploy_devbox_release_tool.ainvoke(
                {
                    "devbox_name": "test-devbox",
                    "release_tag": "v1.0.0",
                    "state": mock_state,
                }
            )
            print("✅ Deploy devbox release tool test successful!")
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ Deploy devbox release tool test failed: {e}")

        print(f"Tool name: {deploy_devbox_release_tool.name}")
        print(f"Tool description: {deploy_devbox_release_tool.description}")

    asyncio.run(test_deploy_devbox_release())
