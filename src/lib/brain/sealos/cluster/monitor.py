"""
Get cluster monitoring data using Brain API.
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


def get_cluster_monitor(
    context: BrainClusterContext,
    name: str,
    db_type: str,
) -> Dict[str, Any]:
    """
    Get cluster monitoring data using Brain API.

    Args:
        context: BrainClusterContext containing kubeconfig
        name: Cluster name
        db_type: Database type for monitoring

    Returns:
        Dictionary containing the monitoring data

    Raises:
        requests.RequestException: If the API request fails
    """
    base_url = compose_api_url()
    if not base_url:
        raise ValueError("SEALOS_BRAIN_FRONTEND_URL environment variable is not set")

    api_url = f"{base_url}/api/sealos/cluster/{name}/monitor"

    headers = {
        "Authorization": context.kubeconfig,
        "Content-Type": "application/json",
    }

    params = {"dbType": db_type}

    response = requests.get(
        api_url,
        headers=headers,
        params=params,
        verify=False,
    )
    response.raise_for_status()

    return response.json()


# python -m src.lib.brain.sealos.cluster.monitor
if __name__ == "__main__":
    # Test variables
    context = BrainClusterContext(
        kubeconfig=os.getenv("BJA_KC", "/path/to/your/kubeconfig"),
    )

    # Test the function
    try:
        result = get_cluster_monitor(context, "ai-postgresql", "mysql")
        print(result)
    except Exception as e:
        print(f"Error getting cluster monitor: {e}")
