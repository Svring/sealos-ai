"""
Get cluster logs using Brain API.
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


def get_cluster_logs(
    context: BrainClusterContext,
    name: str,
) -> Dict[str, Any]:
    """
    Get cluster logs using Brain API.

    Args:
        context: BrainClusterContext containing kubeconfig
        name: Cluster name

    Returns:
        Dictionary containing the cluster logs

    Raises:
        requests.RequestException: If the API request fails
    """
    base_url = compose_api_url()
    if not base_url:
        raise ValueError("SEALOS_BRAIN_FRONTEND_URL environment variable is not set")

    api_url = f"{base_url}/api/sealos/cluster/{name}/logs"

    headers = {
        "Authorization": context.kubeconfig,
        "Content-Type": "application/json",
    }

    response = requests.get(
        api_url,
        headers=headers,
        verify=False,
    )
    response.raise_for_status()

    return response.json()


# python -m src.lib.brain.sealos.cluster.logs
if __name__ == "__main__":
    # Test variables
    context = BrainClusterContext(
        kubeconfig=os.getenv("BJA_KC", "/path/to/your/kubeconfig"),
    )

    # Test the function
    try:
        result = get_cluster_logs(context, "ai-postgresql")
        print(result)
    except Exception as e:
        print(f"Error getting cluster logs: {e}")
