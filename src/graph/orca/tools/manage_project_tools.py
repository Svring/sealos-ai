"""
Tools for the manage project agent.
Contains tools for creating and managing project-level resources.
"""

from typing import List, Optional, Dict, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class DevboxPort(BaseModel):
    """Port configuration for DevBox."""

    number: int = Field(description="Port number (1-65535)")
    publicAccess: bool = Field(
        description="Whether the port should be publicly accessible"
    )


class DevboxResource(BaseModel):
    """DevBox resource configuration."""

    name: str = Field(
        description="Devbox name (lowercase, numbers, underscores, hyphens only, max 24 chars)"
    )
    runtime: str = Field(
        description="Devbox runtime",
        enum=[
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
            "sealaf",
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
        ],
    )
    ports: Optional[List[DevboxPort]] = Field(
        default=None, description="Array of ports to expose"
    )


class DatabaseResource(BaseModel):
    """Database resource configuration."""

    name: str = Field(
        description="Database name (lowercase, numbers, underscores, hyphens only, max 24 chars)"
    )
    type: str = Field(
        description="Database type",
        enum=["postgresql", "mysql", "redis", "mongodb", "elasticsearch"],
    )


class BucketResource(BaseModel):
    """Object storage bucket resource configuration."""

    name: str = Field(
        description="Bucket name (lowercase, numbers, underscores, hyphens only, max 24 chars)"
    )
    policy: str = Field(
        description="Bucket access policy",
        enum=["private", "publicRead", "publicReadWrite"],
    )


class AppPort(BaseModel):
    """Port configuration for App."""

    number: int = Field(description="Port number (1-65535)")
    publicAccess: bool = Field(
        description="Whether the port should be publicly accessible"
    )


class AppEnv(BaseModel):
    """Environment variable configuration for App."""

    name: str = Field(description="Environment variable name")
    value: str = Field(description="Environment variable value")


class AppResource(BaseModel):
    """App resource configuration."""

    name: str = Field(
        description="App name (lowercase, numbers, underscores, hyphens only, max 24 chars)"
    )
    image: str = Field(description="Docker image for the app (e.g., nginx:latest)")
    ports: Optional[List[AppPort]] = Field(
        default=None, description="Array of ports to expose"
    )
    env: Optional[List[AppEnv]] = Field(
        default=None, description="Array of environment variables"
    )


@tool
async def add_resource_to_project(
    devbox: Optional[List[DevboxResource]] = None,
    database: Optional[List[DatabaseResource]] = None,
    bucket: Optional[List[BucketResource]] = None,
    app: Optional[List[AppResource]] = None,
) -> Dict[str, Any]:
    """
    Add resources (devbox, database, bucket, app) to the currently selected project.

    Args:
        devbox: Array of devbox resources to add
        database: Array of database resources to add
        bucket: Array of object storage bucket resources to add
        app: Array of app resources to add

    Returns:
        Dict containing the action and payload with all resources to add
    """
    return {
        "action": "add_resource_to_project",
        "payload": {
            "devbox": (
                [devbox_item.model_dump() for devbox_item in devbox] if devbox else None
            ),
            "database": (
                [db_item.model_dump() for db_item in database] if database else None
            ),
            "bucket": (
                [bucket_item.model_dump() for bucket_item in bucket] if bucket else None
            ),
            "app": [app_item.model_dump() for app_item in app] if app else None,
        },
    }
