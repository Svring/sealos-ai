"""
Sealos Agent - A CopilotKit agent for Sealos operations.
It defines the workflow graph, state, tools, nodes and edges.
"""

# python -m src.agent.sealos_agent
from typing_extensions import Literal

from copilotkit import CopilotKitState

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.types import Command
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt
from langgraph.runtime import Runtime
from langchain_tavily import TavilySearch

from src.provider.backbone_provider import get_sealos_model
from src.utils.context_utils import (
    get_state_values,
    get_copilot_actions,
    has_copilot_actions,
)


class SealosAIState(CopilotKitState):
    """
    Sealos AI State

    Inherits from CopilotKitState and adds Sealos-specific fields.
    """

    base_url: str
    api_key: str
    model: str


tool = TavilySearch(max_results=2)
tools = [tool]


async def sealos_ai_node(
    state: SealosAIState,
) -> Command[Literal["tool_node", "__end__"]]:
    """
    Optimized chat node based on the ReAct design pattern.
    Handles model binding, system prompts, Sealos context, and tool calls.
    """
    # Extract state data
    (
        messages,
        base_url,
        api_key,
        model,
    ) = get_state_values(
        state,
        {
            "messages": [],
            "base_url": None,
            "api_key": None,
            "model": None,
        },
    )

    model = get_sealos_model(model, base_url, api_key)

    all_tools = tools + get_copilot_actions(state)

    model_with_tools = model.bind_tools(all_tools, parallel_tool_calls=False)

    # Build messages with system prompt and optional Sealos data
    messages.append(
        SystemMessage(
            content="you are sealos brain. You are here to help create and manage sealos projects. You can help with creating new projects, deploying templates, and importing github repos. you can create devbox for development and clusters for storing data, based on the request of the user."
        )
    )

    # Get model response
    response = await model_with_tools.ainvoke(messages)

    # Handle tool calls
    # if isinstance(response, AIMessage) and response.tool_calls:
    #     # Check if it's a copilot action
    #     is_copilot_action = any(
    #         action.get("name") == response.tool_calls[0].get("name")
    #         for action in get_copilot_actions(state)
    #     )

    #     if is_copilot_action:
    #         # For copilot actions, request approval
    #         tool_call_name = response.tool_calls[0].get("name")
    #         # this line prevents a bug: resumption of a tool call would trigger the same tool call again, which causes two identical tool call messages followed by the tool result, setting the response to [] neutralizes the initial tool call
    #         # note added later: resumption from interruption reexecutes the node again, which causes the code before the interruption run again, this is possibly the cause of the double tool call, but I still can't locate where did the copilotkit on frontend take the parameters and execute the tool call, obviously not in the langgraph backend since there is no 'copilotkit node' to execute the tool call.
    #         # response = []
    #         # state["approval"] = interrupt(
    #         #     {
    #         #         "type": "approval",
    #         #         "content": "please approve the action " + tool_call_name,
    #         #     }
    #         # )
    #         # if state["approval"] == "false":
    #         #     return Command(
    #         #         goto="__end__",
    #         #         update={
    #         #             "messages": HumanMessage(content="User rejected the action")
    #         #         },
    #         #     )
    #     else:
    #         # Route to tool_node for non-CopilotKit tools
    #         # return Command(goto="tool_node", update={"messages": response})
    #         pass

    return Command(goto="__end__", update={"messages": response})


# Define the workflow graph
workflow = StateGraph(SealosAIState)
workflow.add_node("sealos_ai_node", sealos_ai_node)
workflow.add_node("tool_node", ToolNode(tools=tools))
workflow.add_edge("tool_node", "sealos_ai_node")
workflow.set_entry_point("sealos_ai_node")

# Compile the workflow graph
graph = workflow.compile()
