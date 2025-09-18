"""
Append node that simply goes to end and updates messages from state.
"""

from typing import Literal
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from src.utils.context_utils import get_state_values
from src.graph.orca.state import OrcaState


async def append_node(
    state: OrcaState, config: RunnableConfig
) -> Command[Literal["__end__"]]:
    """
    Append node that goes to end and updates messages from state.
    """
    # Extract messages from state
    (messages,) = get_state_values(
        state,
        {
            "messages": [],
        },
    )

    # Go to end and update messages
    return Command(
        goto="__end__",
        update={"messages": messages},
    )
