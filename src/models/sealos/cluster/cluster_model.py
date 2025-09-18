"""
Cluster models with validation for the Sealos cluster operations.
"""

from typing import Dict, Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class ClusterResource(BaseModel):
    """Resource allocation for cluster with validation."""

    cpu: Optional[Literal[1, 2, 4, 8]] = Field(
        None, alias="cpu", description="CPU allocation in cores"
    )
    memory: Optional[Literal[1, 2, 4, 8, 16, 32]] = Field(
        None, alias="memory", description="Memory allocation in GB"
    )
    replicas: Optional[int] = Field(
        None,
        alias="replicas",
        description="Number of replicas",
        ge=1,  # Greater than or equal to 1
        le=20,  # Less than or equal to 20
    )
    storage: Optional[int] = Field(
        None,
        alias="storage",
        description="Storage allocation in GB",
        ge=3,  # Greater than or equal to 3
        le=300,  # Less than or equal to 300
    )


class ClusterContext(BaseModel):
    """Context information for cluster operations."""

    kubeconfig: str = Field(
        ..., alias="kubeconfig", description="Kubernetes configuration"
    )
    region_url: str = Field(
        ..., alias="regionUrl", description="Region URL (e.g., '192.168.10.35.nip.io')"
    )


class ClusterUpdatePayload(BaseModel):
    """Payload for updating a cluster instance."""

    name: str = Field(
        ...,
        alias="name",
        min_length=1,
        max_length=63,
        pattern=r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$",
        description="Cluster name (must be DNS compliant: lowercase, numbers, hyphens, 1-63 chars)",
    )

    resource: ClusterResource = Field(
        ..., alias="resource", description="Resource allocation"
    )


class ClusterCreatePayload(BaseModel):
    """Payload for creating a new cluster instance."""

    name: str = Field(
        ...,
        alias="name",
        min_length=1,
        max_length=63,
        pattern=r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$",
        description="Cluster name (must be DNS compliant: lowercase, numbers, hyphens, 1-63 chars)",
    )

    type: str = Field(..., alias="type", description="Cluster type")

    resource: ClusterResource = Field(
        ..., alias="resource", description="Resource allocation"
    )

    termination_policy: Literal["Delete", "Retain"] = Field(
        default="Delete",
        alias="terminationPolicy",
        description="Termination policy for the cluster",
    )


class ClusterDeletePayload(BaseModel):
    """Payload for deleting a cluster instance."""

    name: str = Field(
        ...,
        alias="name",
        min_length=1,
        max_length=63,
        pattern=r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$",
        description="Cluster name (must be DNS compliant: lowercase, numbers, hyphens, 1-63 chars)",
    )


class ClusterPausePayload(BaseModel):
    """Payload for pausing a cluster instance."""

    name: str = Field(
        ...,
        alias="name",
        min_length=1,
        max_length=63,
        pattern=r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$",
        description="Cluster name (must be DNS compliant: lowercase, numbers, hyphens, 1-63 chars)",
    )


class ClusterStartPayload(BaseModel):
    """Payload for starting a cluster instance."""

    name: str = Field(
        ...,
        alias="name",
        min_length=1,
        max_length=63,
        pattern=r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$",
        description="Cluster name (must be DNS compliant: lowercase, numbers, hyphens, 1-63 chars)",
    )
