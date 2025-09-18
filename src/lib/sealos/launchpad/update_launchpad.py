"""
Update a launchpad instance configuration.
"""

import os
from dotenv import load_dotenv
import requests
from typing import Dict, Any
from src.utils.sealos.compose_api_url import compose_launchpad_api_url
from src.models.sealos.launchpad.launchpad_model import (
    LaunchpadContext,
    LaunchpadUpdatePayload,
    LaunchpadResource,
)

load_dotenv()


def update_launchpad(
    context: LaunchpadContext,
    payload: LaunchpadUpdatePayload,
) -> Dict[str, Any]:
    """
    Update a launchpad instance configuration.

    Args:
        context: LaunchpadContext containing kubeconfig and region_url
        payload: LaunchpadUpdatePayload containing launchpad name and resource configuration

    Returns:
        Dictionary containing the API response

    Raises:
        requests.RequestException: If the API request fails
    """
    region_url = context.region_url
    api_url = compose_launchpad_api_url(region_url)

    headers = {"Authorization": context.kubeconfig, "Content-Type": "application/json"}

    response = requests.patch(
        f"{api_url}/v1/app/{payload.name}",
        json=payload.model_dump(by_alias=True, exclude_none=True),
        headers=headers,
        verify=False,
    )
    response.raise_for_status()

    # Check if response has content before trying to parse JSON
    if response.text.strip():
        return response.json()
    else:
        return {"message": "Operation completed successfully", "status": "success"}


# python -m src.lib.sealos.launchpad.update_launchpad
if __name__ == "__main__":
    # Test variables
    context = LaunchpadContext(
        kubeconfig=os.getenv("BJA_KC", "/path/to/your/kubeconfig"),
        regionUrl=os.getenv("BJA_REGION_URL", "192.168.10.35.nip.io"),
    )

    payload = LaunchpadUpdatePayload(
        name="test-launchpad",
        resource=LaunchpadResource(cpu=4, memory=8, replicas=2),
    )

    # Test the function
    try:
        result = update_launchpad(context, payload)
        print(result)
    except Exception as e:
        print(f"Error updating launchpad: {e}")
