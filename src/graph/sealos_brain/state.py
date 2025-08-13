"""
State definitions for the New Project agent.
"""

from typing import Any
from copilotkit import CopilotKitState

from src.graph.sealos_brain.schemas import ProjectBrief, ProjectPlanWithStatus


class SealosBrainState(CopilotKitState):
    """
    Sealos Brain State

    Inherits from CopilotKitState and adds Sealos-specific fields.
    """

    base_url: str
    api_key: str
    model: str

    project_context: Any

    project_plan: ProjectPlanWithStatus
    project_brief: ProjectBrief
