"""
Update launchpad configuration using Brain API.
"""

import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from src.utils.brain.compose_api_url import compose_api_url

load_dotenv()


class BrainLaunchpadContext(BaseModel):
    """Context information for brain launchpad operations."""

    kubeconfig: str = Field(
        ..., alias="kubeconfig", description="Kubernetes configuration"
    )


class LaunchpadUpdateData(BaseModel):
    """Data for updating a launchpad instance."""

    name: str = Field(..., description="Launchpad name")
    # Add fields based on launchpadUpdateFormSchema from the Next.js code
    # This is a placeholder - you may need to adjust based on actual schema
    cpu: Optional[int] = Field(None, description="CPU allocation")
    memory: Optional[int] = Field(None, description="Memory allocation")
    # Add other fields as needed based on the actual launchpadUpdateFormSchema


def update_launchpad(
    context: BrainLaunchpadContext,
    update_data: LaunchpadUpdateData,
) -> Dict[str, Any]:
    """
    Update launchpad configuration using Brain API.

    Args:
        context: BrainLaunchpadContext containing kubeconfig
        update_data: LaunchpadUpdateData containing update configuration

    Returns:
        Dictionary containing the API response

    Raises:
        requests.RequestException: If the API request fails
    """
    base_url = compose_api_url()
    if not base_url:
        raise ValueError("SEALOS_BRAIN_FRONTEND_URL environment variable is not set")

    api_url = f"{base_url}/api/sealos/launchpad/{update_data.name}"

    headers = {
        "Authorization": context.kubeconfig,
        "Content-Type": "application/json",
    }

    response = requests.patch(
        api_url,
        json=update_data.model_dump(by_alias=True, exclude_none=True),
        headers=headers,
        verify=False,
    )
    response.raise_for_status()

    # Check if response has content before trying to parse JSON
    if response.text.strip():
        return response.json()
    else:
        return {"message": "Operation completed successfully", "status": "success"}


# python -m src.lib.brain.sealos.launchpad.update
if __name__ == "__main__":
    # Test variables
    context = BrainLaunchpadContext(
        kubeconfig=os.getenv("BJA_KC", "/path/to/your/kubeconfig"),
    )

    update_data = LaunchpadUpdateData(
        name="devbox124-release-rfboksunnceh",
        cpu=4,
        memory=8,
    )

    # Test the function
    try:
        result = update_launchpad(context, update_data)
        print(result)
    except Exception as e:
        print(f"Error updating launchpad: {e}")
