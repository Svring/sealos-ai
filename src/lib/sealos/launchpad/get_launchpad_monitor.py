"""
Get monitoring information for a launchpad instance.
"""

import os
from dotenv import load_dotenv
import requests
from typing import Dict, Any, Literal
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


class LaunchpadMonitorPayload(BaseModel):
    """Payload for getting launchpad monitoring information."""

    name: str = Field(
        ...,
        alias="name",
        min_length=1,
        max_length=63,
        pattern=r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$",
        description="Launchpad name (must be DNS compliant: lowercase, numbers, hyphens, 1-63 chars)",
    )

    metrics_type: Literal["all", "cpu", "memory", "storage", "network"] = Field(
        default="all", alias="metricsType", description="Type of metrics to retrieve"
    )


def get_launchpad_monitor(
    context: LaunchpadContext,
    payload: LaunchpadMonitorPayload,
) -> Dict[str, Any]:
    """
    Get monitoring information for a launchpad instance.

    Args:
        context: LaunchpadContext containing kubeconfig and region_url
        payload: LaunchpadMonitorPayload containing launchpad name and metrics type

    Returns:
        Dictionary containing the monitoring data

    Raises:
        requests.RequestException: If the API request fails
    """
    region_url = context.region_url
    api_url = compose_launchpad_api_url(region_url)

    headers = {"Authorization": context.kubeconfig, "Content-Type": "application/json"}

    response = requests.get(
        f"{api_url}/v1/launchpad/{payload.name}/monitor",
        json=payload.model_dump(by_alias=True, exclude_none=True),
        headers=headers,
        verify=False,
    )
    response.raise_for_status()

    return response.json()


# python -m src.lib.sealos.launchpad.get_launchpad_monitor
if __name__ == "__main__":
    # Test variables
    context = LaunchpadContext(
        kubeconfig=os.getenv("BJA_KC", "/path/to/your/kubeconfig"),
        regionUrl=os.getenv("BJA_REGION_URL", "192.168.10.35.nip.io"),
    )

    payload = LaunchpadMonitorPayload(name="test-launchpad", metrics_type="all")

    # Test the function
    try:
        result = get_launchpad_monitor(context, payload)
        print(result)
    except Exception as e:
        print(f"Error getting launchpad monitor: {e}")
