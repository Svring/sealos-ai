"""
Graph assembly for the Orca agent.
"""

from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from src.graph.orca.state import OrcaState
from src.graph.orca.entry import entry_node
from src.graph.orca.manage_project_agent import (
    manage_project_agent,
    tools as manage_tools,
)
from src.graph.orca.propose_project_agent import propose_project_agent, propose_project


def build_graph():
    workflow = StateGraph(OrcaState)

    # Add nodes
    workflow.add_node("entry_node", entry_node)
    workflow.add_node("propose_project_agent", propose_project_agent)
    workflow.add_node("manage_project_agent", manage_project_agent)
    workflow.add_node("manage_tool_node", ToolNode(tools=manage_tools))
    workflow.add_node("propose_tool_node", ToolNode(tools=[propose_project]))

    # Add edges
    workflow.add_edge("manage_tool_node", "manage_project_agent")
    workflow.add_edge("propose_tool_node", "propose_project_agent")

    # Set entry point
    workflow.set_entry_point("entry_node")

    return workflow.compile()


graph = build_graph()
