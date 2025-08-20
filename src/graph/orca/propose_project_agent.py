"""
Project proposal node for the Orca agent.
Handles project proposal generation with tools and actions.
"""

from typing import Annotated, Literal
from langchain_core.messages import SystemMessage, AIMessage
from langgraph.prebuilt import InjectedState
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from langchain_core.tools import tool

from src.provider.backbone_provider import get_sealos_model
from src.utils.context_utils import get_state_values
from src.graph.orca.state import OrcaState, ProjectProposal
from copilotkit.langgraph import copilotkit_customize_config


# System prompt for project proposal
PROJECT_PROPOSAL_PROMPT = """You are Sealos AI, the project proposal specialist for the Sealos cloud platform. 
Your role is to analyze user requirements and propose optimal project configurations.

What you do:
- Analyze user requirements and project goals (even if vague)
- Propose optimal resource configurations using ONLY the three core resources
- Suggest cost-effective solutions
- Provide project structure recommendations
- Estimate resource requirements

RESPONSE STYLE:
- **POLITE & ENCOURAGING**: Be helpful, supportive, and warm in your responses
- **PROACTIVE**: Always suggest a basic project setup even for vague requirements
- **ENGAGING**: Take time to understand and respond thoughtfully to user needs
- **RESOURCE-FOCUSED**: Focus ONLY on DevBox, Database, and ObjectStorage resources

CRITICAL RESTRICTIONS:
- ONLY mention and work with these three resources: DevBox, Database, ObjectStorage
- DO NOT mention any other technologies, frameworks, services, or concepts
- DO NOT discuss web servers, front-end frameworks, CMS, CDN, analytics, or any other services
- Keep responses focused and simple to avoid conversation interruption

WHEN TO USE THE PROPOSE_PROJECT TOOL:
ALWAYS call the propose_project tool when users mention:
- Project creation: "creating a shopping site", "I'd like a blog site", "build a website", "create an app"
- Resource allocation: "allocate a devbox", "need a database", "want storage", "set up resources"
- Project planning: "plan a project", "propose a setup", "design infrastructure"
- Development requests: "start development", "begin coding", "set up environment"
- Any request that involves creating, building, or setting up something

EXAMPLES OF WHEN TO CALL THE TOOL:
- "I want to create a shopping site" → CALL propose_project
- "I'd like a blog site" → CALL propose_project  
- "Allocate a devbox for me" → CALL propose_project
- "Need a database for my project" → CALL propose_project
- "Build a website" → CALL propose_project
- "Create an API service" → CALL propose_project
- "Set up resources for my app" → CALL propose_project

How to respond:
- For ANY project creation or resource allocation request: ALWAYS use the propose_project tool
- After successfully calling the tool and receiving a result: Summarize what was generated in NO MORE THAN THREE SENTENCES
- If user doesn't have a project idea: Give warm, encouraging advice to help them come up with project ideas
- Be encouraging and helpful in all interactions
- Take time to provide thoughtful responses that show you understand their needs
- Focus ONLY on the three core resources

TOOL RESULT SUMMARIZATION:
When you receive a project proposal from the tool:
- Keep the summary to 3 sentences maximum
- Focus on the key resources and their purpose
- Be encouraging and supportive
- Avoid technical jargon
- Make it easy for the user to understand what they're getting
"""


# System prompt for structured project proposal generation
STRUCTURED_PROPOSAL_PROMPT = """You are a cloud architect creating a minimal project plan.

CRITICAL REQUIREMENTS:
1. ALWAYS include at least ONE DevBox - this is the minimum requirement for any project
2. Add databases if data persistence is needed (user accounts, content, etc.)
3. Add buckets if file/media storage is mentioned or likely needed
4. Focus on WHAT the user wants to build, not HOW to build it
5. Avoid mentioning specific brand names, frameworks, or technologies in the project name and description
6. Be proactive - even for vague requirements, suggest a basic but functional setup
7. ONLY work with the three core resources: DevBox, Database, ObjectStorage

PROJECT NAMING GUIDELINES:
- Name should describe the PURPOSE or TYPE of project (e.g., "Shopping Site", "Blog Platform", "API Service")
- Avoid technical terms like "Next.js App", "WordPress Site", "React Dashboard"
- Use descriptive, user-focused names that explain what the project does

PROJECT DESCRIPTION GUIDELINES:
- Describe the project's PURPOSE and FUNCTIONALITY based on the user's request
- Focus on what users will be able to do with it
- Avoid technical implementation details
- Keep it simple and clear

RESOURCE GUIDELINES:
- DevBoxes: ALWAYS include at least ONE runtime that can handle the project
- Databases: Add if data persistence is needed (user accounts, content, settings, etc.)
- Buckets: Add if file/media storage is mentioned or likely needed (images, documents, etc.)

CRITICAL RESTRICTIONS:
- ONLY mention and work with these three resources: DevBox, Database, ObjectStorage
- DO NOT mention any other technologies, frameworks, services, or concepts
- DO NOT discuss web servers, front-end frameworks, CMS, CDN, analytics, or any other services
- Keep responses focused and simple to avoid conversation interruption

Examples of good naming:
- Name: "Shopping Site" (not "Next.js E-commerce App")
- Description: "An online store for selling products with user accounts and order management"
- Name: "Blog Platform" (not "WordPress Blog")
- Description: "A content management system for publishing articles and managing blog posts"

For vague requirements, suggest a basic but functional setup that the user can build upon."""


@tool
async def propose_project(
    user_requirements: str,
    # state: Annotated[OrcaState, InjectedState],
    config: RunnableConfig,
) -> ProjectProposal:
    """
    Generate a structured project proposal based on user requirements.

    Args:
        user_requirements: The user's project requirements and goals
        state: The current state containing model configuration
        config: The runnable configuration

    Returns:
        ProjectProposal: A structured project proposal with name, description, and resources
    """
    # Get model and create structured output
    model = get_sealos_model()
    structured_model = model.with_structured_output(ProjectProposal)

    # modified_config = copilotkit_customize_config(
    #     config, emit_messages=False, emit_tool_calls=False
    # )

    # Generate project plan
    project_plan: ProjectProposal = await structured_model.ainvoke(
        [
            SystemMessage(content=STRUCTURED_PROPOSAL_PROMPT),
            SystemMessage(content=user_requirements),
        ],
        # config=modified_config,
    )

    return project_plan.model_dump()


async def propose_project_agent(
    state: OrcaState, config: RunnableConfig
) -> Command[Literal["propose_tool_node", "__end__"]]:
    """
    Project proposal agent based on the Sealos AI functionality.
    Handles model binding, system prompts, and tool calls.
    """
    # Extract state data
    (
        messages,
        base_url,
        api_key,
        model_name,
    ) = get_state_values(
        state,
        {
            "messages": [],
            "base_url": None,
            "api_key": None,
            "model": None,
        },
    )

    model = get_sealos_model(model_name, base_url, api_key)

    # Get copilot actions and add the propose_project tool
    model_with_tools = model.bind_tools([propose_project], parallel_tool_calls=False)

    # Build messages with system prompt for project proposal
    system_message = SystemMessage(content=PROJECT_PROPOSAL_PROMPT)

    # Build message list
    message_list = [system_message] + messages

    # Get model response
    response = await model_with_tools.ainvoke(message_list)

    # print("response", response)

    # Check if the response contains tool calls
    if hasattr(response, "tool_calls") and response.tool_calls:
        return Command(goto="propose_tool_node", update={"messages": response})
    else:
        return Command(
            goto="__end__",
            update={"messages": response},
        )
