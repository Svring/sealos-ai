"""
Development environment deployment proposal tool for deploy project operations.
Proposes deployment of development environments with DevBox and Database.
"""

from langchain_core.tools import tool
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator
import re


class DeployDevBox(BaseModel):
    """Simplified DevBox configuration for deployment."""

    name: str = Field(
        ...,
        max_length=30,
        description="DevBox name (max 30 chars, lowercase letters, numbers, hyphens only). Examples: 'dev-env', 'frontend_dev', 'api-dev'",
    )
    runtime: Literal[
        "nuxt3",
        "angular",
        "quarkus",
        "ubuntu",
        "flask",
        "java",
        "chi",
        "net",
        "iris",
        "hexo",
        "python",
        "docusaurus",
        "vitepress",
        "cpp",
        "vue",
        "nginx",
        "rocket",
        "debian-ssh",
        "vert.x",
        "express.js",
        "django",
        "next.js",
        "go",
        "react",
        "php",
        "svelte",
        "c",
        "astro",
        "umi",
        "gin",
        "echo",
        "rust",
        "mcp",
        "hugo",
        "spring-boot",
        "node.js",
    ] = Field(
        description="The runtime environment for development (e.g., 'Next.js', 'Python', 'React')"
    )
    ports: Optional[List[int]] = Field(
        default=None,
        description="Optional list of port numbers to expose for the development environment",
    )
    reliance: Optional[List[str]] = Field(
        default=None,
        description="Optional list of database names that this DevBox should connect to. These databases must be defined in the same deployment proposal.",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "DevBox name must contain only lowercase letters, numbers, and hyphens. "
                "Examples: 'dev-env', 'frontend_dev', 'api-dev'. "
                f"Invalid name: '{v}'"
            )
        return v


class DeployDatabase(BaseModel):
    """Database configuration for deployment."""

    name: str = Field(
        ...,
        max_length=30,
        description="Database name (max 30 chars, lowercase letters, numbers, hyphens only). Examples: 'main-db', 'cache-db', 'analytics'",
    )
    type: Literal[
        "postgresql",
        "mongodb",
        "apecloud-mysql",
        "redis",
        "kafka",
        "milvus",
    ] = Field(
        description="The type of database (e.g., 'postgresql', 'mongodb', 'redis')"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "Database name must contain only lowercase letters, numbers, and hyphens. "
                "Examples: 'main-db', 'cache-db', 'analytics'. "
                f"Invalid name: '{v}'"
            )
        return v


@tool
async def propose_devenv_deployment(
    project_name: str,
    devbox: Optional[List[DeployDevBox]] = None,
    database: Optional[List[DeployDatabase]] = None,
) -> Dict[str, Any]:
    """
    Propose deployment of a development environment with one or more DevBox instances and/or databases. Need to be reviewed and confirmed by the user.

    IMPORTANT: When calling this tool, make sure to add random characters
    to the end of all resource names to avoid name collisions with existing
    resources. For example, if you want to create a project called "my-project",
    append something like "my-project-abc123" or "my-project-xyz789" to make it unique.
    This applies to project names, DevBox names, and Database names.

    Args:
        project_name (str): Name of the project for this development environment deployment (add random characters to avoid collisions).
        devbox (Optional[List[DeployDevBox]]): List of DevBox configurations for development environments. Can deploy multiple DevBox instances.
        database (Optional[List[DeployDatabase]]): List of database configurations for the development environment. Can deploy multiple databases.

    Returns:
        Dict containing the action and payload for development environment deployment
    """
    return {
        "action": "propose_devenv_deployment",
        "payload": {
            "project_name": project_name,
            "devbox": [item.model_dump() for item in devbox] if devbox else None,
            "database": [item.model_dump() for item in database] if database else None,
        },
    }


if __name__ == "__main__":
    # Test the development environment deployment proposal tool
    # Run with: python -m src.graph.orca.tools.deploy_project_tool.propose_devenv_deployment

    import asyncio

    async def test_devenv_deployment():
        print("Testing propose_devenv_deployment...")
        try:
            # Test with both devbox and database
            devbox = [
                DeployDevBox(
                    name="test-dev",
                    runtime="next.js",
                    ports=[3000, 8080],
                    reliance=["test-db"],
                )
            ]
            database = [DeployDatabase(name="test-db", type="postgresql")]

            result1 = await propose_devenv_deployment.ainvoke(
                {"project_name": "test-project", "devbox": devbox, "database": database}
            )
            print("✅ DevEnv deployment proposal (both) successful!")
            print(f"Result: {result1}")

            # Test with only devbox
            result2 = await propose_devenv_deployment.ainvoke(
                {
                    "project_name": "frontend-project",
                    "devbox": [
                        DeployDevBox(name="frontend", runtime="react", ports=[3000])
                    ],
                }
            )
            print("✅ DevEnv deployment proposal (devbox only) successful!")
            print(f"Result: {result2}")

            # Test with only database
            result3 = await propose_devenv_deployment.ainvoke(
                {
                    "project_name": "database-project",
                    "database": [DeployDatabase(name="cache-db", type="redis")],
                }
            )
            print("✅ DevEnv deployment proposal (database only) successful!")
            print(f"Result: {result3}")

            # Test with multiple devboxes and databases
            multiple_devboxes = [
                DeployDevBox(
                    name="frontend-dev",
                    runtime="react",
                    ports=[3000],
                    reliance=["main-db"],
                ),
                DeployDevBox(
                    name="backend-dev",
                    runtime="python",
                    ports=[8000],
                    reliance=["main-db", "cache-db"],
                ),
            ]
            multiple_databases = [
                DeployDatabase(name="main-db", type="postgresql"),
                DeployDatabase(name="cache-db", type="redis"),
            ]
            result4 = await propose_devenv_deployment.ainvoke(
                {
                    "project_name": "multi-resource-project",
                    "devbox": multiple_devboxes,
                    "database": multiple_databases,
                }
            )
            print("✅ DevEnv deployment proposal (multiple resources) successful!")
            print(f"Result: {result4}")

        except Exception as e:
            print(f"❌ DevEnv deployment proposal failed: {e}")

        print(f"Tool name: {propose_devenv_deployment.name}")
        print(f"Tool description: {propose_devenv_deployment.description}")

        # Test model validation
        print("\nTesting model validation...")
        try:
            # Test valid models
            valid_devbox = DeployDevBox(
                name="valid-dev", runtime="python", ports=[8000], reliance=["valid-db"]
            )
            valid_database = DeployDatabase(name="valid-db", type="mongodb")
            print("✅ Model validation successful!")
            print(
                f"Valid DevBox: {valid_devbox.name} ({valid_devbox.runtime}) with reliance: {valid_devbox.reliance}"
            )
            print(f"Valid Database: {valid_database.name} ({valid_database.type})")
        except Exception as e:
            print(f"❌ Model validation failed: {e}")

    asyncio.run(test_devenv_deployment())
