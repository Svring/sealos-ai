"""
Pydantic schemas for the New Project agent.
"""

from typing import List
from typing_extensions import Literal, TypedDict
from pydantic import BaseModel


class ProjectBrief(BaseModel):
    briefs: List[str]
    status: Literal["pending", "active", "completed"]


class ProjectPlanWithStatus(BaseModel):
    name: str
    description: str
    resources: "ProjectResources"
    status: Literal["pending", "active", "completed"]


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


class ProjectPlan(BaseModel):
    name: str
    description: str
    resources: ProjectResources


class RouteDecision(BaseModel):
    next_node: Literal["__end__", "compose_project_brief"]
    info: str


class RouteOnly(BaseModel):
    next_node: Literal["__end__", "compose_project_brief", "manage_resource"]


class ProjectRequirements(BaseModel):
    requirements: List[str]
