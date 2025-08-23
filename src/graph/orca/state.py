from typing import Any, Literal, List, Optional, Dict, TypedDict
from copilotkit import CopilotKitState
from pydantic import BaseModel, Field, field_validator
import re


class Reliances(TypedDict, total=False):
    database: List[str]
    bucket: List[str]


class DevBox(BaseModel):
    name: str = Field(..., max_length=12)
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
    reliances: Optional[Reliances] = None
    description: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9_-]+$", v):
            raise ValueError(
                "Name must contain only lowercase letters, numbers, underscores, and hyphens"
            )
        return v


class Database(BaseModel):
    name: str = Field(..., max_length=12)
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

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9_-]+$", v):
            raise ValueError(
                "Name must contain only lowercase letters, numbers, underscores, and hyphens"
            )
        return v


class ObjectStorageBucket(BaseModel):
    name: str = Field(..., max_length=12)
    policy: Literal["Private", "PublicRead", "PublicReadwrite"]
    description: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9_-]+$", v):
            raise ValueError(
                "Name must contain only lowercase letters, numbers, underscores, and hyphens"
            )
        return v


class App(BaseModel):
    name: str = Field(..., max_length=12)
    description: str
    image: str
    reliances: Optional[Reliances] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9_-]+$", v):
            raise ValueError(
                "Name must contain only lowercase letters, numbers, underscores, and hyphens"
            )
        return v

    @field_validator("image")
    @classmethod
    def validate_image(cls, v: str) -> str:
        # Docker image format: [registry/]name[:tag][@digest]
        # Examples: nginx, nginx:latest, docker.io/nginx:1.21, nginx@sha256:...
        if not re.match(
            r"^[a-zA-Z0-9._-]+(/[a-zA-Z0-9._-]+)*(:[a-zA-Z0-9._-]+)?(@sha256:[a-fA-F0-9]{64})?$",
            v,
        ):
            raise ValueError(
                "Image must be a valid Docker image format (e.g., nginx, nginx:latest, docker.io/nginx:1.21)"
            )
        return v


class ProjectResources(BaseModel):
    devbox: Optional[List[DevBox]] = None
    database: Optional[List[Database]] = None
    bucket: Optional[List[ObjectStorageBucket]] = None
    app: Optional[List[App]] = None


class ProjectProposal(BaseModel):
    name: str = Field(..., max_length=12)
    description: str = Field(..., max_length=30)
    resources: ProjectResources

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9_-]+$", v):
            raise ValueError(
                "Name must contain only lowercase letters, numbers, underscores, and hyphens"
            )
        return v


class OrcaState(CopilotKitState):
    """
    Orca State

    Inherits from CopilotKitState and adds Orca-specific fields.
    """

    base_url: Optional[str] = None
    api_key: Optional[str] = None
    model: Optional[str] = None

    stage: Optional[Literal["propose_project", "manage_project"]] = None
