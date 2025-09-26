"""
Perform devbox autostart operations using Brain API.
"""

import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any
from pydantic import BaseModel, Field
from src.utils.brain.compose_api_url import compose_api_url

load_dotenv()


class BrainDevboxContext(BaseModel):
    """Context information for brain devbox operations."""

    kubeconfig: str = Field(
        ..., alias="kubeconfig", description="Kubernetes configuration"
    )


def devbox_autostart(
    context: BrainDevboxContext,
    name: str,
) -> Dict[str, Any]:
    """
    Perform devbox autostart operations using Brain API.

    Args:
        context: BrainDevboxContext containing kubeconfig
        name: Devbox name

    Returns:
        Dictionary containing the API response

    Raises:
        requests.RequestException: If the API request fails
    """
    base_url = compose_api_url()
    if not base_url:
        raise ValueError("SEALOS_BRAIN_FRONTEND_URL environment variable is not set")

    api_url = f"{base_url}/api/sealos/devbox/{name}/autostart"

    headers = {
        "Authorization": context.kubeconfig,
        "Content-Type": "application/json",
    }

    response = requests.post(
        api_url,
        headers=headers,
        verify=False,
    )
    response.raise_for_status()

    # Check if response has content before trying to parse JSON
    if response.text.strip():
        return response.json()
    else:
        return {
            "message": "Autostart operation completed successfully",
            "status": "success",
        }


# python -m src.lib.brain.sealos.devbox.autostart
if __name__ == "__main__":
    # Test variables
    context = BrainDevboxContext(
        kubeconfig=os.getenv("BJA_KC", "/path/to/your/kubeconfig"),
    )

    # Test the function
    try:
        result = devbox_autostart(context, "my-devb")
        print(result)
    except Exception as e:
        print(f"Error performing devbox autostart action: {e}")
