"""
Image deployment proposal tool for deploy project operations.
Proposes deployment of Docker images with specified ports.
"""

from langchain_core.tools import tool
from typing import List, Optional, Dict, Any
import asyncio


@tool
async def propose_image_deployment(
    image_name: str,
    project_name: str,
    name: str,
    ports: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Propose deployment of a Docker image with specified ports. Need to be reviewed and confirmed by the user.

    IMPORTANT: When calling this tool, make sure to add random characters
    to the end of all resource names to avoid name collisions with existing
    resources. For example, if you want to create a project called "my-project",
    append something like "my-project-abc123" or "my-project-xyz789" to make it unique.
    This applies to project names and application names.

    CRITICAL DEPLOYMENT BEHAVIOR: After using this tool to propose an image deployment,
    DO NOT suggest adding additional resources (databases, devboxes, etc.) as image
    deployments are fixed configurations that cannot be expanded. Only suggest
    deployment-related refinements if needed.

    Args:
        image_name (str): Docker image name (e.g., nginx:latest, node:18-alpine)
        project_name (str): Name of the project for this image deployment (add random characters to avoid collisions)
        name (str): Name of the application/container instance (add random characters to avoid collisions)
        ports (Optional[List[int]]): List of port numbers to expose for access

    Returns:
        Dict containing the action and payload for image deployment
    """
    return {
        "action": "propose_image_deployment",
        "payload": {
            "image_name": image_name,
            "project_name": project_name,
            "name": name,
            "ports": ports,
        },
    }


if __name__ == "__main__":
    # Test the image deployment proposal tool
    # Run with: python -m src.graph.orca.tools.deploy_project_tool.propose_image_deployment

    async def test_image_deployment():
        print("Testing propose_image_deployment...")
        try:
            # Test with ports
            result1 = await propose_image_deployment.ainvoke(
                {
                    "image_name": "nginx:latest",
                    "project_name": "web-project",
                    "name": "nginx-app",
                    "ports": [80, 443],
                }
            )
            print("✅ Image deployment proposal (with ports) successful!")
            print(f"Result: {result1}")

            # Test without ports
            result2 = await propose_image_deployment.ainvoke(
                {
                    "image_name": "node:18-alpine",
                    "project_name": "api-project",
                    "name": "node-app",
                }
            )
            print("✅ Image deployment proposal (without ports) successful!")
            print(f"Result: {result2}")

            # Test with single port
            result3 = await propose_image_deployment.ainvoke(
                {
                    "image_name": "myapp:latest",
                    "project_name": "custom-project",
                    "name": "my-app",
                    "ports": [8080],
                }
            )
            print("✅ Image deployment proposal (single port) successful!")
            print(f"Result: {result3}")

        except Exception as e:
            print(f"❌ Image deployment proposal failed: {e}")

        print(f"Tool name: {propose_image_deployment.name}")
        print(f"Tool description: {propose_image_deployment.description}")

    asyncio.run(test_image_deployment())
