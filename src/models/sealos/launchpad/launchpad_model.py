"""
Launchpad models with validation for the Sealos launchpad operations.
"""

from typing import Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator


class LaunchpadResource(BaseModel):
    """Resource allocation for launchpad with validation."""

    cpu: Literal[1, 2, 4, 8, 16] = Field(
        ..., alias="cpu", description="CPU allocation in cores"
    )
    memory: Literal[1, 2, 4, 8, 16, 32] = Field(
        ..., alias="memory", description="Memory allocation in GB"
    )
    replicas: int = Field(
        ...,
        alias="replicas",
        description="Number of replicas",
        ge=1,  # Greater than or equal to 1
        le=20,  # Less than or equal to 20
    )


class LaunchpadContext(BaseModel):
    """Context information for launchpad operations."""

    kubeconfig: str = Field(
        ..., alias="kubeconfig", description="Kubernetes configuration"
    )
    region_url: str = Field(
        ..., alias="regionUrl", description="Region URL (e.g., '192.168.10.35.nip.io')"
    )


class LaunchpadUpdatePayload(BaseModel):
    """Payload for updating a launchpad instance."""

    name: str = Field(
        ...,
        alias="name",
        min_length=1,
        max_length=63,
        pattern=r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$",
        description="Launchpad name (must be DNS compliant: lowercase, numbers, hyphens, 1-63 chars)",
    )

    resource: LaunchpadResource = Field(
        ..., alias="resource", description="Resource allocation"
    )
