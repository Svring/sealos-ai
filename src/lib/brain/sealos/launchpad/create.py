"""
Create launchpad instance using Brain API.
"""

import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from src.utils.brain.compose_api_url import compose_api_url

load_dotenv()


class BrainLaunchpadContext(BaseModel):
    """Context information for brain launchpad operations."""

    kubeconfig: str = Field(
        ..., alias="kubeconfig", description="Kubernetes configuration"
    )


class LaunchpadCreateData(BaseModel):
    """Data for creating a launchpad instance."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=63,
        pattern=r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$",
        description="Launchpad name (must be DNS compliant: lowercase, numbers, hyphens, 1-63 chars)",
    )

    image: str = Field(..., description="Docker image name")

    cpu: Optional[int] = Field(1, description="CPU allocation in cores")
    memory: Optional[int] = Field(1, description="Memory allocation in GB")
    ports: Optional[List[int]] = Field(
        default=[], description="Array of port numbers to expose"
    )
    env: Optional[List[tuple[str, str]]] = Field(
        default=[], description="Array of environment variable tuples (name, value)"
    )


def create_launchpad(
    context: BrainLaunchpadContext,
    create_data: LaunchpadCreateData,
) -> Dict[str, Any]:
    """
    Create launchpad instance using Brain API.

    Args:
        context: BrainLaunchpadContext containing kubeconfig
        create_data: LaunchpadCreateData containing launchpad configuration

    Returns:
        Dictionary containing the API response

    Raises:
        requests.RequestException: If the API request fails
    """
    base_url = compose_api_url()
    if not base_url:
        raise ValueError("SEALOS_BRAIN_FRONTEND_URL environment variable is not set")

    api_url = f"{base_url}/api/sealos/launchpad"

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
        return {"message": "Launchpad created successfully", "status": "success"}


# python -m src.lib.brain.sealos.launchpad.create
if __name__ == "__main__":
    # Test variables
    context = BrainLaunchpadContext(
        kubeconfig=os.getenv("BJA_KC", "/path/to/your/kubeconfig"),
    )

    create_data = LaunchpadCreateData(
        name="test-launchpad",
        image="nginx:latest",
        cpu=2,
        memory=4,
        ports=[80, 443],
        env=[("ENV", "production"), ("DEBUG", "false")],
    )

    # Test the function
    try:
        result = create_launchpad(context, create_data)
        print(f"✅ Launchpad create API call successful: {result}")
    except Exception as e:
        print(f"❌ Error creating launchpad: {e}")
