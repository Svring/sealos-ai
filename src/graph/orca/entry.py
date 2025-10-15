"""
Simple entry node that routes based on stage to propose_project or manage_project.
"""

from typing import Literal
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from src.utils.context_utils import get_state_values
from src.graph.orca.state import OrcaState


async def entry_node(state: OrcaState, config: RunnableConfig) -> Command[
    Literal[
        # "propose_project_agent",
        "manage_project_agent",
        "manage_resource_agent",
        "deploy_project_agent",
        "suggestion_agent",
        "append_node",
        "__end__",
    ]
]:
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

    # print(f"Stage: {stage}")

    # Route based on stage
    if stage == "propose_project":
        return Command(goto="deploy_project_agent")
    elif stage == "manage_project":
        return Command(goto="manage_project_agent")
    elif stage == "manage_resource":
        return Command(goto="manage_resource_agent")
    elif stage == "deploy_project":
        return Command(goto="deploy_project_agent")
    elif stage == "suggestion":
        return Command(goto="suggestion_agent")
    elif stage == "append":
        return Command(goto="append_node")
    else:
        # Default fallback
        return Command(
            goto="__end__",
            update={
                "messages": AIMessage(
                    content="Invalid stage. Please set stage to 'propose_project', 'manage_project', 'manage_resource', 'deploy_project', 'suggestion', or 'append'."
                )
            },
        )
