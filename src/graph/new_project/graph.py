"""
Graph assembly for the New Project agent.
"""

from langgraph.graph import StateGraph

from .state import SealosAIState
from .nodes import entry_node, compose_new_project, summarize_project


def build_graph():
    workflow = StateGraph(SealosAIState)
    workflow.add_node("entry_node", entry_node)
    workflow.add_node("compose_new_project", compose_new_project)
    workflow.add_node("summarize_project", summarize_project)
    workflow.add_edge("compose_new_project", "summarize_project")
    workflow.set_entry_point("entry_node")
    return workflow.compile()


graph = build_graph()
