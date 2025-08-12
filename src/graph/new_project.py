"""
Backwards-compatible shim for the refactored New Project agent.
Keeps the old import path working while delegating to the modular implementation.
"""

from langgraph.graph import StateGraph

from src.graph.new_project.state import SealosAIState
from src.graph.new_project.nodes import (
    entry_node,
    compose_new_project,
    summarize_project,
)


# Define the workflow graph (back-compat)
workflow = StateGraph(SealosAIState)
workflow.add_node("entry_node", entry_node)
workflow.add_node("compose_new_project", compose_new_project)
workflow.add_node("summarize_project", summarize_project)
workflow.add_edge("compose_new_project", "summarize_project")
workflow.set_entry_point("entry_node")

# Compile the workflow graph
graph = workflow.compile()
