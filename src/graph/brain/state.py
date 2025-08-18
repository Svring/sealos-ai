from typing import Any, Literal, List
from copilotkit import CopilotKitState
from pydantic import BaseModel


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


class ProjectProposal(BaseModel):
    name: str
    description: str
    resources: ProjectResources


class BrainState(CopilotKitState):
    """
    Brain State

    Inherits from CopilotKitState and adds Sealos-specific fields.
    """

    base_url: str
    api_key: str
    model: str

    stage: Literal["project", "resource"]
    project_proposal: ProjectProposal
    resource_context: Any
