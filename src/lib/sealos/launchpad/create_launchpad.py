"""
Create a new launchpad instance.
"""

import os
from dotenv import load_dotenv
import requests
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from src.utils.sealos.compose_api_url import compose_launchpad_api_url

load_dotenv()


class LaunchpadResource(BaseModel):
    """Resource allocation for launchpad."""

    cpu: int = Field(..., alias="cpu", description="CPU allocation in cores")
    memory: int = Field(..., alias="memory", description="Memory allocation in GB")
    replicas: int = Field(..., alias="replicas", description="Number of replicas")


class LaunchpadEnv(BaseModel):
    """Environment variable for launchpad."""

    name: str = Field(..., alias="name", description="Environment variable name")
    value: str = Field(..., alias="value", description="Environment variable value")


class LaunchpadContext(BaseModel):
    """Context information for launchpad operations."""

    kubeconfig: str = Field(
        ..., alias="kubeconfig", description="Kubernetes configuration"
    )
    region_url: str = Field(
        ..., alias="regionUrl", description="Region URL (e.g., '192.168.10.35.nip.io')"
    )


class LaunchpadCreatePayload(BaseModel):
    """Payload for creating a new launchpad instance."""

    name: str = Field(
        ...,
        alias="name",
        min_length=1,
        max_length=63,
        pattern=r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$",
        description="Launchpad name (must be DNS compliant: lowercase, numbers, hyphens, 1-63 chars)",
    )

    image: str = Field(..., alias="image", description="Docker image for the launchpad")

    resource: LaunchpadResource = Field(
        ..., alias="resource", description="Resource allocation"
    )

    env: List[LaunchpadEnv] = Field(
        default=[], alias="env", description="Environment variables"
    )


def create_launchpad(
    context: LaunchpadContext,
    payload: LaunchpadCreatePayload,
) -> Dict[str, Any]:
    """
    Create a new launchpad instance.

    Args:
        context: LaunchpadContext containing kubeconfig and region_url
        payload: LaunchpadCreatePayload containing launchpad configuration

    Returns:
        Dictionary containing the API response

    Raises:
        requests.RequestException: If the API request fails
    """
    region_url = context.region_url
    api_url = compose_launchpad_api_url(region_url)

    headers = {"Authorization": context.kubeconfig, "Content-Type": "application/json"}

    response = requests.post(
        f"{api_url}/v1/app",
        json=payload.model_dump(by_alias=True, exclude_none=True),
        headers=headers,
        verify=False,
    )
    response.raise_for_status()

    return response.json()


# python -m src.lib.sealos.launchpad.create_launchpad
if __name__ == "__main__":
    # Test variables
    context = LaunchpadContext(
        kubeconfig=os.getenv("BJA_KC", "/path/to/your/kubeconfig"),
        regionUrl=os.getenv("BJA_REGION_URL", "192.168.10.35.nip.io"),
    )

    payload = LaunchpadCreatePayload(
        name="test-launchpad",
        image="nginx:latest",
        resource=LaunchpadResource(cpu=2, memory=4, replicas=1),
        env=[
            LaunchpadEnv(name="PORT", value="8080"),
            LaunchpadEnv(name="NODE_ENV", value="production"),
        ],
    )

    # Test the function
    try:
        result = create_launchpad(context, payload)
        print(result)
    except Exception as e:
        print(f"Error creating launchpad: {e}")
