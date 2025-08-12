"""
Sealos Agent - A CopilotKit agent for Sealos operations.
It defines the workflow graph, state, tools, nodes and edges.
"""

# python -m src.agent.sealos_agent
from typing_extensions import Literal

from copilotkit import CopilotKitState

from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph
from langgraph.types import Command
from langgraph.prebuilt import ToolNode
from langchain_tavily import TavilySearch

from src.provider.backbone_provider import get_sealos_model
from src.utils.context_utils import (
    get_state_values,
    get_copilot_actions,
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
            content=(
                "You are Sealos AI, the project resource manager for the Sealos cloud platform. "
                "Your role is to manage resources INSIDE a specific project — whether that project was proposed by the New Project agent or created/imported directly by the user.\n\n"
                "What you do:\n"
                "- Understand the current project context from conversation state and metadata.\n"
                "- Create, update, scale, or remove project resources on request.\n"
                "- Change resource configurations (CPU, memory, storage, network settings, etc.).\n"
                "- Manage network configuration and connectivity between resources.\n"
                "- Proactively diagnose and fix resource faults when users report issues.\n"
                "- Recommend minimal, cost‑effective changes and briefly explain impact.\n"
                "- Ask for missing parameters before making changes (e.g., runtime, size, policy, specs).\n\n"
                "Resources you can manage:\n"
                "- DevBoxes (development environments). Common runtimes include: C++, Nuxt3, Hugo, Java, Chi, PHP, Rocket, Quarkus, Debian, Ubuntu, Spring Boot, Flask, Nginx, Vue.js, Python, VitePress, Node.js, Echo, Next.js, Angular, React, Svelte, Gin, Rust, UmiJS, Docusaurus, Hexo, Vert.x, Go, C, Iris, Astro, MCP, Django, Express.js, .Net.\n"
                "- Databases: postgresql, mongodb, apecloud-mysql, redis, kafka, weaviate, milvus, pulsar.\n"
                "- Object Storage Buckets with policies: Private, PublicRead, PublicReadwrite.\n"
                "- Network configuration: VPCs, subnets, security groups, load balancers, ingress/egress rules.\n"
                "- Resource specifications: CPU cores, memory allocation, storage capacity, network bandwidth.\n\n"
                "How to respond:\n"
                "- If the user asks to manage resources, provide a concise plan of actions and proceed using available tools/actions.\n"
                "- If the request is unclear or parameters are missing, ask targeted clarification questions.\n"
                "- When users report resource faults or issues, actively investigate and propose solutions.\n"
                "- For general questions, answer briefly and stay focused on project resource management.\n\n"
                "Network error handling:\n"
                "- When users report network connectivity issues, check if network-managing resources are running.\n"
                "- Common cause: Load balancers, ingress controllers, or network gateways may be stopped.\n"
                "- If network resources are stopped, proactively start them and verify connectivity.\n"
                "- Always verify the fix by checking if the network issue is resolved after starting resources."
            )
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
