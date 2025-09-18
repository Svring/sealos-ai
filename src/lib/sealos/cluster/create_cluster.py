"""
Create a new cluster instance.
"""

import os
from dotenv import load_dotenv
import requests
from typing import Dict, Any, Literal
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


def create_cluster(
    context: ClusterContext,
    payload: ClusterCreatePayload,
) -> Dict[str, Any]:
    """
    Create a new cluster instance.

    Args:
        context: ClusterContext containing kubeconfig and region_url
        payload: ClusterCreatePayload containing cluster configuration

    Returns:
        Dictionary containing the API response

    Raises:
        requests.RequestException: If the API request fails
    """
    region_url = context.region_url
    api_url = compose_cluster_api_url(region_url)

    headers = {"Authorization": context.kubeconfig, "Content-Type": "application/json"}

    response = requests.post(
        f"{api_url}/v1/database",
        json=payload.model_dump(by_alias=True, exclude_none=True),
        headers=headers,
        verify=False,
    )
    response.raise_for_status()

    return response.json()


# python -m src.lib.sealos.cluster.create_cluster
if __name__ == "__main__":
    # Test variables
    context = ClusterContext(
        kubeconfig=os.getenv("35_KC", "/path/to/your/kubeconfig"),
        regionUrl=os.getenv("35_REGION_URL", "192.168.10.35.nip.io"),
    )

    payload = ClusterCreatePayload(
        name="test-cluster",
        type="postgresql",
        resource=ClusterResource(cpu=2, memory=4, replicas=1, storage=3),
    )

    # Test the function
    try:
        result = create_cluster(context, payload)
        print(result)
    except Exception as e:
        print(f"Error creating cluster: {e}")
