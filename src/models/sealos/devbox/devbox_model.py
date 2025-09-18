"""
Devbox models with validation for the Sealos devbox operations.
"""

from typing import Dict, Any, Literal, Optional
from pydantic import BaseModel, Field


class DevboxResource(BaseModel):
    """Resource allocation for devbox with validation."""

    cpu: Optional[Literal[1, 2, 4, 8, 16]] = Field(
        None, alias="cpu", description="CPU allocation in cores"
    )
    memory: Optional[Literal[1, 2, 4, 8, 16, 32]] = Field(
        None, alias="memory", description="Memory allocation in GB"
    )


class DevboxContext(BaseModel):
    """Context information for devbox operations."""

    kubeconfig: str = Field(
        ..., alias="kubeconfig", description="Kubernetes configuration"
    )
    region_url: str = Field(
        ..., alias="regionUrl", description="Region URL (e.g., '192.168.10.35.nip.io')"
    )


class DevboxUpdatePayload(BaseModel):
    """Payload for updating a devbox instance."""

    name: str = Field(
        ...,
        alias="name",
        min_length=1,
        max_length=63,
        pattern=r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$",
        description="Devbox name (must be DNS compliant: lowercase, numbers, hyphens, 1-63 chars)",
    )

    resource: DevboxResource = Field(
        ..., alias="resource", description="Resource allocation"
    )


class DevboxStartPayload(BaseModel):
    """Payload for starting a devbox instance."""

    name: str = Field(
        ...,
        alias="name",
        min_length=1,
        max_length=63,
        pattern=r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$",
        description="Devbox name (must be DNS compliant: lowercase, numbers, hyphens, 1-63 chars)",
    )


class DevboxPausePayload(BaseModel):
    """Payload for pausing a devbox instance."""

    name: str = Field(
        ...,
        alias="name",
        min_length=1,
        max_length=63,
        pattern=r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$",
        description="Devbox name (must be DNS compliant: lowercase, numbers, hyphens, 1-63 chars)",
    )


class DevboxDeletePayload(BaseModel):
    """Payload for deleting a devbox instance."""

    name: str = Field(
        ...,
        alias="name",
        min_length=1,
        max_length=63,
        pattern=r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$",
        description="Devbox name (must be DNS compliant: lowercase, numbers, hyphens, 1-63 chars)",
    )
