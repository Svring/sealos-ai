"""
Check launchpad network status using Brain API.
"""

import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any
from pydantic import BaseModel, Field
from src.utils.brain.compose_api_url import compose_api_url

load_dotenv()


class BrainLaunchpadContext(BaseModel):
    """Context information for brain launchpad operations."""

    kubeconfig: str = Field(
        ..., alias="kubeconfig", description="Kubernetes configuration"
    )


def check_launchpad_network(
    context: BrainLaunchpadContext,
    name: str,
) -> Dict[str, Any]:
    """
    Check launchpad network status using Brain API.

    Args:
        context: BrainLaunchpadContext containing kubeconfig
        name: Launchpad name

    Returns:
        Dictionary containing the network status information

    Raises:
        requests.RequestException: If the API request fails
    """
    base_url = compose_api_url()
    if not base_url:
        raise ValueError("SEALOS_BRAIN_FRONTEND_URL environment variable is not set")

    api_url = f"{base_url}/api/sealos/launchpad/{name}/network"

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


# python -m src.lib.brain.sealos.launchpad.network
if __name__ == "__main__":
    # Test variables
    context = BrainLaunchpadContext(
        kubeconfig=os.getenv("BJA_KC", "/path/to/your/kubeconfig"),
    )

    # Test the function
    try:
        result = check_launchpad_network(context, "devbox124-release-rfboksunnceh")
        print(result)
    except Exception as e:
        print(f"Error checking launchpad network: {e}")
