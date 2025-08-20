"""
Simple entry node that routes based on stage to propose_project or manage_project.
"""

from typing import Literal
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from src.utils.context_utils import get_state_values
from src.graph.orca.state import OrcaState


async def entry_node(
    state: OrcaState, config: RunnableConfig
) -> Command[Literal["propose_project_agent", "manage_project_agent", "__end__"]]:
    """
    Entry node that routes based on stage.
    """
    # Extract state variables
    (stage,) = get_state_values(
        state,
        {
            "stage": None,
        },
    )

    # Route based on stage
    if stage == "propose_project":
        return Command(goto="propose_project_agent")
    elif stage == "manage_project":
        return Command(goto="manage_project_agent")
    else:
        # Default fallback
        return Command(
            goto="__end__",
            update={
                "messages": AIMessage(
                    content="Invalid stage. Please set stage to 'propose_project' or 'manage_project'."
                )
            },
        )
