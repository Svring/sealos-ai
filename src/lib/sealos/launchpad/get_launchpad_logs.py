"""
Get logs for a launchpad instance.
"""

import os
from dotenv import load_dotenv
import requests
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from src.utils.sealos.compose_api_url import compose_launchpad_api_url

load_dotenv()


class LaunchpadContext(BaseModel):
    """Context information for launchpad operations."""

    kubeconfig: str = Field(
        ..., alias="kubeconfig", description="Kubernetes configuration"
    )
    region_url: str = Field(
        ..., alias="regionUrl", description="Region URL (e.g., '192.168.10.35.nip.io')"
    )


class LaunchpadLogsPayload(BaseModel):
    """Payload for getting launchpad logs."""

    name: str = Field(
        ...,
        alias="name",
        min_length=1,
        max_length=63,
        pattern=r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$",
        description="Launchpad name (must be DNS compliant: lowercase, numbers, hyphens, 1-63 chars)",
    )

    lines: Optional[int] = Field(
        default=100, alias="lines", description="Number of log lines to retrieve"
    )

    follow: Optional[bool] = Field(
        default=False, alias="follow", description="Whether to follow logs in real-time"
    )


def get_launchpad_logs(
    context: LaunchpadContext,
    payload: LaunchpadLogsPayload,
) -> Dict[str, Any]:
    """
    Get logs for a launchpad instance.

    Args:
        context: LaunchpadContext containing kubeconfig and region_url
        payload: LaunchpadLogsPayload containing launchpad name and log parameters

    Returns:
        Dictionary containing the log data

    Raises:
        requests.RequestException: If the API request fails
    """
    region_url = context.region_url
    api_url = compose_launchpad_api_url(region_url)

    headers = {"Authorization": context.kubeconfig, "Content-Type": "application/json"}

    response = requests.get(
        f"{api_url}/v1/launchpad/{payload.name}/logs",
        json=payload.model_dump(by_alias=True, exclude_none=True),
        headers=headers,
        verify=False,
    )
    response.raise_for_status()

    return response.json()


# python -m src.lib.sealos.launchpad.get_launchpad_logs
if __name__ == "__main__":
    # Test variables
    context = LaunchpadContext(
        kubeconfig=os.getenv("BJA_KC", "/path/to/your/kubeconfig"),
        regionUrl=os.getenv("BJA_REGION_URL", "192.168.10.35.nip.io"),
    )

    payload = LaunchpadLogsPayload(name="test-launchpad", lines=50, follow=False)

    # Test the function
    try:
        result = get_launchpad_logs(context, payload)
        print(result)
    except Exception as e:
        print(f"Error getting launchpad logs: {e}")
