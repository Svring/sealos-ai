from typing import Any, Literal, List, Optional
from copilotkit import CopilotKitState
from pydantic import BaseModel


class DevBox(BaseModel):
    name: str
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
    name: str
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
    name: str
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


class OrcaState(CopilotKitState):
    """
    Orca State

    Inherits from CopilotKitState and adds Orca-specific fields.
    """

    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None

    stage: Optional[Literal["propose_project", "manage_project"]] = None
