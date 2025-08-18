"""
Graph assembly for the New Project agent.
"""

from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from src.graph.sealos_brain.state import SealosBrainState
from src.graph.sealos_brain.nodes import (
    entry_node,
    compose_new_project,
    manage_resource,
    tools,
)


def build_graph():
    workflow = StateGraph(SealosBrainState)
    workflow.add_node("entry_node", entry_node)
    workflow.add_node("compose_new_project", compose_new_project)
    workflow.add_node("manage_resource", manage_resource)
    workflow.add_node("tool_node", ToolNode(tools=tools))

    # Existing edges

    # New edges for resource management
    workflow.add_edge("tool_node", "manage_resource")

    workflow.set_entry_point("entry_node")
    return workflow.compile()


graph = build_graph()
