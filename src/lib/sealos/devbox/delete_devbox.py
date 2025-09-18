"""
Delete a devbox instance.
"""

import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any
from pydantic import BaseModel, Field
from src.utils.sealos.compose_api_url import compose_devbox_api_url

load_dotenv()


class DevboxContext(BaseModel):
    """Context information for devbox operations."""

    kubeconfig: str = Field(
        ..., alias="kubeconfig", description="Kubernetes configuration"
    )
    region_url: str = Field(
        ..., alias="regionUrl", description="Region URL (e.g., '192.168.10.35.nip.io')"
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


def delete_devbox(
    context: DevboxContext,
    payload: DevboxDeletePayload,
) -> Dict[str, Any]:
    """
    Delete a devbox instance.

    Args:
        context: DevboxContext containing kubeconfig and region_url
        payload: DevboxDeletePayload containing devbox name

    Returns:
        Dictionary containing the API response

    Raises:
        requests.RequestException: If the API request fails
    """
    region_url = context.region_url
    api_url = compose_devbox_api_url(region_url)

    headers = {"Authorization": context.kubeconfig, "Content-Type": "application/json"}

    response = requests.delete(
        f"{api_url}/v1/devbox/{payload.name}/delete",
        headers=headers,
        verify=False,
    )
    response.raise_for_status()

    # Check if response has content before trying to parse JSON
    if response.text.strip():
        return response.json()
    else:
        return {"message": "Operation completed successfully", "status": "success"}


# python -m src.lib.sealos.devbox.delete_devbox
if __name__ == "__main__":
    # Test variables
    context = DevboxContext(
        kubeconfig=os.getenv("BJA_KC", "/path/to/your/kubeconfig"),
        regionUrl=os.getenv("BJA_REGION_URL", "192.168.10.35.nip.io"),
    )

    payload = DevboxDeletePayload(name="test-devbox")

    # Test the function
    try:
        result = delete_devbox(context, payload)
        print(result)
    except Exception as e:
        print(f"Error deleting devbox: {e}")
