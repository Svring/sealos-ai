"""
Error handling utilities for the Orca agent system.
Provides functions for extracting error types and constructing structured error messages.
"""

import json
import re


def extract_error_type_and_construct_message(error_str: str) -> str:
    """
    Extract error type from error message and construct structured system message.

    Args:
        error_str: The original error message string

    Returns:
        Stringified JSON with structured error information
    """
    error_type = "unknown_error"

    # Try to extract error type from JSON-like error messages
    # Pattern: "type": "error_type_name"
    type_match = re.search(r'"type":\s*"([^"]+)"', error_str)
    if type_match:
        error_type = type_match.group(1)

    # Construct structured message
    structured_message = {
        "type": "universal.error",
        "payload": {"type": error_type, "error": error_str},
    }

    return json.dumps(structured_message)
