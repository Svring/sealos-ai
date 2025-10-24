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

    ACTIVELY CALL THIS TOOL when you identify opportunities to provide helpful suggestions to the user.
    This tool should be called proactively when user requests are unclear or when you want to offer
    creative but concrete next steps. Use this tool to offer concrete, specific next steps that would
    be natural follow-up actions based on the current conversation context. When user requests are
    ambiguous, ACTIVELY USE THIS TOOL to offer creative but specific suggestions rather than asking for clarification.

    IMPORTANT RULES:
    1. ACTIVELY CALL THIS TOOL when you identify opportunities to provide helpful suggestions
    2. Only provide 1-2 suggestions maximum
    3. Base suggestions on the current conversation context, especially what you just explained or offered
    4. **CRITICAL LANGUAGE CONSISTENCY**: Suggestions MUST match the user's current message language exactly. If the user communicates in English, provide suggestions ONLY in English. If the user communicates in Chinese, provide suggestions ONLY in Chinese. **NEVER provide Chinese suggestions following English responses or vice versa.** The suggestions language must match the response language without exception.
    5. Suggestions must be DIRECT COMMANDS with CONCRETE VALUES - not vague descriptions or recommendations
    6. Suggestions will be used as subsequent messages sent on the user's behalf, so they must be:
       - Direct commands that can be executed immediately
       - Include specific values and parameters
       - Concise but complete (less than 15 words)
       - Ready to send as-is without modification
    7. ACTIVELY USE THIS TOOL proactively when user requests are unclear - offer creative but concrete suggestions instead of asking for clarification
    8. If the current context doesn't warrant suggestions, don't call this tool
    9. NEVER finish responses without calling a tool or providing suggestions (except when you have just completed a user request like 'start devbox', 'create database', etc.)
    10. When unsure what the user wants to do next, ACTIVELY CALL THIS TOOL to guess the best next step rather than ending the response or asking questions

    EXAMPLES OF GOOD SUGGESTIONS (direct commands with concrete values):
    - "update to 2c 4g" (not "update DevBox resource if needed")
    - "create nextjs devbox" (not "create a development environment")
    - "start devbox" (not "start the development environment")
    - "add port 8080" (not "configure port settings")
    - "create postgres database" (not "set up database if needed")
    - "deploy fastapi app" (not "deploy application")
    - "add redis database" (good suggestion after proposing a web app that needs caching)
    - "add mongodb database" (good suggestion for data storage needs)
    - "deploy nginx app" (good suggestion for load balancing needs)

    EXAMPLES OF BAD SUGGESTIONS (too vague, not direct commands):
    - "Create a new resource (e.g., another DevBox or a database)" ❌
    - "Update DevBox resource if needed" ❌
    - "Set up monitoring and logging" ❌
    - "Consider implementing best practices" ❌
    - "Configure the application" ❌
    - "deploy the project" (avoid after calling propose_*_deployment tools) ❌
    - "Would you like to deploy the proposed configuration?" (avoid deployment questions) ❌
    - "configure environment variables" (belongs to manage_resource mode, not deployment) ❌
    - "modify resource allocation" (belongs to manage_resource mode, not deployment) ❌
    - "add a redis database" (NEVER suggest after propose_template_deployment or propose_image_deployment) ❌
    - "add a postgresql database" (NEVER suggest after propose_template_deployment or propose_image_deployment) ❌
    - "deploy another devbox" (NEVER suggest after propose_template_deployment or propose_image_deployment) ❌

    COMMON CASES WHERE SUGGESTIONS ARE NEEDED:
    - After analyzing monitoring data and finding performance issues (e.g., high CPU/memory usage)
    - After checking logs and identifying specific problems that have known solutions
    - After network diagnostics revealing connectivity issues with clear fixes
    - When you have concrete clues about what actions would resolve the identified problems
    - When you can provide specific, actionable next steps based on your analysis
    - When you identify problems and have solutions, instead of asking "Would you like to..." questions

    COMMON CASES WHERE NO SUGGESTIONS ARE NEEDED:
    - Simple confirmations or acknowledgments
    - Error messages or technical failures where you don't know the solution
    - Greetings or basic questions
    - When your response is already complete and self-contained
    - When you've already provided multiple suggestions that failed and have no new ideas
    - When analysis shows problems but you have no concrete solutions to suggest

    AVOID THESE PATTERNS:
    - "Would you like to update the launch command now?" → Use suggestion_tool instead
    - "Would you like to restart the app launchpad now for immediate recovery?" → Use suggestion_tool instead
    - "If needed, I can also help you update..." → Use suggestion_tool instead
    - "deploy the project..." → Avoid after calling propose_*_deployment tools since model cannot deploy projects itself
    - "Would you like to deploy the proposed project?" → Avoid deployment questions since model only proposes, doesn't deploy

    Args:
        suggestions (List[str]): List of 1-2 direct command strings with concrete values.
            Each suggestion should be a specific command that can be executed immediately
            by the user. Include specific values and parameters. Keep suggestions concise
            but complete (less than 15 words).

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
