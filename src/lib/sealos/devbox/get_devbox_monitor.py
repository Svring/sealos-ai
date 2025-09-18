"""
Get monitoring information for a devbox instance.
"""

import requests
from typing import Dict, Any
from ...utils.sealos.compose_api_url import compose_devbox_api_url


def get_devbox_monitor(
    context: Dict[str, str],
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Get monitoring information for a devbox instance.

    Args:
        context: Dictionary containing "kubeconfig" and "region_url"
        payload: Dictionary containing devbox identification and monitoring parameters
                (name, metrics_type, etc.)

    Returns:
        Dictionary containing the monitoring data

    Raises:
        requests.RequestException: If the API request fails
    """
    region_url = context["region_url"]
    api_url = compose_devbox_api_url(region_url)

    response = requests.get(f"{api_url}/devbox/monitor", json=payload)
    response.raise_for_status()

    return response.json()
