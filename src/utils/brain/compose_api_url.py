"""
Brain API URL composition utilities.
Handles reading and returning the SEALOS_BRAIN_FRONTEND_URL environment variable.
"""

import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()


def compose_api_url() -> Optional[str]:
    """
    Read the SEALOS_BRAIN_FRONTEND_URL environment variable and return it.

    Returns:
        Optional[str]: The value of SEALOS_BRAIN_FRONTEND_URL environment variable,
                      or None if not set.
    """
    return os.getenv("SEALOS_BRAIN_FRONTEND_URL")


# python -m src.utils.brain.compose_api_url
if __name__ == "__main__":
    # Test the function
    url = compose_api_url()
    if url:
        print(f"✅ SEALOS_BRAIN_FRONTEND_URL: {url}")
    else:
        print("❌ SEALOS_BRAIN_FRONTEND_URL environment variable is not set")
