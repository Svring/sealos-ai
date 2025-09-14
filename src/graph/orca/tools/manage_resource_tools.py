"""
Tools for the manage resource agent.
Contains tools for managing individual resource configurations and lifecycle.
"""

from typing import Optional, Dict, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class ResourceConfig(BaseModel):
    """Basic resource configuration."""

    cpu: float = Field(description="CPU allocation in cores")
    memory: float = Field(description="Memory allocation in GB")


class ClusterResourceConfig(BaseModel):
    """Extended resource configuration for database clusters."""

    replicas: int = Field(description="Number of replicas")
    cpu: float = Field(description="CPU allocation in cores")
    memory: float = Field(description="Memory allocation in GB")
    storage: Optional[float] = Field(
        default=None, description="Storage allocation in GB"
    )


class LaunchpadResourceConfig(BaseModel):
    """Extended resource configuration for launchpads."""

    replicas: Optional[int] = Field(default=None, description="Number of replicas")
    cpu: Optional[float] = Field(default=None, description="CPU allocation in cores")
    memory: Optional[float] = Field(default=None, description="Memory allocation in GB")
    hpa: Optional[str] = Field(
        default=None, description="Horizontal Pod Autoscaler configuration"
    )


@tool
async def updateDevbox(
    devboxName: str, resource: Optional[ResourceConfig] = None
) -> Dict[str, Any]:
    """
    Update a devbox configuration (resource, ports, etc.).

    Args:
        devboxName: Name of the devbox to update
        resource: Updated resource allocation (CPU and memory)

    Returns:
        Dict containing the update operation result
    """
    return {
        "action": "updateDevbox",
        "payload": {
            "devboxName": devboxName,
            "resource": resource.model_dump() if resource else None,
        },
    }


@tool
async def devboxLifecycle(devboxName: str, action: str) -> Dict[str, Any]:
    """
    Manage devbox lifecycle (start, pause, restart, shutdown, delete).

    Args:
        devboxName: Name of the devbox
        action: Lifecycle action to perform (start, pause, restart, shutdown, delete)

    Returns:
        Dict containing the lifecycle operation result
    """
    return {
        "action": "devboxLifecycle",
        "payload": {
            "devboxName": devboxName,
            "lifecycleAction": action,
        },
    }


@tool
async def releaseDevbox(
    devboxName: str, tag: str, releaseDes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Release a devbox with a specific tag.

    Args:
        devboxName: Name of the devbox to release
        tag: Release tag for the devbox
        releaseDes: Optional description for the release

    Returns:
        Dict containing the release operation result
    """
    return {
        "action": "releaseDevbox",
        "payload": {
            "devboxName": devboxName,
            "tag": tag,
            "releaseDes": releaseDes,
        },
    }


@tool
async def deployDevbox(devboxName: str, tag: str) -> Dict[str, Any]:
    """
    Deploy a devbox release with fixed resource configuration (2 CPU cores, 2GB memory).

    Args:
        devboxName: Name of the devbox to deploy
        tag: Devbox release version tag to deploy

    Returns:
        Dict containing the deployment operation result
    """
    return {
        "action": "deployDevbox",
        "payload": {
            "devboxName": devboxName,
            "tag": tag,
        },
    }


@tool
async def updateCluster(
    clusterName: str, resource: Optional[ClusterResourceConfig] = None
) -> Dict[str, Any]:
    """
    Update a cluster configuration (resource, etc.).

    Args:
        clusterName: Name of the cluster to update
        resource: Updated resource allocation (replicas, CPU, memory, storage)

    Returns:
        Dict containing the update operation result
    """
    return {
        "action": "updateCluster",
        "payload": {
            "clusterName": clusterName,
            "resource": resource.model_dump() if resource else None,
        },
    }


@tool
async def clusterLifecycle(clusterName: str, action: str) -> Dict[str, Any]:
    """
    Manage cluster lifecycle (start, pause).

    Args:
        clusterName: Name of the cluster
        action: Lifecycle action to perform (start, pause)

    Returns:
        Dict containing the lifecycle operation result
    """
    return {
        "action": "clusterLifecycle",
        "payload": {
            "clusterName": clusterName,
            "lifecycleAction": action,
        },
    }


@tool
async def updateLaunchpad(
    launchpadName: str, resource: Optional[LaunchpadResourceConfig] = None
) -> Dict[str, Any]:
    """
    Update a launchpad configuration (resource, ports, etc.).

    Args:
        launchpadName: Name of the launchpad to update
        resource: Updated resource allocation (replicas, CPU, memory, HPA)

    Returns:
        Dict containing the update operation result
    """
    return {
        "action": "updateLaunchpad",
        "payload": {
            "launchpadName": launchpadName,
            "resource": resource.model_dump() if resource else None,
        },
    }


@tool
async def launchpadLifecycle(launchpadName: str, action: str) -> Dict[str, Any]:
    """
    Manage launchpad lifecycle (start, pause, delete).

    Args:
        launchpadName: Name of the launchpad
        action: Lifecycle action to perform (start, pause, delete)

    Returns:
        Dict containing the lifecycle operation result
    """
    return {
        "action": "launchpadLifecycle",
        "payload": {
            "launchpadName": launchpadName,
            "lifecycleAction": action,
        },
    }
