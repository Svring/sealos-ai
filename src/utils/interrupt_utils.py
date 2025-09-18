"""
Utility functions for handling interrupts in resource management tools.
"""

import json
from typing import Dict, Any, Optional


def handle_interrupt_with_approval(
    action: str,
    payload: Dict[str, Any],
    interrupt_func,
    original_params: Dict[str, Any],
) -> tuple[bool, Dict[str, Any], Dict[str, Any]]:
    """
    Handle interrupt with approval and parameter editing.

    Args:
        action: The action name (e.g., "update_devbox")
        payload: The original payload to send to interrupt
        interrupt_func: The interrupt function to call
        original_params: Dictionary of original parameter values for fallback

    Returns:
        Tuple of (is_approved, edited_data, response_payload)
        - is_approved: Boolean indicating if operation was approved
        - edited_data: Dictionary of edited parameters
        - response_payload: The payload to return in response
    """
    # Call interrupt with the action and payload
    edited_payload_str = interrupt_func(
        {
            "action": action,
            "payload": payload,
        }
    )

    # Parse the stringified JSON response
    try:
        edited_payload = (
            json.loads(edited_payload_str)
            if isinstance(edited_payload_str, str)
            else edited_payload_str
        )
    except (json.JSONDecodeError, TypeError):
        edited_payload = {"approve": False, "payload": {}}

    # Check if the operation was approved
    is_approved = edited_payload.get("approve", False)

    # Extract the edited parameters from the approved payload
    edited_data = edited_payload.get("payload", {})

    # Create response payload with edited data
    response_payload = edited_data.copy()

    # If not approved, return early
    if not is_approved:
        return False, edited_data, response_payload

    # Update original parameters with edited values (with fallback to original)
    for key, original_value in original_params.items():
        if key in edited_data:
            # Use edited value if provided
            original_params[key] = edited_data[key]
        else:
            # Keep original value if not edited
            original_params[key] = original_value

    return True, edited_data, response_payload


def create_rejection_response(
    action: str,
    response_payload: Dict[str, Any],
    resource_name: str,
    operation_type: str,
) -> Dict[str, Any]:
    """
    Create a standardized rejection response.

    Args:
        action: The action name
        response_payload: The payload to return
        resource_name: Name of the resource
        operation_type: Type of operation (e.g., "Update", "Start", "Pause", "Delete")

    Returns:
        Dictionary containing the rejection response
    """
    return {
        "action": action,
        "payload": response_payload,
        "success": False,
        "error": "Operation rejected by user",
        "message": f"{operation_type} operation for {resource_name} '{resource_name}' was rejected by user",
    }
