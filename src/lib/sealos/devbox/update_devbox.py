"""
Update a devbox instance configuration.
"""

import os
from dotenv import load_dotenv
import requests
from typing import Dict, Any, Literal
from pydantic import BaseModel, Field
from src.utils.sealos.compose_api_url import compose_devbox_api_url

load_dotenv()


class DevboxResource(BaseModel):
    """Resource allocation for devbox."""

    cpu: Literal[1, 2, 4, 8, 16] = Field(
        ..., alias="cpu", description="CPU allocation in cores"
    )
    memory: Literal[1, 2, 4, 8, 16, 32] = Field(
        ..., alias="memory", description="Memory allocation in GB"
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


def update_devbox(
    context: DevboxContext,
    payload: DevboxUpdatePayload,
) -> Dict[str, Any]:
    """
    Update a devbox instance configuration.

    Args:
        context: DevboxContext containing kubeconfig and region_url
        payload: DevboxUpdatePayload containing devbox name and resource configuration

    Returns:
        Dictionary containing the API response

    Raises:
        requests.RequestException: If the API request fails
    """
    region_url = context.region_url
    api_url = compose_devbox_api_url(region_url)

    headers = {"Authorization": context.kubeconfig, "Content-Type": "application/json"}

    response = requests.patch(
        f"{api_url}/v1/devbox/{payload.name}",
        json=payload.model_dump(by_alias=True, exclude_none=True),
        headers=headers,
        verify=False,
    )
    response.raise_for_status()

    # Check if response has content before trying to parse JSON
    if response.text.strip():
        return response.json()
    else:
        return {"message": "Operation completed successfully", "status": "success"}


# python -m src.lib.sealos.devbox.update_devbox
if __name__ == "__main__":
    # Test variables
    context = DevboxContext(
        kubeconfig=os.getenv("BJA_KC", "/path/to/your/kubeconfig"),
        regionUrl=os.getenv("BJA_REGION_URL", "192.168.10.35.nip.io"),
    )

    payload = DevboxUpdatePayload(
        name="test-devbox",
        resource=DevboxResource(cpu=4, memory=8),
    )

    # Test the function
    try:
        result = update_devbox(context, payload)
        print(result)
    except Exception as e:
        print(f"Error updating devbox: {e}")
