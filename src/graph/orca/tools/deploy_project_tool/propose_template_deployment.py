"""
Template deployment proposal tool for deploy project operations.
Proposes deployment of templates from the App Store.
"""

from langchain_core.tools import tool
from typing import Dict, Any
import asyncio


@tool
async def propose_template_deployment(template_name: str) -> Dict[str, Any]:
    """
    Propose deployment of a template from the App Store. Need to be reviewed and confirmed by the user.

    Args:
        template_name (str): Name of the template to deploy from the App Store

    Returns:
        Dict containing the action and payload for template deployment
    """
    return {
        "action": "propose_template_deployment",
        "payload": {
            "template_name": template_name,
        },
    }


if __name__ == "__main__":
    # Test the template deployment proposal tool
    # Run with: python -m src.graph.orca.tools.deploy_project_tool.propose_template_deployment

    async def test_template_deployment():
        print("Testing propose_template_deployment...")
        try:
            result = await propose_template_deployment.ainvoke(
                {"template_name": "nginx-template"}
            )
            print("✅ Template deployment proposal successful!")
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ Template deployment proposal failed: {e}")

        print(f"Tool name: {propose_template_deployment.name}")
        print(f"Tool description: {propose_template_deployment.description}")

    asyncio.run(test_template_deployment())
