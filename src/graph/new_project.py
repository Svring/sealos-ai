"""
Sealos Brain - An intelligent entry point for Sealos platform.
Provides users with cloud resource planning for easy development and deployment.
"""

# python -m src.agent.sealos_agent
from typing import List
from typing_extensions import Literal, TypedDict

from copilotkit import CopilotKitState


from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.types import Command


from src.provider.backbone_provider import get_sealos_model
from pydantic import BaseModel
from src.utils.context_utils import (
    get_state_values,
)


class DevBox(BaseModel):
    runtime: Literal[
        "C++",
        "Nuxt3",
        "Hugo",
        "Java",
        "Chi",
        "PHP",
        "Rocket",
        "Quarkus",
        "Debian",
        "Ubuntu",
        "Spring Boot",
        "Flask",
        "Nginx",
        "Vue.js",
        "Python",
        "VitePress",
        "Node.js",
        "Echo",
        "Next.js",
        "Angular",
        "React",
        "Svelte",
        "Gin",
        "Rust",
        "UmiJS",
        "Docusaurus",
        "Hexo",
        "Vert.x",
        "Go",
        "C",
        "Iris",
        "Astro",
        "MCP",
        "Django",
        "Express.js",
        ".Net",
    ]
    description: str


class Database(BaseModel):
    type: Literal[
        "postgresql",
        "mongodb",
        "apecloud-mysql",
        "redis",
        "kafka",
        "weaviate",
        "milvus",
        "pulsar",
    ]
    description: str


class ObjectStorageBucket(BaseModel):
    policy: Literal["Private", "PublicRead", "PublicReadwrite"]
    description: str


class ProjectResources(BaseModel):
    devboxes: List[DevBox]
    databases: List[Database]
    buckets: List[ObjectStorageBucket]


class ProjectInfo(TypedDict, total=False):
    name: str
    description: str
    resources: ProjectResources


class SealosAIState(CopilotKitState):
    """
    Sealos Brain State

    Inherits from CopilotKitState and adds Sealos-specific fields.
    """

    base_url: str
    api_key: str
    model: str

    project: ProjectInfo
    project_brief: str


class ProjectPlan(BaseModel):
    name: str
    description: str
    resources: ProjectResources


class RouteDecision(BaseModel):
    next_node: Literal["__end__", "compose_new_project", "continue_chat"]
    info: str


async def entry_node(
    state: SealosAIState,
    config: RunnableConfig,
) -> Command[Literal["compose_new_project", "__end__", "continue_chat"]]:
    """
    Sealos Brain entry point. Carefully analyzes user requests and manages ongoing conversations.
    Only routes to project planning for specific new project requests or explicit resource modifications.
    """
    (
        messages,
        base_url,
        api_key,
        model_name,
        project,
    ) = get_state_values(
        state,
        {
            "messages": [],
            "base_url": None,
            "api_key": None,
            "model": None,
            "project": None,
        },
    )

    model = get_sealos_model(model_name, base_url, api_key)

    structured = model.with_structured_output(RouteDecision)

    # Check if we already have a project plan
    has_existing_project = project and hasattr(project, "name") and project.name

    if has_existing_project:
        system = SystemMessage(
            content=(
                "You are Sealos Brain managing an ongoing conversation about an existing project. "
                "CAREFULLY analyze the user's input:\n\n"
                "ONLY set next_node='compose_new_project' if the user makes a VERY SPECIFIC request to:\n"
                "- Add a new resource type (e.g., 'add a database', 'need file storage')\n"
                "- Modify the project scope significantly (e.g., 'make it a mobile app too')\n"
                "- Change core requirements (e.g., 'it needs to handle 1000 users')\n\n"
                "For all other inputs (questions, clarifications, general chat, minor tweaks), set next_node='continue_chat' "
                "and respond naturally to continue the conversation about the existing project.\n\n"
                "If they want to start a completely new project, set next_node='compose_new_project'.\n\n"
                "Return only the structured fields next_node and info."
            )
        )
    else:
        system = SystemMessage(
            content=(
                "You are Sealos Brain, an intelligent entry point for the Sealos cloud platform. "
                "Analyze the conversation to determine if the user wants to create/build/deploy a project. "
                "If they want to build something (website, app, service, etc.), set next_node='compose_new_project' "
                "and provide a SHORT, CONCISE project brief focused on RESOURCES NEEDED:\n"
                "- What type of application/service is being built\n"
                "- Key technical requirements that determine resource needs\n"
                "- Any specific constraints or preferences mentioned\n\n"
                "Keep the brief to 2-3 sentences maximum. Focus on what will help determine which Sealos resources (DevBoxes, Databases, Buckets) are needed.\n\n"
                "If not about building a project, set next_node='__end__' and chat naturally with the user. "
                "Greet them warmly, respond briefly to their input, and gently encourage them to propose a project they'd like to build. "
                "Mention that you can help plan cloud resources for any software project. Keep the response friendly and conversational. "
                "Return only the structured fields next_node and info."
            )
        )

    decision: RouteDecision = await structured.ainvoke([system, *messages])

    if decision.next_node == "compose_new_project":
        return Command(
            goto="compose_new_project",
            update={"project_brief": decision.info},
        )
    elif decision.next_node == "continue_chat":
        updated_messages = [*messages, AIMessage(content=decision.info)]
        return Command(goto="__end__", update={"messages": updated_messages})
    else:
        updated_messages = [*messages, AIMessage(content=decision.info)]
        return Command(goto="__end__", update={"messages": updated_messages})


