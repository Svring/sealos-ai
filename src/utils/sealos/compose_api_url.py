"""
Utility functions to compose API URLs for different Sealos services based on region URL.
"""


def compose_devbox_api_url(region_url: str) -> str:
    return f"http://devbox.{region_url}/api"


def compose_cluster_api_url(region_url: str) -> str:
    return f"http://dbprovider.{region_url}/api"


def compose_launchpad_api_url(region_url: str) -> str:
    return f"http://applaunchpad.{region_url}/api"
