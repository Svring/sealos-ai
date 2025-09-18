"""
Update a devbox instance configuration.
"""

import requests
from typing import Dict, Any
from ...utils.sealos.compose_api_url import compose_devbox_api_url


def update_devbox(
    context: Dict[str, str],
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Update a devbox instance configuration.

    Args:
        context: Dictionary containing "kubeconfig" and "region_url"
        payload: Dictionary containing devbox identification and update parameters
                (name, cpu, memory, storage, etc.)

    Returns:
        Dictionary containing the API response

    Raises:
        requests.RequestException: If the API request fails
    """
    region_url = context["region_url"]
    api_url = compose_devbox_api_url(region_url)

    response = requests.put(f"{api_url}/devbox", json=payload)
    response.raise_for_status()

    return response.json()