async def compose_new_project(
    state: SealosAIState, config: RunnableConfig
) -> Command[Literal["summarize_project"]]:
    """
    Compose a Sealos cloud resource plan based on the project brief.
    Recommends optimal combinations of DevBoxes, Databases, and Object Storage Buckets.
    """
    (
        project_brief,
        base_url,
        api_key,
        model_name,
    ) = get_state_values(
        state,
        {
            "project_brief": "",
            "base_url": None,
            "api_key": None,
            "model": None,
        },
    )

    model = get_sealos_model(model_name, base_url, api_key)

    structured = model.with_structured_output(ProjectPlan)

    system = SystemMessage(
        content=(
            "You are a Sealos cloud architect. Design a MINIMAL resource plan using the least resources possible. "
            "CRITICAL: Use as FEW resources as possible. Only add resources if absolutely necessary.\n"
            "Guidelines:\n"
            "- DevBoxes: Choose ONE runtime that can handle the entire project (e.g., Next.js for full-stack web apps)\n"
            "- Databases: Only add if data persistence is explicitly required. Choose ONE database type maximum\n"
            "- Buckets: Only add if file/media storage is explicitly mentioned\n\n"
            "Examples of MINIMAL selection:\n"
            "- Blog website: Next.js devbox only (no database needed for static)\n"
            "- Shopping site: Next.js devbox + postgresql database + PublicRead bucket\n"
            "- API service: Python/Node.js devbox + database only if data storage needed\n\n"
            "Return structured data with: name, description, and resources arrays. Keep descriptions brief."
        )
    )

    plan: ProjectPlan = await structured.ainvoke(
        [system, SystemMessage(content=f"Project brief: {project_brief}")]
    )

    return Command(
        goto="summarize_project",
        update={
            "project": {
                "name": plan.name,
                "description": plan.description,
                "resources": plan.resources,
            },
        },
    )


async def summarize_project(
    state: SealosAIState, config: RunnableConfig
) -> Command[Literal["__end__"]]:
    """
    Generate a comprehensive Sealos resource plan summary explaining the rationale
    behind resource selections and providing usage guidance.
    """
    (
        project_brief,
        project,
        base_url,
        api_key,
        model_name,
    ) = get_state_values(
        state,
        {
            "project_brief": "",
            "project": {"name": "", "description": "", "resources": None},
            "base_url": None,
            "api_key": None,
            "model": None,
        },
    )

    model = get_sealos_model(model_name, base_url, api_key)

    system = SystemMessage(
        content=(
            "You are Sealos Brain. Format your response as an unordered list with this structure:\n"
            "• **Resource Name**: One sentence explaining its purpose and role\n\n"
            "Example format:\n"
            "• **Next.js DevBox**: Provides the complete development environment for frontend and backend\n"
            "• **PostgreSQL Database**: Stores user data and application state\n\n"
            "Keep each explanation to one sentence maximum. Be direct and actionable."
        )
    )

    # Format resources for better readability
    resources = project.get("resources")
    if resources and hasattr(resources, "devboxes"):
        devboxes = resources.devboxes or []
        databases = resources.databases or []
        buckets = resources.buckets or []
    else:
        devboxes = []
        databases = []
        buckets = []

    summary_prompt = f"""
Project Brief: {project_brief}

RECOMMENDED SEALOS RESOURCE PLAN:
Project Name: {project.get('name', 'Unnamed Project')}
Description: {project.get('description', 'No description provided')}

DevBoxes (Development Environments):
{chr(10).join([f"- {box.runtime}: {box.description}" for box in devboxes]) if devboxes else "- None recommended"}

Databases:
{chr(10).join([f"- {db.type}: {db.description}" for db in databases]) if databases else "- None recommended"}

Object Storage Buckets:
{chr(10).join([f"- {bucket.policy} policy: {bucket.description}" for bucket in buckets]) if buckets else "- None recommended"}

Provide a comprehensive summary explaining the rationale and usage guidance.
"""

    summary = await model.ainvoke([system, SystemMessage(content=summary_prompt)])

    return Command(
        goto="__end__",
        update={
            "messages": [AIMessage(content=summary.content)],
        },
    )


# Define the workflow graph
workflow = StateGraph(SealosAIState)
workflow.add_node("entry_node", entry_node)
workflow.add_node("compose_new_project", compose_new_project)
workflow.add_node("summarize_project", summarize_project)
workflow.add_edge("compose_new_project", "summarize_project")

workflow.set_entry_point("entry_node")

# Compile the workflow graph
graph = workflow.compile()
