"""
Perform devbox lifecycle operations using Brain API.
"""

import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any, Literal
from pydantic import BaseModel, Field
from src.utils.brain.compose_api_url import compose_api_url

load_dotenv()


class BrainDevboxContext(BaseModel):
    """Context information for brain devbox operations."""

    kubeconfig: str = Field(
        ..., alias="kubeconfig", description="Kubernetes configuration"
    )


class DevboxLifecycleAction(BaseModel):
    """Action for devbox lifecycle operations."""

    action: Literal["start", "pause", "shutdown", "restart", "delete"] = Field(
        ..., description="Lifecycle action to perform"
    )


def devbox_lifecycle(
    context: BrainDevboxContext,
    name: str,
    action: DevboxLifecycleAction,
) -> Dict[str, Any]:
    """
    Perform devbox lifecycle operations using Brain API.

    Args:
        context: BrainDevboxContext containing kubeconfig
        name: Devbox name
        action: DevboxLifecycleAction containing the action to perform

    Returns:
        Dictionary containing the API response

    Raises:
        requests.RequestException: If the API request fails
    """
    base_url = compose_api_url()
    if not base_url:
        raise ValueError("SEALOS_BRAIN_FRONTEND_URL environment variable is not set")

    api_url = f"{base_url}/api/sealos/devbox/{name}/lifecycle"

    headers = {
        "Authorization": context.kubeconfig,
        "Content-Type": "application/json",
    }

    response = requests.post(
        api_url,
        json=action.model_dump(by_alias=True, exclude_none=True),
        headers=headers,
        verify=False,
    )
    response.raise_for_status()

    # Check if response has content before trying to parse JSON
    if response.text.strip():
        return response.json()
    else:
        return {"message": "Operation completed successfully", "status": "success"}


# python -m src.lib.brain.sealos.devbox.lifecycle
if __name__ == "__main__":
    # Test variables
    context = BrainDevboxContext(
        kubeconfig=os.getenv("BJA_KC", "/path/to/your/kubeconfig"),
    )

    action = DevboxLifecycleAction(action="start")

    # Test the function
    try:
        result = devbox_lifecycle(context, "my-devb", action)
        print(result)
    except Exception as e:
        print(f"Error performing devbox lifecycle action: {e}")
