"""
Project proposal node for the Orca agent.
Handles project proposal generation with tools and actions.
"""

from typing import Annotated, Literal
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage
from langgraph.prebuilt import InjectedState
from langchain_core.runnables import RunnableConfig
from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import Command
from langchain_core.tools import tool

from src.provider.backbone_provider import get_sealos_model
from src.utils.context_utils import get_state_values
from src.graph.orca.state import OrcaState, ProjectProposal
from copilotkit.langgraph import copilotkit_customize_config


from src.graph.orca.prompts.propose_project_prompt import (
    PROPOSE_PROJECT_PROMPT,
    PROPOSE_PROJECT_REQUIREMENT_PROMPT,
)


@tool
async def propose_project(
    requirement: str,
    state: Annotated[OrcaState, InjectedState],
    config: RunnableConfig,
) -> ProjectProposal:
    """
    Generate a structured project proposal based on user requirements.

    Args:
        requirement: The user's project requirements and goals
        config: The runnable configuration

    Returns:
        ProjectProposal: A structured project proposal with name, description, and resources
    """
    # Extract state data
    (
        messages,
        base_url,
        api_key,
        model_name,
    ) = get_state_values(
        state,
        {
            "messages": [],
            "base_url": None,
            "api_key": None,
            "model_name": None,
        },
    )
    # print("base_url in propose_project tool", base_url)
    # print("api_key in propose_project tool", api_key)
    # print("model_name in propose_project tool", model_name)
    # Get model and create structured output
    model = get_sealos_model(base_url=base_url, api_key=api_key)
    structured_model = model.with_structured_output(ProjectProposal)

    # Create the message list with system prompt and requirement
    message_list = [
        SystemMessage(content=PROPOSE_PROJECT_PROMPT),
    ]

    if messages:
        message_list.extend(messages[:-1])

    # Generate project plan
    project_plan: ProjectProposal = await structured_model.ainvoke(message_list)

    return project_plan.model_dump()


async def propose_project_agent(
    state: OrcaState, config: RunnableConfig
) -> Command[Literal["propose_tool_node", "__end__"]]:
    """
    Project proposal agent based on the Sealos AI functionality.
    Handles model binding, system prompts, and tool calls.
    """
    # print("state in propose_project_agent", state)
    # Extract state data
    (
        messages,
        base_url,
        api_key,
        model_name,
    ) = get_state_values(
        state,
        {
            "messages": [],
            "base_url": None,
            "api_key": None,
            "model_name": None,
        },
    )

    # print("base_url", base_url)
    # print("api_key", api_key)
    # print("model_name", model_name)

    # print("messages", messages)

    model = get_sealos_model(base_url=base_url, api_key=api_key, model_name=model_name)

    # Get copilot actions and add the propose_project tool
    model_with_tools = model.bind_tools([propose_project], parallel_tool_calls=False)

    # print("model_with_tools", model_with_tools)

    # Build messages with system prompt for project proposal
    # prompt = ChatPromptTemplate.from_messages(
    #     [
    #         SystemMessage(content=PROPOSE_PROJECT_REQUIREMENT_PROMPT),
    #         HumanMessage(content="{input}"),
    #     ]
    # )

    # chain = prompt | model_with_tools

    # Create the message list with system prompt and existing messages
    message_list = [
        SystemMessage(content=PROPOSE_PROJECT_REQUIREMENT_PROMPT),
    ]

    # Add existing messages from state
    if messages:
        message_list.extend(messages)

    # print("message_list", message_list)

    # Get model response
    response = await model_with_tools.ainvoke(message_list)

    # print("response", response)

    # Check if the response contains tool calls
    if hasattr(response, "tool_calls") and response.tool_calls:
        print("response has tool calls", response.tool_calls)
        return Command(goto="propose_tool_node", update={"messages": response})
    else:
        return Command(
            goto="__end__",
            update={"messages": response},
        )
