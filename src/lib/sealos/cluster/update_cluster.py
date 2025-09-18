"""
Update a cluster instance configuration.
"""

import os
from dotenv import load_dotenv
import requests
from typing import Dict, Any
from pydantic import BaseModel, Field
from src.utils.sealos.compose_api_url import compose_cluster_api_url

load_dotenv()


class ClusterResource(BaseModel):
    """Resource allocation for cluster."""

    cpu: int = Field(..., alias="cpu", description="CPU allocation in cores")
    memory: int = Field(..., alias="memory", description="Memory allocation in GB")
    replicas: int = Field(..., alias="replicas", description="Number of replicas")
    storage: int = Field(..., alias="storage", description="Storage allocation in GB")


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


def update_cluster(
    context: ClusterContext,
    payload: ClusterUpdatePayload,
) -> Dict[str, Any]:
    """
    Update a cluster instance configuration.

    Args:
        context: ClusterContext containing kubeconfig and region_url
        payload: ClusterUpdatePayload containing cluster name and resource configuration

    Returns:
        Dictionary containing the API response

    Raises:
        requests.RequestException: If the API request fails
    """
    region_url = context.region_url
    api_url = compose_cluster_api_url(region_url)

    headers = {"Authorization": context.kubeconfig, "Content-Type": "application/json"}

    response = requests.patch(
        f"{api_url}/v1/database/{payload.name}",
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


# python -m src.lib.sealos.cluster.update_cluster
if __name__ == "__main__":
    # Test variables
    context = ClusterContext(
        kubeconfig=os.getenv("BJA_KC", "/path/to/your/kubeconfig"),
        regionUrl=os.getenv("BJA_REGION_URL", "192.168.10.35.nip.io"),
    )

    payload = ClusterUpdatePayload(
        name="test-cluster",
        resource=ClusterResource(cpu=4, memory=8, replicas=2, storage=50),
    )

    # Test the function
    try:
        result = update_cluster(context, payload)
        print(result)
    except Exception as e:
        print(f"Error updating cluster: {e}")
