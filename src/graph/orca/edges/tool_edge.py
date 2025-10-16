"""
Tool edges for conditional routing based on tool names.
Routes suggestion tools to __end__ and other tools back to their respective agents.
"""

from typing import Literal
from langchain_core.messages import ToolMessage


def manage_project_tool_edge(state) -> Literal["manage_project_agent", "__end__"]:
    """
    Route for manage_project_tool_node.
    If suggestion_tool was called, go to __end__.
    Otherwise, route back to manage_project_agent.
    """
    # Get the last message which should contain the tool call
    messages = state.get("messages", [])
    if not messages:
        return "manage_project_agent"

    last_message = messages[-1]

    # Check if it's a tool message (result of tool execution)
    if isinstance(last_message, ToolMessage):
        # Check if the tool call was for suggestion_tool
        if hasattr(last_message, "tool_call_id") and last_message.tool_call_id:
            # Look through messages to find the original tool call
            for msg in reversed(messages):
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        if tool_call.get("id") == last_message.tool_call_id:
                            tool_name = tool_call.get("name", "")
                            if tool_name == "suggestion_tool":
                                return "__end__"

    # Check if it's a tool call message
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        tool_name = last_message.tool_calls[0].get("name", "")
        if tool_name == "suggestion_tool":
            return "__end__"

    # Default: route back to manage_project_agent
    return "manage_project_agent"


def manage_resource_tool_edge(state) -> Literal["manage_resource_agent", "__end__"]:
    """
    Route for manage_resource_tool_node.
    If suggestion_tool was called, go to __end__.
    Otherwise, route back to manage_resource_agent.
    """
    # Get the last message which should contain the tool call
    messages = state.get("messages", [])
    if not messages:
        return "manage_resource_agent"

    last_message = messages[-1]

    # Check if it's a tool message (result of tool execution)
    if isinstance(last_message, ToolMessage):
        # Check if the tool call was for suggestion_tool
        if hasattr(last_message, "tool_call_id") and last_message.tool_call_id:
            # Look through messages to find the original tool call
            for msg in reversed(messages):
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        if tool_call.get("id") == last_message.tool_call_id:
                            tool_name = tool_call.get("name", "")
                            if tool_name == "suggestion_tool":
                                return "__end__"

    # Check if it's a tool call message
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        tool_name = last_message.tool_calls[0].get("name", "")
        if tool_name == "suggestion_tool":
            return "__end__"

    # Default: route back to manage_resource_agent
    return "manage_resource_agent"


def deploy_project_tool_edge(state) -> Literal["deploy_project_agent", "__end__"]:
    """
    Route for deploy_project_tool_node.
    If suggestion_tool was called, go to __end__.
    Otherwise, route back to deploy_project_agent.
    """
    # Get the last message which should contain the tool call
    messages = state.get("messages", [])
    if not messages:
        return "deploy_project_agent"

    last_message = messages[-1]

    # Check if it's a tool message (result of tool execution)
    if isinstance(last_message, ToolMessage):
        # Check if the tool call was for suggestion_tool
        if hasattr(last_message, "tool_call_id") and last_message.tool_call_id:
            # Look through messages to find the original tool call
            for msg in reversed(messages):
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        if tool_call.get("id") == last_message.tool_call_id:
                            tool_name = tool_call.get("name", "")
                            if tool_name == "suggestion_tool":
                                return "__end__"

    # Check if it's a tool call message
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        tool_name = last_message.tool_calls[0].get("name", "")
        if tool_name == "suggestion_tool":
            return "__end__"

    # Default: route back to deploy_project_agent
    return "deploy_project_agent"
