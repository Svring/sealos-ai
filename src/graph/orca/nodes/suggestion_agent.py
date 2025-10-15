"""
Suggestion node for the Orca agent.
Provides helpful suggestions based on the current context.
"""

from typing import Literal
from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from src.provider.backbone_provider import get_sealos_model
from src.utils.context_utils import get_state_values
from src.utils.error_utils import extract_error_type_and_construct_message
from src.graph.orca.state import OrcaState, SuggestionOutput
import json


async def suggestion_agent(
    state: OrcaState, config: RunnableConfig
) -> Command[Literal["__end__"]]:
    """
    Suggestion agent that provides helpful suggestions based on the current context.
    Returns structured data with a list of suggestions.
    """
    try:
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

        model = get_sealos_model(
            base_url=base_url, api_key=api_key, model_name=model_name
        )

        # Configure model with structured output
        model_with_structured_output = model.with_structured_output(SuggestionOutput)

        # Build system message for suggestions
        system_message = SystemMessage(
            content="""You are a suggestion agent that works as an extension of a working AI chat system. Your role is to analyze the chat history and provide specific, actionable suggestions based on the latest AI messages.

CONTEXT:
- You are part of an AI chat system that helps users manage Sealos projects and resources
- Focus primarily on the latest AI messages in the conversation history
- Generate suggestions that would be natural follow-up actions or clarifications for the AI's responses

IMPORTANT RULES:
1. Only provide 1-2 suggestions maximum
2. Base suggestions on the latest AI messages, especially what the AI just explained or offered
3. Suggestions must be CONCRETE and SPECIFIC - no vague suggestions like "Create a new resource (e.g., another DevBox or a database)"
4. Suggestions will be used as subsequent messages sent on the user's behalf, so they must be:
   - Clear and unambiguous
   - Short and concise (preferably 2-5 words)
   - Ready to send as-is
5. If the latest AI message doesn't warrant suggestions, return an empty list

EXAMPLES OF GOOD SUGGESTIONS:
- If AI explains resource management capabilities → suggest "create nextjs devbox" or "show project resources"
- If AI offers to help with specific operations → suggest the most relevant operation like "create postgres database"
- If AI provides technical information → suggest practical next steps like "deploy application"
- If AI lists available options → suggest the most useful option like "start devbox"

EXAMPLES OF BAD SUGGESTIONS (too vague):
- "Create a new resource (e.g., another DevBox or a database)" ❌
- "Set up monitoring and logging" ❌
- "Consider implementing best practices" ❌

COMMON CASES WHERE NO SUGGESTIONS ARE NEEDED:
- Simple confirmations or acknowledgments
- Error messages or technical failures
- Greetings or basic questions
- When the AI message is already complete and self-contained

Each suggestion should be concise, specific, and directly actionable. Focus on what the user would naturally want to do next based on what the AI just told them."""
        )

        # Build message list
        message_list = [system_message]

        # Add existing messages from state
        if messages:
            message_list.extend(messages)

        # Get structured response
        response = await model_with_structured_output.ainvoke(message_list)

        # Convert to JSON string
        json_response = json.dumps(response.model_dump(), indent=2)

        return Command(
            goto="__end__",
            update={"messages": AIMessage(content=json_response)},
        )

    except Exception as e:
        # Handle any errors that occur during suggestion processing
        error_str = str(e)
        structured_error_message = extract_error_type_and_construct_message(error_str)
        return Command(
            goto="__end__",
            update={"messages": AIMessage(content=structured_error_message)},
        )
