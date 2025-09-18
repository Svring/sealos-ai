"""
Start a devbox instance.
"""

import requests
from typing import Dict, Any
from ...utils.sealos.compose_api_url import compose_devbox_api_url


def start_devbox(
    context: Dict[str, str],
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Start a devbox instance.

    Args:
        context: Dictionary containing "kubeconfig" and "region_url"
        payload: Dictionary containing devbox identification parameters
                (name, etc.)

    Returns:
        Dictionary containing the API response

    Raises:
        requests.RequestException: If the API request fails
    """
    region_url = context["region_url"]
    api_url = compose_devbox_api_url(region_url)

    response = requests.post(f"{api_url}/devbox/start", json=payload)
    response.raise_for_status()

    return response.json()
