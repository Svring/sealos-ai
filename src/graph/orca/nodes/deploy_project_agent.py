"""
Project deployment node for the Orca agent.
Handles project deployment operations with tools and actions.
"""

import os
from typing import Literal
from langchain_core.messages import SystemMessage
from langgraph.types import Command
from dotenv import load_dotenv

from src.provider.backbone_provider import get_sealos_model
from src.utils.context_utils import get_state_values
from src.utils.error_utils import extract_error_type_and_construct_message
from src.graph.orca.state import OrcaState
from src.graph.orca.prompts.deploy_project_prompt import DEPLOY_PROJECT_PROMPT
from src.graph.orca.tools.deploy_project_tool import (
    deploy_project_tools,
)

load_dotenv()


async def deploy_project_agent(
    state: OrcaState,
) -> Command[Literal["deploy_project_tool_node", "__end__"]]:
    """
    Project deployment agent based on the Sealos AI functionality.
    Handles model binding, system prompts, and deployment tool calls.
    """
    try:
        # Extract state data
        (
            messages,
            base_url,
            api_key,
            model_name,
            trial,
        ) = get_state_values(
            state,
            {
                "messages": [],
                "base_url": None,
                "api_key": None,
                "model_name": None,
                "trial": False,
            },
        )

        # Use TRIAL_API_KEY and TRIAL_BASE_URL if trial is true, otherwise use the provided values
        if trial:
            effective_api_key = os.getenv("TRIAL_API_KEY")
            effective_base_url = os.getenv("TRIAL_BASE_URL")
            # If trial, use TRIAL_BASE_URL and TRIAL_API_KEY
            model = get_sealos_model(
                base_url=effective_base_url, api_key=effective_api_key
            )
        else:
            effective_api_key = api_key
            effective_base_url = base_url
            # If not trial, pass all parameters
            model = get_sealos_model(
                base_url=effective_base_url,
                api_key=effective_api_key,
                model_name=model_name,
            )

        model_with_tools = model.bind_tools(deploy_project_tools)

        # Build system message for project deployment
        system_message = SystemMessage(content=DEPLOY_PROJECT_PROMPT)

        # Build message list
        message_list = [system_message]

        # Add existing messages from state
        if messages:
            message_list.extend(messages)

        # Get model response
        response = await model_with_tools.ainvoke(message_list)

        # Check if the response contains tool calls
        if hasattr(response, "tool_calls") and response.tool_calls:
            return Command(
                goto="deploy_project_tool_node", update={"messages": response}
            )
        else:
            return Command(
                goto="__end__",
                update={"messages": response},
            )

    except Exception as e:
        # Handle any errors that occur during deployment processing
        error_str = str(e)
        structured_error_message = extract_error_type_and_construct_message(error_str)
        return Command(
            goto="__end__",
            update={"messages": SystemMessage(content=structured_error_message)},
        )
