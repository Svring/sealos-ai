"""
Update devbox configuration using Brain API.
"""

import os
import requests
from dotenv import load_dotenv
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from src.utils.brain.compose_api_url import compose_api_url

load_dotenv()


class BrainDevboxContext(BaseModel):
    """Context information for brain devbox operations."""

    kubeconfig: str = Field(
        ..., alias="kubeconfig", description="Kubernetes configuration"
    )


class DevboxUpdateData(BaseModel):
    """Data for updating a devbox instance."""

    name: str = Field(..., description="Devbox name")
    # Add fields based on devboxUpdateFormSchema from the Next.js code
    # This is a placeholder - you may need to adjust based on actual schema
    cpu: Optional[int] = Field(None, description="CPU allocation")
    memory: Optional[int] = Field(None, description="Memory allocation")
    create_ports: Optional[List[int]] = Field(
        None, alias="createPorts", description="Array of port numbers to create"
    )
    delete_ports: Optional[List[int]] = Field(
        None, alias="deletePorts", description="Array of port numbers to delete"
    )
    # Add other fields as needed based on the actual devboxUpdateFormSchema


def update_devbox(
    context: BrainDevboxContext,
    update_data: DevboxUpdateData,
) -> Dict[str, Any]:
    """
    Update devbox configuration using Brain API.

    Args:
        context: BrainDevboxContext containing kubeconfig
        update_data: DevboxUpdateData containing update configuration

    Returns:
        Dictionary containing the API response

    Raises:
        requests.RequestException: If the API request fails
    """
    base_url = compose_api_url()
    if not base_url:
        raise ValueError("SEALOS_BRAIN_FRONTEND_URL environment variable is not set")

    api_url = f"{base_url}/api/sealos/devbox/{update_data.name}"

    headers = {
        "Authorization": context.kubeconfig,
        "Content-Type": "application/json",
    }

    response = requests.patch(
        api_url,
        json=update_data.model_dump(by_alias=True, exclude_none=True),
        headers=headers,
        verify=False,
    )
    response.raise_for_status()

    # Check if response has content before trying to parse JSON
    if response.text.strip():
        return response.json()
    else:
        return {"message": "Operation completed successfully", "status": "success"}


# python -m src.lib.brain.sealos.devbox.update
if __name__ == "__main__":
    # Test variables
    context = BrainDevboxContext(
        kubeconfig=os.getenv("BJA_KC", "/path/to/your/kubeconfig"),
    )

    update_data = DevboxUpdateData(
        name="my-devb",
        cpu=4,
        memory=8,
    )

    # Test the function
    try:
        result = update_devbox(context, update_data)
        print(result)
    except Exception as e:
        print(f"Error updating devbox: {e}")
