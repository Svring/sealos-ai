"""
Tools for the propose project agent.
Contains the propose_project tool for generating project proposals.
"""

from typing import Dict, Any
from langchain_core.tools import tool

from src.graph.orca.state import ProjectProposal


@tool
async def propose_project(project_proposal: ProjectProposal) -> Dict[str, Any]:
    """
    Generate a structured project proposal based on user requirements.

    Args:
        project_proposal: The structured project proposal with name, description, and resources

    Returns:
        Dict containing the action and payload with the project proposal
    """
    return {
        "action": "propose_project",
        "payload": {
            "project_proposal": project_proposal.model_dump(),
        },
    }
