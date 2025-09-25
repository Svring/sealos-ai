"""
Create devbox instance using Brain API.
"""

import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any, Literal, Optional, List
from pydantic import BaseModel, Field
from src.utils.brain.compose_api_url import compose_api_url

load_dotenv()


class BrainDevboxContext(BaseModel):
    """Context information for brain devbox operations."""

    kubeconfig: str = Field(
        ..., alias="kubeconfig", description="Kubernetes configuration"
    )


class DevboxCreateData(BaseModel):
    """Data for creating a devbox instance."""

    name: str = Field(
        ...,
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
    ] = Field(..., description="Runtime environment name")

    cpu: Optional[int] = Field(2, description="CPU allocation in cores")
    memory: Optional[int] = Field(4, description="Memory allocation in GB")
    ports: Optional[List[int]] = Field(
        default=[], description="Array of port numbers to expose"
    )


def create_devbox(
    context: BrainDevboxContext,
    create_data: DevboxCreateData,
) -> Dict[str, Any]:
    """
    Create devbox instance using Brain API.

    Args:
        context: BrainDevboxContext containing kubeconfig
        create_data: DevboxCreateData containing devbox configuration

    Returns:
        Dictionary containing the API response

    Raises:
        requests.RequestException: If the API request fails
    """
    base_url = compose_api_url()
    if not base_url:
        raise ValueError("SEALOS_BRAIN_FRONTEND_URL environment variable is not set")

    api_url = f"{base_url}/api/sealos/devbox"

    headers = {
        "Authorization": context.kubeconfig,
        "Content-Type": "application/json",
    }

    response = requests.post(
        api_url,
        json=create_data.model_dump(by_alias=True, exclude_none=True),
        headers=headers,
        verify=False,
    )
    response.raise_for_status()

    # Check if response has content before trying to parse JSON
    if response.text.strip():
        return response.json()
    else:
        return {"message": "Devbox created successfully", "status": "success"}


# python -m src.lib.brain.sealos.devbox.create
if __name__ == "__main__":
    # Test variables
    context = BrainDevboxContext(
        kubeconfig=os.getenv("BJA_KC", "/path/to/your/kubeconfig"),
    )

    create_data = DevboxCreateData(
        name="test-devbox",
        runtime="python",
        cpu=2,
        memory=4,
        ports=[8080, 3000],
    )

    # Test the function
    try:
        result = create_devbox(context, create_data)
        print(f"✅ Devbox create API call successful: {result}")
    except Exception as e:
        print(f"❌ Error creating devbox: {e}")
