"""
Delete launchpad instance using Brain API.
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


def delete_launchpad(
    context: BrainLaunchpadContext,
    name: str,
) -> Dict[str, Any]:
    """
    Delete launchpad instance using Brain API.

    Args:
        context: BrainLaunchpadContext containing kubeconfig
        name: Launchpad name to delete

    Returns:
        Dictionary containing the API response

    Raises:
        requests.RequestException: If the API request fails
    """
    base_url = compose_api_url()
    if not base_url:
        raise ValueError("SEALOS_BRAIN_FRONTEND_URL environment variable is not set")

    api_url = f"{base_url}/api/sealos/launchpad/{name}"

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
        return {"message": "Launchpad deleted successfully", "status": "success"}


# python -m src.lib.brain.sealos.launchpad.delete
if __name__ == "__main__":
    # Test variables
    context = BrainLaunchpadContext(
        kubeconfig=os.getenv("BJA_KC", "/path/to/your/kubeconfig"),
    )

    # Test the function
    try:
        result = delete_launchpad(context, "app-9a5ty6")
        print(f"✅ Launchpad delete API call successful: {result}")
    except Exception as e:
        print(f"❌ Error deleting launchpad: {e}")
