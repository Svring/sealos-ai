"""
Image deployment proposal tool for deploy project operations.
Proposes deployment of Docker images with specified ports.
"""

from langchain_core.tools import tool
from typing import List, Optional, Dict, Any
import asyncio


@tool
async def propose_image_deployment(
    image_name: str, ports: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Propose deployment of a Docker image with specified ports.

    Args:
        image_name (str): Docker image name (e.g., nginx:latest, node:18-alpine)
        ports (Optional[List[int]]): List of port numbers to expose for access

    Returns:
        Dict containing the action and payload for image deployment
    """
    return {
        "action": "propose_image_deployment",
        "payload": {
            "image_name": image_name,
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
                {"image_name": "nginx:latest", "ports": [80, 443]}
            )
            print("✅ Image deployment proposal (with ports) successful!")
            print(f"Result: {result1}")

            # Test without ports
            result2 = await propose_image_deployment.ainvoke(
                {"image_name": "node:18-alpine"}
            )
            print("✅ Image deployment proposal (without ports) successful!")
            print(f"Result: {result2}")
        except Exception as e:
            print(f"❌ Image deployment proposal failed: {e}")

        print(f"Tool name: {propose_image_deployment.name}")
        print(f"Tool description: {propose_image_deployment.description}")

    asyncio.run(test_image_deployment())
