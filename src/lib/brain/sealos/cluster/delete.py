"""
Delete cluster instance using Brain API.
"""

import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any
from pydantic import BaseModel, Field
from src.utils.brain.compose_api_url import compose_api_url

load_dotenv()


class BrainClusterContext(BaseModel):
    """Context information for brain cluster operations."""

    kubeconfig: str = Field(
        ..., alias="kubeconfig", description="Kubernetes configuration"
    )


def delete_cluster(
    context: BrainClusterContext,
    name: str,
) -> Dict[str, Any]:
    """
    Delete cluster instance using Brain API.

    Args:
        context: BrainClusterContext containing kubeconfig
        name: Cluster name to delete

    Returns:
        Dictionary containing the API response

    Raises:
        requests.RequestException: If the API request fails
    """
    base_url = compose_api_url()
    if not base_url:
        raise ValueError("SEALOS_BRAIN_FRONTEND_URL environment variable is not set")

    api_url = f"{base_url}/api/sealos/cluster/{name}"

    headers = {
        "Authorization": context.kubeconfig,
        "Content-Type": "application/json",
    }

    response = requests.delete(
        api_url,
        headers=headers,
        verify=False,
    )
    response.raise_for_status()

    # Check if response has content before trying to parse JSON
    if response.text.strip():
        return response.json()
    else:
        return {"message": "Cluster deleted successfully", "status": "success"}


# python -m src.lib.brain.sealos.cluster.delete
if __name__ == "__main__":
    # Test variables
    context = BrainClusterContext(
        kubeconfig=os.getenv("BJA_KC", "/path/to/your/kubeconfig"),
    )

    # Test the function
    try:
        result = delete_cluster(context, "my-cluster")
        print(f"✅ Cluster delete API call successful: {result}")
    except Exception as e:
        print(f"❌ Error deleting cluster: {e}")
