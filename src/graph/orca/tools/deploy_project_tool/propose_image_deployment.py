"""
Image deployment proposal tool for deploy project operations.
Proposes deployment of Docker images with specified ports.
"""

from langchain_core.tools import tool
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
import re
import asyncio


class DeployDatabase(BaseModel):
    name: str = Field(..., max_length=12, description="Database name")
    type: Literal[
        "postgresql",
        "mongodb",
        "apecloud-mysql",
        "redis",
        "kafka",
        "weaviate",
        "milvus",
        "pulsar",
    ] = Field(description="The type of database")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "Database name must contain only lowercase letters, numbers, and hyphens."
            )
        return v


@tool
async def propose_image_deployment(
    image_name: str,
    ports: Optional[List[int]] = None,
    database: Optional[DeployDatabase] = None,
) -> Dict[str, Any]:
    """
    Propose deployment of a Docker image with specified ports and optional database. Need to be reviewed and confirmed by the user.

    Args:
        image_name (str): Docker image name (e.g., nginx:latest, node:18-alpine)
        ports (Optional[List[int]]): List of port numbers to expose for access
        database (Optional[DeployDatabase]): Database configuration for the deployment

    Returns:
        Dict containing the action and payload for image deployment
    """
    return {
        "action": "propose_image_deployment",
        "payload": {
            "image_name": image_name,
            "ports": ports,
            "database": database.model_dump() if database else None,
        },
    }


if __name__ == "__main__":
    # Test the image deployment proposal tool
    # Run with: python -m src.graph.orca.tools.deploy_project_tool.propose_image_deployment

    async def test_image_deployment():
        print("Testing propose_image_deployment...")
        try:
            # Test with ports only
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

            # Test with database
            database = DeployDatabase(name="app-db", type="postgresql")
            result3 = await propose_image_deployment.ainvoke(
                {"image_name": "myapp:latest", "ports": [8080], "database": database}
            )
            print("✅ Image deployment proposal (with database) successful!")
            print(f"Result: {result3}")

        except Exception as e:
            print(f"❌ Image deployment proposal failed: {e}")

        print(f"Tool name: {propose_image_deployment.name}")
        print(f"Tool description: {propose_image_deployment.description}")

        # Test model validation
        print("\nTesting model validation...")
        try:
            valid_database = DeployDatabase(name="test-db", type="mongodb")
            print("✅ Model validation successful!")
            print(f"Valid Database: {valid_database.name} ({valid_database.type})")
        except Exception as e:
            print(f"❌ Model validation failed: {e}")

    asyncio.run(test_image_deployment())
