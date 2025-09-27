"""
Context utilities for extracting values from config and state objects.
"""

from typing import Any, Dict, List, Union
from langchain_core.runnables import RunnableConfig


def get_config_value(config: RunnableConfig, key: str, default: Any = None) -> Any:
    """
    Extract a value from the config's configurable section.

    Args:
        config: The RunnableConfig object
        key: The key to extract from configurable
        default: Default value if key is not found

    Returns:
        The value associated with the key, or default if not found
    """
    return config.get("configurable", {}).get(key, default)


def get_config_values(
    config: RunnableConfig, keys: Union[List[str], Dict[str, Any]]
) -> tuple:
    """
    Extract multiple values from the config's configurable section.

    Args:
        config: The RunnableConfig object
        keys: Either a list of keys or a dict mapping keys to default values

    Returns:
        Tuple of values in the same order as provided keys
    """
    if isinstance(keys, list):
        return tuple(get_config_value(config, key) for key in keys)
    elif isinstance(keys, dict):
        return tuple(
            get_config_value(config, key, default) for key, default in keys.items()
        )
    else:
        raise ValueError("keys must be either a list or a dict")


def get_state_value(state: dict, key: str, default: Any = None) -> Any:
    """
    Extract a value from the state object.

    Args:
        state: The CopilotKitState object
        key: The key to extract from state
        default: Default value if key is not found

    Returns:
        The value associated with the key, or default if not found
    """
    return state.get(key, default)


def get_state_values(state: dict, keys: Union[List[str], Dict[str, Any]]) -> tuple:
    """
    Extract multiple values from the state object.

    Args:
        state: The CopilotKitState object
        keys: Either a list of keys or a dict mapping keys to default values

    Returns:
        Tuple of values in the same order as provided keys
    """
    if isinstance(keys, list):
        return tuple(get_state_value(state, key) for key in keys)
    elif isinstance(keys, dict):
        return tuple(
            get_state_value(state, key, default) for key, default in keys.items()
        )
    else:
        raise ValueError("keys must be either a list or a dict")


def get_copilot_actions(state: dict) -> list:
    """
    Extract CopilotKit actions from state.

    Args:
        state: The CopilotKitState object

    Returns:
        List of CopilotKit actions, or empty list if not found
    """
    copilotkit = get_state_value(state, "copilotkit", {})
    return copilotkit.get("actions", [])


def has_copilot_actions(state: dict) -> bool:
    """
    Check if state has CopilotKit actions.

    Args:
        state: The CopilotKitState object

    Returns:
        True if CopilotKit actions exist, False otherwise
    """
    return bool(get_copilot_actions(state))
