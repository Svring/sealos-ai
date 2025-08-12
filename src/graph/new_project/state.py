"""
State definitions for the New Project agent.
"""

from typing_extensions import TypedDict
from copilotkit import CopilotKitState

from .schemas import ProjectInfo


class SealosAIState(CopilotKitState):
    """
    Sealos Brain/New Project State

    Inherits from CopilotKitState and adds Sealos-specific fields.
    """

    base_url: str
    api_key: str
    model: str

    project: ProjectInfo
    project_brief: str
