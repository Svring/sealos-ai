"""
Graph assembly for the Brain agent.
"""

from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from src.graph.brain.state import BrainState
from src.graph.brain.nodes import (
    entry_node,
    project_agent,
    resource_agent,
    tools,
)


def build_graph():
    workflow = StateGraph(BrainState)

    # Add nodes
    workflow.add_node("entry_node", entry_node)
    workflow.add_node("project_agent", project_agent)
    workflow.add_node("resource_agent", resource_agent)
    workflow.add_node("tool_node", ToolNode(tools=tools))

    # Add edges
    workflow.add_edge("tool_node", "resource_agent")

    # Set entry point
    workflow.set_entry_point("entry_node")

    return workflow.compile()


graph = build_graph()
