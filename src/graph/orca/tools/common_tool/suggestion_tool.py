"""
Suggestion tool for returning suggestions directly.
Takes suggestions as parameters and returns them in a structured format.
"""

from langchain_core.tools import tool, InjectedToolCallId
from typing import List, Dict, Any
from langgraph.types import Command
from typing_extensions import Annotated
from langchain_core.messages import ToolMessage

import json


@tool
def suggestion_tool(
    suggestions: List[str], tool_call_id: Annotated[str, InjectedToolCallId]
) -> Dict[str, Any]:
    """
    Provide specific, actionable suggestions for subsequent actions that the user can take.

    This tool should be called proactively when user requests are unclear or when you want to offer
    creative but concrete next steps. Use this tool to offer concrete, specific next steps that would
    be natural follow-up actions based on the current conversation context. When user requests are
    ambiguous, use this tool to offer creative but specific suggestions rather than asking for clarification.

    IMPORTANT RULES:
    1. Only provide 1-2 suggestions maximum
    2. Base suggestions on the current conversation context, especially what you just explained or offered
    3. Suggestions must be CONCRETE and SPECIFIC - no vague suggestions like "Create a new resource (e.g., another DevBox or a database)"
    4. Suggestions will be used as subsequent messages sent on the user's behalf, so they must be:
       - Clear and unambiguous
       - Concise but descriptive (less than 15 words)
       - Ready to send as-is
    5. Use this tool proactively when user requests are unclear - offer creative but concrete suggestions instead of asking for clarification
    6. If the current context doesn't warrant suggestions, don't call this tool

    EXAMPLES OF GOOD SUGGESTIONS:
    - If you explain resource management capabilities → suggest "create nextjs devbox" or "show project resources"
    - If you offer to help with specific operations → suggest the most relevant operation like "create postgres database"
    - If you provide technical information → suggest practical next steps like "deploy application"
    - If you list available options → suggest the most useful option like "start devbox"

    EXAMPLES OF BAD SUGGESTIONS (too vague):
    - "Create a new resource (e.g., another DevBox or a database)" ❌
    - "Set up monitoring and logging" ❌
    - "Consider implementing best practices" ❌

    COMMON CASES WHERE NO SUGGESTIONS ARE NEEDED:
    - Simple confirmations or acknowledgments
    - Error messages or technical failures
    - Greetings or basic questions
    - When your response is already complete and self-contained

    Args:
        suggestions (List[str]): List of 1-2 concrete, specific suggestion strings.
            Each suggestion should be a clear, actionable statement that the user
            can send as their next message. Keep suggestions concise but descriptive (less than 15 words).

    Returns:
        Dict containing the action and payload for suggestions
    """
    tool_message = ToolMessage(
        content=json.dumps(
            {
                "action": "suggestion",
                "payload": {
                    "suggestions": suggestions,
                },
            }
        ),
        tool_call_id=tool_call_id,
    )
    return Command(
        goto="__end__",
        update={"messages": [tool_message]},
    )
