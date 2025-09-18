"""
Create a new devbox instance.
"""

import os
from dotenv import load_dotenv
import requests
from typing import Dict, Any, List, Literal, Optional
from pydantic import BaseModel, Field
from src.utils.sealos.compose_api_url import compose_devbox_api_url

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()


class DevboxResource(BaseModel):
    """Resource allocation for devbox."""

    cpu: Literal[1, 2, 4, 8, 16] = Field(
        ..., alias="cpu", description="CPU allocation in cores"
    )
    memory: Literal[1, 2, 4, 8, 16, 32] = Field(
        ..., alias="memory", description="Memory allocation in GB"
    )


class DevboxPort(BaseModel):
    """Port configuration for devbox."""

    number: int = Field(..., alias="number", description="Port number")
    protocol: Literal["HTTP", "GRPC", "WS"] = Field(
        default="HTTP", alias="protocol", description="Protocol type"
    )
    exposes_public_domain: bool = Field(
        default=True,
        alias="exposesPublicDomain",
        description="Whether port is publicly accessible",
    )
    custom_domain: Optional[str] = Field(
        default=None,
        alias="customDomain",
        description="Custom domain for public access",
    )


class DevboxContext(BaseModel):
    """Context information for devbox operations."""

    kubeconfig: str = Field(
        ..., alias="kubeconfig", description="Kubernetes configuration"
    )
    region_url: str = Field(
        ..., alias="regionUrl", description="Region URL (e.g., '192.168.10.35.nip.io')"
    )


class DevboxCreatePayload(BaseModel):
    """Payload for creating a new devbox instance."""

    name: str = Field(
        ...,
        alias="name",
        min_length=1,
        max_length=63,
        pattern=r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$",
        description="Devbox name (must be DNS compliant: lowercase, numbers, hyphens, 1-63 chars)",
    )

    runtime: Literal[
        "nuxt3",
        "angular",
        "quarkus",
        "ubuntu",
        "flask",
        "java",
        "chi",
        "net",
        "iris",
        "hexo",
        "python",
        "docusaurus",
        "vitepress",
        "cpp",
        "vue",
        "nginx",
        "rocket",
        "debian-ssh",
        "vert.x",
        "express.js",
        "django",
        "next.js",
        "sealaf",
        "go",
        "react",
        "php",
        "svelte",
        "c",
        "astro",
        "umi",
        "gin",
        "echo",
        "rust",
    ] = Field(..., alias="runtime", description="Runtime environment name")

    resource: DevboxResource = Field(
        default=DevboxResource(cpu=1, memory=1),
        alias="resource",
        description="Resource allocation",
    )

    ports: List[DevboxPort] = Field(
        default=[],
        alias="ports",
        description="Port configurations (optional, can be empty)",
    )


def create_devbox(
    context: DevboxContext,
    payload: DevboxCreatePayload,
) -> Dict[str, Any]:
    """
    Create a new devbox instance.

    Args:
        context: DevboxContext containing kubeconfig and region_url
        payload: DevboxCreatePayload containing devbox configuration

    Returns:
        Dictionary containing the API response

    Raises:
        requests.RequestException: If the API request fails
    """
    region_url = context.region_url
    api_url = compose_devbox_api_url(region_url)

    headers = {"Authorization": context.kubeconfig, "Content-Type": "application/json"}

    response = requests.post(
        f"{api_url}/v1/devbox",
        json=payload.model_dump(by_alias=True, exclude_none=True),
        headers=headers,
        verify=False,
    )
    response.raise_for_status()

    return response.json()


# python -m src.lib.sealos.devbox.create_devbox
if __name__ == "__main__":
    # Test variables
    context = DevboxContext(
        kubeconfig=os.getenv("BJA_KC", "/path/to/your/kubeconfig"),
        regionUrl=os.getenv("BJA_REGION_URL", "192.168.10.35.nip.io"),
    )

    payload = DevboxCreatePayload(
        name="test-devbox",
        runtime="python",
        resource=DevboxResource(cpu=2, memory=4),
        ports=[
            DevboxPort(
                number=8080,
                protocol="HTTP",
                exposes_public_domain=True,
            ),
            DevboxPort(number=3000, protocol="WS", exposes_public_domain=False),
        ],
    )

    # Test the function
    try:
        result = create_devbox(context, payload)
        print(result)
    except Exception as e:
        print(f"Error creating devbox: {e}")
