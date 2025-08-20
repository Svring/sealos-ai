"""
Simple entry node that extracts variables from state and determines stage.
"""

from typing import Literal
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from pydantic import BaseModel

from src.provider.backbone_provider import get_sealos_model
from src.utils.context_utils import get_state_values
from src.graph.brain.state import BrainState

from copilotkit.langgraph import (
    copilotkit_customize_config,
)


# System prompt for project routing decision
PROJECT_ROUTING_PROMPT = """You are determining whether to route to the project agent or respond directly.

Analyze the user's latest message to determine if they want to:

- TRUE: User wants to create, modify, or plan a project (e.g., "build a website", "create a new app", "need a devbox", "add a database", "want a blog site", "want a chat app")
- FALSE: User is asking general questions or doesn't need project planning (e.g., "what can you do?", "hello", "how are you", general chat)

Return only TRUE or FALSE."""


class ProjectRoutingDecision(BaseModel):
    should_route_to_project: bool


async def entry_node(
    state: BrainState, config: RunnableConfig
) -> Command[Literal["project_agent", "resource_agent", "__end__"]]:
    """
    Entry node that routes based on stage and user intent.
    """
    # Extract state variables
    (
        messages,
        base_url,
        api_key,
        model_name,
        stage,
    ) = get_state_values(
        state,
        {
            "messages": [],
            "base_url": None,
            "api_key": None,
            "model": None,
            "stage": None,
        },
    )

    # If stage is "resource", directly route to resource_agent
    if stage == "resource":
        return Command(goto="resource_agent")

    # If stage is "project", call model to decide routing
    if stage == "project":
        model = get_sealos_model(model_name, base_url, api_key)
        structured_model = model.with_structured_output(ProjectRoutingDecision)

        modified_config = copilotkit_customize_config(
            config, emit_messages=False, emit_tool_calls=True
        )

        # Get routing decision as structured boolean
        routing_decision: ProjectRoutingDecision = await structured_model.ainvoke(
            [SystemMessage(content=PROJECT_ROUTING_PROMPT), *messages],
            config=modified_config,
        )

        if routing_decision.should_route_to_project:
            return Command(goto="project_agent")
        else:
            return Command(
                goto="__end__",
                update={
                    "messages": AIMessage(
                        content="Hello, if you have any project idea on your mind, please share it and I'll alocate resources for you."
                    )
                },
            )

    # Default fallback
    return Command(goto="__end__")
