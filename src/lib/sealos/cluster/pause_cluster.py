"""
Pause a cluster instance.
"""

import os
from dotenv import load_dotenv
import requests
from typing import Dict, Any
from pydantic import BaseModel, Field
from src.utils.sealos.compose_api_url import compose_cluster_api_url

load_dotenv()


class ClusterContext(BaseModel):
    """Context information for cluster operations."""

    kubeconfig: str = Field(
        ..., alias="kubeconfig", description="Kubernetes configuration"
    )
    region_url: str = Field(
        ..., alias="regionUrl", description="Region URL (e.g., '192.168.10.35.nip.io')"
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


def pause_cluster(
    context: ClusterContext,
    payload: ClusterPausePayload,
) -> Dict[str, Any]:
    """
    Pause a cluster instance.

    Args:
        context: ClusterContext containing kubeconfig and region_url
        payload: ClusterPausePayload containing cluster name

    Returns:
        Dictionary containing the API response

    Raises:
        requests.RequestException: If the API request fails
    """
    region_url = context.region_url
    api_url = compose_cluster_api_url(region_url)

    headers = {"Authorization": context.kubeconfig, "Content-Type": "application/json"}

    # Create payload without name since it's in the URL
    request_payload = {}
    url = f"{api_url}/v1/database/{payload.name}/pause"

    print(f"Making request to: {url}")
    print(f"Payload: {request_payload}")

    response = requests.post(
        url,
        json=request_payload,
        headers=headers,
        verify=False,
    )
    response.raise_for_status()

    print(response.text)

    # Check if response has content before trying to parse JSON
    if response.text.strip():
        return response.json()
    else:
        return {"message": "Operation completed successfully", "status": "success"}


# python -m src.lib.sealos.cluster.pause_cluster
if __name__ == "__main__":
    # Test variables
    context = ClusterContext(
        kubeconfig=os.getenv("BJA_KC", "/path/to/your/kubeconfig"),
        regionUrl=os.getenv("BJA_REGION_URL", "192.168.10.35.nip.io"),
    )

    payload = ClusterPausePayload(name="test-cluster")

    # Test the function
    try:
        result = pause_cluster(context, payload)
        print(result)
    except Exception as e:
        print(f"Error pausing cluster: {e}")
