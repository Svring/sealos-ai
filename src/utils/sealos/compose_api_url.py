"""
Utility functions to compose API URLs for different Sealos services based on region URL.
"""


def compose_devbox_api_url(region_url: str) -> str:
    """
    Compose the devbox API URL from a region URL.

    Args:
        region_url: The region URL (e.g., "192.168.10.35.nip.io")

    Returns:
        Complete devbox API URL (e.g., "http://devbox.192.168.10.35.nip.io/api")
    """
    return f"http://devbox.{region_url}/api"


def compose_cluster_api_url(region_url: str) -> str:
    """
    Compose the cluster API URL from a region URL.

    Args:
        region_url: The region URL (e.g., "192.168.10.35.nip.io")

    Returns:
        Complete cluster API URL (e.g., "http://dbprovider.192.168.10.35.nip.io/api")
    """
    return f"http://dbprovider.{region_url}/api"


def compose_launchpad_api_url(region_url: str) -> str:
    """
    Compose the launchpad API URL from a region URL.

    Args:
        region_url: The region URL (e.g., "192.168.10.35.nip.io")

    Returns:
        Complete launchpad API URL (e.g., "http://applaunchpad.192.168.10.35.nip.io/api")
    """
    return f"http://applaunchpad.{region_url}/api"
