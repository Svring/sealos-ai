"""
Graph assembly for the Orca agent.
"""

from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from src.graph.orca.state import OrcaState
from src.graph.orca.entry import entry_node
from src.graph.orca.nodes.manage_project_agent import (
    manage_project_agent,
    tools as manage_tools,
)
from src.graph.orca.nodes.manage_resource_agent import (
    manage_resource_agent,
    tools as manage_resource_tools,
)
from src.graph.orca.nodes.deploy_project_agent import deploy_project_agent
from src.graph.orca.nodes.suggestion_agent import suggestion_agent
from src.graph.orca.tools.deploy_project_tool import deploy_project_tools
from src.graph.orca.append import append_node
from src.graph.orca.edges.tool_edge import (
    manage_project_tool_edge,
    manage_resource_tool_edge,
    deploy_project_tool_edge,
)


def build_graph():
    workflow = StateGraph(OrcaState)

    # Add nodes
    workflow.add_node("entry_node", entry_node)
    # workflow.add_node("propose_project_agent", propose_project_agent)
    workflow.add_node("manage_project_agent", manage_project_agent)
    workflow.add_node("manage_resource_agent", manage_resource_agent)
    workflow.add_node("deploy_project_agent", deploy_project_agent)
    workflow.add_node("suggestion_agent", suggestion_agent)
    workflow.add_node("append_node", append_node)

    workflow.add_node("manage_project_tool_node", ToolNode(tools=manage_tools))
    workflow.add_node(
        "manage_resource_tool_node", ToolNode(tools=manage_resource_tools)
    )
    # workflow.add_node("propose_project_tool_node", ToolNode(tools=[propose_project]))

    workflow.add_node("deploy_project_tool_node", ToolNode(tools=deploy_project_tools))

    # Add edges with conditional routing
    workflow.add_conditional_edges(
        "manage_project_tool_node",
        manage_project_tool_edge,
        {
            "manage_project_agent": "manage_project_agent",
            "__end__": "__end__",
        },
    )
    workflow.add_conditional_edges(
        "manage_resource_tool_node",
        manage_resource_tool_edge,
        {
            "manage_resource_agent": "manage_resource_agent",
            "__end__": "__end__",
        },
    )
    workflow.add_conditional_edges(
        "deploy_project_tool_node",
        deploy_project_tool_edge,
        {
            "deploy_project_agent": "deploy_project_agent",
            "__end__": "__end__",
        },
    )
    # workflow.add_edge("propose_project_tool_node", "propose_project_agent")

    # Set entry point
    workflow.set_entry_point("entry_node")

    return workflow.compile()


graph = build_graph()
