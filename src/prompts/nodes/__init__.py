"""
Node-specific prompts package for the Sealos Brain agent.
"""

# Entry node prompts
from .entry_node_prompts import (
    ROUTE_ONLY_EXISTING_PROJECT_PROMPT,
    ROUTE_ONLY_NEW_PROJECT_PROMPT,
    GREETING_MESSAGE_PROMPT,
    EXISTING_PROJECT_PLAN_TEMPLATE,
    build_routing_prompt_existing_project,
    build_routing_prompt_new_project,
)

# Compose project brief prompts
from .compose_project_brief_prompts import (
    PROJECT_BRIEF_GENERATION_PROMPT,
    PROJECT_BRIEF_MODIFICATION_PROMPT,
)

# Compose new project prompts
from .compose_new_project_prompts import (
    COMPOSE_NEW_PROJECT_PROMPT,
)

# Summarize project prompts
from .summarize_project_prompts import (
    SUMMARIZE_PROJECT_PROMPT,
)

# Manage resource prompts
from .manage_resource_prompts import (
    MANAGE_RESOURCE_PROMPT,
)

__all__ = [
    # Entry node
    "ROUTE_ONLY_EXISTING_PROJECT_PROMPT",
    "ROUTE_ONLY_NEW_PROJECT_PROMPT",
    "GREETING_MESSAGE_PROMPT",
    "EXISTING_PROJECT_PLAN_TEMPLATE",
    "build_routing_prompt_existing_project",
    "build_routing_prompt_new_project",
    # Compose project brief
    "PROJECT_BRIEF_GENERATION_PROMPT",
    "PROJECT_BRIEF_MODIFICATION_PROMPT",
    # Compose new project
    "COMPOSE_NEW_PROJECT_PROMPT",
    # Summarize project
    "SUMMARIZE_PROJECT_PROMPT",
    # Manage resource
    "MANAGE_RESOURCE_PROMPT",
]
