"""
Tools for the manage project agent.
Contains tools for creating and managing project-level resources.
"""

from typing import List, Optional, Dict, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class DevboxResource(BaseModel):
    """Resource configuration for DevBox."""

    cpu: float = Field(description="CPU allocation in cores")
    memory: float = Field(description="Memory allocation in GB")


class DevboxPort(BaseModel):
    """Port configuration for DevBox."""

    portName: Optional[str] = Field(default=None, description="Name of the port")
    number: int = Field(description="Port number")
    protocol: Optional[str] = Field(
        default="HTTP", description="Protocol type", enum=["HTTP", "GRPC", "WS"]
    )
    exposesPublicDomain: Optional[bool] = Field(
        default=False, description="Whether port is publicly accessible"
    )
    customDomain: Optional[str] = Field(
        default=None, description="Custom domain for the port"
    )


class ClusterResource(BaseModel):
    """Resource configuration for Database Cluster."""

    replicas: int = Field(description="Number of replicas")
    cpu: float = Field(description="CPU allocation in cores")
    memory: float = Field(description="Memory allocation in GB")
    storage: Optional[float] = Field(
        default=None, description="Storage allocation in GB"
    )


class LaunchpadImage(BaseModel):
    """Image configuration for Launchpad."""

    imageName: Optional[str] = Field(
        default=None, description="Name of the Docker image"
    )
    imageRegistry: Optional[str] = Field(
        default=None, description="Registry URL for the image"
    )


class LaunchpadCommand(BaseModel):
    """Launch command configuration for Launchpad."""

    command: Optional[str] = Field(default=None, description="Command to run")
    args: Optional[str] = Field(default=None, description="Arguments for the command")


class LaunchpadResource(BaseModel):
    """Resource configuration for Launchpad."""

    replicas: Optional[int] = Field(default=1, description="Number of replicas")
    cpu: float = Field(description="CPU allocation in cores")
    memory: float = Field(description="Memory allocation in GB")
    hpa: Optional[str] = Field(
        default=None, description="Horizontal Pod Autoscaler configuration"
    )


class LaunchpadEnv(BaseModel):
    """Environment variable configuration for Launchpad."""

    name: str = Field(description="Environment variable name")
    value: Optional[str] = Field(default=None, description="Environment variable value")
    valueFrom: Optional[Dict[str, Any]] = Field(
        default=None, description="Value from secret or configmap"
    )


class LaunchpadStorage(BaseModel):
    """Storage configuration for Launchpad."""

    path: str = Field(description="Mount path for storage")
    size: Optional[str] = Field(
        default="1Gi", description="Storage size", enum=["1Gi", "5Gi", "10Gi", "20Gi"]
    )


class LaunchpadConfigMap(BaseModel):
    """ConfigMap configuration for Launchpad."""

    path: str = Field(description="Mount path for config")
    value: str = Field(description="Configuration content")


@tool
async def createDevbox(
    name: Optional[str] = None,
    runtime: Optional[str] = None,
    resource: Optional[DevboxResource] = None,
    ports: Optional[List[DevboxPort]] = None,
) -> Dict[str, Any]:
    """
    Create a new devbox with specified configuration.

    Args:
        name: Name of the devbox
        runtime: Runtime environment (e.g., python, next.js, react, etc.)
        resource: Resource allocation (CPU and memory)
        ports: List of ports to expose

    Returns:
        Dict containing the created devbox information
    """
    return {
        "action": "createDevbox",
        "payload": {
            "name": name,
            "runtime": runtime,
            "resource": resource.model_dump() if resource else None,
            "ports": [port.model_dump() for port in ports] if ports else None,
        },
    }


@tool
async def createCluster(
    name: Optional[str] = None,
    type: Optional[str] = None,
    version: Optional[str] = None,
    resource: Optional[ClusterResource] = None,
    terminationPolicy: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new database cluster with specified configuration.

    Args:
        name: Name of the database cluster
        type: Database type (e.g., postgresql, mongodb, redis)
        version: Database version
        resource: Resource allocation (replicas, CPU, memory, storage)
        terminationPolicy: Termination policy (Delete or WipeOut)

    Returns:
        Dict containing the created cluster information
    """
    return {
        "action": "createCluster",
        "payload": {
            "name": name,
            "type": type,
            "version": version,
            "resource": resource.model_dump() if resource else None,
            "terminationPolicy": terminationPolicy,
        },
    }


@tool
async def createLaunchpad(
    name: Optional[str] = None,
    image: Optional[LaunchpadImage] = None,
    launchCommand: Optional[LaunchpadCommand] = None,
    resource: Optional[LaunchpadResource] = None,
    ports: Optional[List[DevboxPort]] = None,
    env: Optional[List[LaunchpadEnv]] = None,
    storage: Optional[List[LaunchpadStorage]] = None,
    configMap: Optional[List[LaunchpadConfigMap]] = None,
) -> Dict[str, Any]:
    """
    Create a new launchpad with specified configuration.

    Args:
        name: Name of the launchpad
        image: Docker image configuration
        launchCommand: Launch command and arguments
        resource: Resource allocation (CPU, memory, replicas)
        ports: List of ports to expose
        env: List of environment variables
        storage: List of storage mounts
        configMap: List of config map mounts

    Returns:
        Dict containing the created launchpad information
    """
    return {
        "action": "createLaunchpad",
        "payload": {
            "name": name,
            "image": image.model_dump() if image else None,
            "launchCommand": launchCommand.model_dump() if launchCommand else None,
            "resource": resource.model_dump() if resource else None,
            "ports": [port.model_dump() for port in ports] if ports else None,
            "env": [env_var.model_dump() for env_var in env] if env else None,
            "storage": (
                [storage_item.model_dump() for storage_item in storage]
                if storage
                else None
            ),
            "configMap": (
                [config.model_dump() for config in configMap] if configMap else None
            ),
        },
    }


@tool
async def createObjectStorageBucket(
    name: Optional[str] = None, policy: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new object storage bucket with specified configuration.

    Args:
        name: Name of the storage bucket
        policy: Access policy (private, publicRead, publicReadwrite)

    Returns:
        Dict containing the created bucket information
    """
    return {
        "action": "createObjectStorageBucket",
        "payload": {
            "name": name,
            "policy": policy,
        },
    }
