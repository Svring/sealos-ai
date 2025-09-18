"""
Graph assembly for the Orca agent.
"""

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.graph.orca.state import OrcaState
from src.graph.orca.entry import entry_node
from src.graph.orca.manage_project_agent import (
    manage_project_agent,
    tools as manage_tools,
)
from src.graph.orca.manage_resource_agent import (
    manage_resource_agent,
    tools as manage_resource_tools,
)
from src.graph.orca.propose_project_agent import propose_project_agent
from src.graph.orca.tools.propose_project_tools import propose_project
from src.graph.orca.deploy_project_agent import deploy_project_agent
from src.graph.orca.tools.deploy_project_tool import deploy_project_tools


def build_graph():
    workflow = StateGraph(OrcaState)

    # Add nodes
    workflow.add_node("entry_node", entry_node)
    workflow.add_node("propose_project_agent", propose_project_agent)
    workflow.add_node("manage_project_agent", manage_project_agent)
    workflow.add_node("manage_resource_agent", manage_resource_agent)
    workflow.add_node("deploy_project_agent", deploy_project_agent)

    workflow.add_node("manage_tool_node", ToolNode(tools=manage_tools))
    workflow.add_node(
        "manage_resource_tool_node", ToolNode(tools=manage_resource_tools)
    )
    workflow.add_node("propose_tool_node", ToolNode(tools=[propose_project]))

    workflow.add_node("deploy_tool_node", ToolNode(tools=deploy_project_tools))

    # Add edges
    workflow.add_edge("manage_tool_node", END)
    workflow.add_edge("manage_resource_tool_node", END)
    workflow.add_edge("propose_tool_node", END)
    workflow.add_edge("deploy_tool_node", "deploy_project_agent")

    # Set entry point
    workflow.set_entry_point("entry_node")

    return workflow.compile()


graph = build_graph()
