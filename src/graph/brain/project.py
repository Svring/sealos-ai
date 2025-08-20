"""
Project node that creates project plans based on user input.
"""

from typing import Literal
from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from src.provider.backbone_provider import get_sealos_model
from src.utils.context_utils import get_state_values
from src.graph.brain.state import BrainState, ProjectProposal

from copilotkit.langgraph import (
    copilotkit_customize_config,
)


# System prompt for project plan generation
PROJECT_PLAN_PROMPT = """You are a cloud architect creating a minimal project plan.

CRITICAL REQUIREMENTS:
1. Use as FEW resources as possible. Only add resources if absolutely necessary.
2. Focus on WHAT the user wants to build, not HOW to build it.
3. Avoid mentioning specific brand names, frameworks, or technologies in the project name and description.
4. STRICTLY FOLLOW the user's requirements.

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
- DevBoxes: Choose ONE runtime that can handle the entire project
- Databases: Only add if data persistence is explicitly required. Choose ONE database type maximum
- Buckets: Only add if file/media storage is explicitly mentioned

Examples of good naming:
- Name: "Shopping Site" (not "Next.js E-commerce App")
- Description: "An online store for selling products with user accounts and order management"
- Name: "Blog Platform" (not "WordPress Blog")
- Description: "A content management system for publishing articles and managing blog posts"

Return structured data with: name, description, and resources arrays. Ensure the plan strictly adheres to the user's requirements."""


async def project_agent(
    state: BrainState, config: RunnableConfig
) -> Command[Literal["__end__"]]:
    """
    Project agent that creates project plans based on user input.
    """
    # Extract state variables
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

    # Get model and create structured output
    model = get_sealos_model(model_name, base_url, api_key)
    structured_model = model.with_structured_output(ProjectProposal)

    modified_config = copilotkit_customize_config(
        config, emit_messages=False, emit_tool_calls=True
    )

    # Generate project plan
    project_plan: ProjectProposal = await structured_model.ainvoke(
        [SystemMessage(content=PROJECT_PLAN_PROMPT), *messages],
        config=modified_config,
    )

    # Format the response
    resources = project_plan.resources
    devboxes = resources.devboxes or []
    databases = resources.databases or []
    buckets = resources.buckets or []

    response_content = """
"""

    return Command(
        goto="__end__",
        update={
            "messages": AIMessage(content=response_content),
            "project_proposal": project_plan,
        },
    )
