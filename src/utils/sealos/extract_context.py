"""
Utility functions for extracting context from state for Sealos operations.
"""

from typing import Dict, Any, TypeVar, Type
from typing_extensions import Annotated
from langgraph.prebuilt import InjectedState

from src.utils.context_utils import get_state_values
from src.models.sealos.devbox.devbox_model import DevboxContext
from src.models.sealos.cluster.cluster_model import ClusterContext
from src.models.sealos.launchpad.launchpad_model import LaunchpadContext

T = TypeVar("T", DevboxContext, ClusterContext, LaunchpadContext)


def extract_sealos_context(
    state: Annotated[dict, InjectedState], context_class: Type[T]
) -> T:
    """
    Extract region_url and kubeconfig from state and create a context object.

    Args:
        state: State containing the region_url and kubeconfig
        context_class: The context class to instantiate (DevboxContext, ClusterContext, or LaunchpadContext)

    Returns:
        Context object of the specified type

    Raises:
        ValueError: If required state values are missing
    """
    # Extract state data from config
    (
        region_url,
        kubeconfig,
    ) = get_state_values(
        state,
        {
            "region_url": None,
            "kubeconfig": None,
        },
    )

    if not region_url:
        raise ValueError("region_url is required in state")
    if not kubeconfig:
        raise ValueError("kubeconfig is required in state")

    # Create context object
    return context_class(
        kubeconfig=kubeconfig,
        regionUrl=region_url,
    )
