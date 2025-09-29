"""
Template deployment proposal tool for deploy project operations.
Proposes deployment of templates from the App Store.
"""

from langchain_core.tools import tool
from typing import Dict, Any
import asyncio


@tool
async def propose_template_deployment(
    template_name: str, project_name: str
) -> Dict[str, Any]:
    """
    Propose deployment of a template from the App Store. Need to be reviewed and confirmed by the user.

    IMPORTANT: When calling this tool, make sure to add random characters
    to the end of the project name to avoid name collisions with existing
    projects. For example, if you want to create a project called "my-project",
    append something like "my-project-abc123" or "my-project-xyz789" to make it unique.

    Args:
        template_name (str): Name of the template to deploy from the App Store
        project_name (str): Name of the project for this template deployment (add random characters to avoid collisions)

    Returns:
        Dict containing the action and payload for template deployment
    """
    return {
        "action": "propose_template_deployment",
        "payload": {
            "template_name": template_name,
            "project_name": project_name,
        },
    }


if __name__ == "__main__":
    # Test the template deployment proposal tool
    # Run with: python -m src.graph.orca.tools.deploy_project_tool.propose_template_deployment

    async def test_template_deployment():
        print("Testing propose_template_deployment...")
        try:
            result = await propose_template_deployment.ainvoke(
                {"template_name": "nginx-template", "project_name": "test-project"}
            )
            print("✅ Template deployment proposal successful!")
            print(f"Result: {result}")
        except Exception as e:
            print(f"❌ Template deployment proposal failed: {e}")

        print(f"Tool name: {propose_template_deployment.name}")
        print(f"Tool description: {propose_template_deployment.description}")

    asyncio.run(test_template_deployment())
