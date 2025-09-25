"""
Create cluster instance using Brain API.
"""

import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from src.utils.brain.compose_api_url import compose_api_url

load_dotenv()


class BrainClusterContext(BaseModel):
    """Context information for brain cluster operations."""

    kubeconfig: str = Field(
        ..., alias="kubeconfig", description="Kubernetes configuration"
    )


class ClusterCreateData(BaseModel):
    """Data for creating a cluster instance."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=63,
        pattern=r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$",
        description="Cluster name (must be DNS compliant: lowercase, numbers, hyphens, 1-63 chars)",
    )

    type: Literal[
        "postgresql",
        "mongodb",
        "apecloud-mysql",
        "redis",
        "kafka",
        "milvus",
    ] = Field(..., description="Cluster type")

    cpu: Optional[int] = Field(2, description="CPU allocation in cores")
    memory: Optional[int] = Field(2, description="Memory allocation in GB")
    storage: Optional[int] = Field(10, description="Storage allocation in GB")
    replicas: Optional[int] = Field(1, description="Number of replicas")


def create_cluster(
    context: BrainClusterContext,
    create_data: ClusterCreateData,
) -> Dict[str, Any]:
    """
    Create cluster instance using Brain API.

    Args:
        context: BrainClusterContext containing kubeconfig
        create_data: ClusterCreateData containing cluster configuration

    Returns:
        Dictionary containing the API response

    Raises:
        requests.RequestException: If the API request fails
    """
    base_url = compose_api_url()
    if not base_url:
        raise ValueError("SEALOS_BRAIN_FRONTEND_URL environment variable is not set")

    api_url = f"{base_url}/api/sealos/cluster"

    headers = {
        "Authorization": context.kubeconfig,
        "Content-Type": "application/json",
    }

    response = requests.post(
        api_url,
        json=create_data.model_dump(by_alias=True, exclude_none=True),
        headers=headers,
        verify=False,
    )
    response.raise_for_status()

    # Check if response has content before trying to parse JSON
    if response.text.strip():
        return response.json()
    else:
        return {"message": "Cluster created successfully", "status": "success"}


# python -m src.lib.brain.sealos.cluster.create
if __name__ == "__main__":
    # Test variables
    context = BrainClusterContext(
        kubeconfig=os.getenv("BJA_KC", "/path/to/your/kubeconfig"),
    )

    create_data = ClusterCreateData(
        name="test-cluster",
        type="postgresql",
        cpu=2,
        memory=4,
        storage=20,
        replicas=1,
    )

    # Test the function
    try:
        result = create_cluster(context, create_data)
        print(f"✅ Cluster create API call successful: {result}")
    except Exception as e:
        print(f"❌ Error creating cluster: {e}")
