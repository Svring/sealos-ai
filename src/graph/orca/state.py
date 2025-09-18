from typing import Any, Literal, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
import re
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from typing import Annotated
from typing_extensions import TypedDict


class Port(BaseModel):
    """
    Port configuration for network access.

    Defines a network port with its number and public access settings.
    """

    number: int = Field(
        ...,
        ge=1,
        le=65535,
        description="Port number (1-65535). Examples: 80, 3000, 8080",
    )
    publicAccess: bool = Field(
        description="Whether the port should be publicly accessible from the internet"
    )


class Reliances(BaseModel):
    """
    Resource dependencies configuration.

    Defines which databases and storage buckets a resource depends on.
    All fields are optional and can be None if no dependencies exist.
    """

    database: Optional[List[str]] = Field(
        default=None, description="List of database names this resource depends on"
    )
    bucket: Optional[List[str]] = Field(
        default=None, description="List of bucket names this resource depends on"
    )


class AppEnv(BaseModel):
    """
    Application environment variable configuration.

    Defines an environment variable with name and value for application configuration.
    """

    name: str = Field(
        ...,
        description="Environment variable name. Examples: 'DATABASE_URL', 'API_KEY', 'NODE_ENV'",
    )
    value: str = Field(
        ...,
        description="Environment variable value. Examples: 'production', 'localhost:5432', 'your-api-key'",
    )


class DevBox(BaseModel):
    """
    Development environment configuration.

    Represents a development environment with a specific runtime, optional ports,
    and optional dependencies on other resources like databases or storage buckets.
    """

    name: str = Field(
        ...,
        max_length=12,
        description="DevBox name (max 12 chars, lowercase letters, numbers, hyphens only). Examples: 'dev-env', 'frontend_dev', 'api-dev'",
    )
    runtime: Literal[
        "nuxt3",
        "angular",
        "quarkus",
        "ubuntu",
        "flask",
        "java",
        "chi",
        "net",
        "iris",
        "hexo",
        "python",
        "docusaurus",
        "vitepress",
        "cpp",
        "vue",
        "nginx",
        "rocket",
        "debian-ssh",
        "vert.x",
        "express.js",
        "django",
        "next.js",
        "sealaf",
        "go",
        "react",
        "php",
        "svelte",
        "c",
        "astro",
        "umi",
        "gin",
        "echo",
        "rust",
    ] = Field(
        description="The runtime environment for development (e.g., 'Next.js', 'Python', 'React')"
    )
    ports: Optional[List[Port]] = Field(
        default=None,
        description="Optional list of ports to expose for the development environment",
    )
    reliances: Optional[Reliances] = Field(
        default=None,
        description="Optional dependencies on databases or storage buckets. Specify resource names that this DevBox depends on.",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """
        Validate DevBox name format.

        Args:
            v: The DevBox name to validate

        Returns:
            The validated DevBox name

        Raises:
            ValueError: If the name doesn't match the required format
        """
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "DevBox name must contain only lowercase letters, numbers, and hyphens. "
                "Examples: 'dev-env', 'frontend_dev', 'api-dev'. "
                f"Invalid name: '{v}'"
            )
        return v


class Database(BaseModel):
    """
    Database configuration.

    Represents a database instance with a specific type and configuration.
    """

    name: str = Field(
        ...,
        max_length=12,
        description="Database name (max 12 chars, lowercase letters, numbers, hyphens only). Examples: 'main-db', 'cache-db', 'analytics'",
    )
    type: Literal[
        "postgresql",
        "mongodb",
        "apecloud-mysql",
        "redis",
        "kafka",
        "weaviate",
        "milvus",
        "pulsar",
    ] = Field(
        description="The type of database (e.g., 'postgresql', 'mongodb', 'redis')"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """
        Validate Database name format.

        Args:
            v: The Database name to validate

        Returns:
            The validated Database name

        Raises:
            ValueError: If the name doesn't match the required format
        """
        if not re.match(r"^[a-z0-9-]+$", v):
            raise ValueError(
                "Database name must contain only lowercase letters, numbers, and hyphens. "
                "Examples: 'main-db', 'cache-db', 'analytics'. "
                f"Invalid name: '{v}'"
            )
        return v


class ObjectStorageBucket(BaseModel):
    """
    Object storage bucket configuration.

    Represents a storage bucket for files, media, and other assets with
    configurable access policies.
    """

    name: str = Field(
        ...,
        max_length=12,
        description="Bucket name (max 12 chars, lowercase letters, numbers, hyphens only). Examples: 'media-bucket', 'uploads', 'static-assets'",
    )
    policy: Literal["private", "publicRead", "publicReadwrite"] = Field(
        description="Access policy for the bucket: 'private' (no public access), 'publicRead' (public read access), 'publicReadwrite' (public read/write access)"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """
        Validate ObjectStorageBucket name format.

        Args:
            v: The ObjectStorageBucket name to validate

        Returns:
            The validated ObjectStorageBucket name

        Raises:
            ValueError: If the name doesn't match the required format
        """
        if not re.match(r"^[a-z0-9_-]+$", v):
            raise ValueError(
                "ObjectStorageBucket name must contain only lowercase letters, numbers, and hyphens. "
                "Examples: 'media-bucket', 'uploads', 'static-assets'. "
                f"Invalid name: '{v}'"
            )
        return v


class App(BaseModel):
    """
    Application configuration.

    Represents a deployed application with a Docker image, optional ports,
    environment variables, and optional dependencies on other resources.
    """

    name: str = Field(
        ...,
        max_length=12,
        description="Application name (max 12 chars, lowercase letters, numbers, hyphens only). Examples: 'web-app', 'api-server', 'frontend'",
    )

    image: str = Field(
        description="Docker image for the application (e.g., 'nginx:latest', 'node:18-alpine', 'python:3.11')"
    )
    ports: Optional[List[Port]] = Field(
        default=None, description="Optional list of ports to expose for the application"
    )
    env: Optional[List[AppEnv]] = Field(
        default=None,
        description="Optional list of environment variables for the application",
    )
    reliances: Optional[Reliances] = Field(
        default=None,
        description="Optional dependencies on databases or storage buckets. Specify resource names that this app depends on.",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """
        Validate App name format.

        Args:
            v: The App name to validate

        Returns:
            The validated App name

        Raises:
            ValueError: If the name doesn't match the required format
        """
        if not re.match(r"^[a-z0-9_-]+$", v):
            raise ValueError(
                "App name must contain only lowercase letters, numbers, and hyphens. "
                "Examples: 'web-app', 'api-server', 'frontend'. "
                f"Invalid name: '{v}'"
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
    """
    Project resources configuration.

    Defines all the infrastructure components needed for the project,
    including development environments, databases, storage buckets, and applications.
    All fields are optional and can be None if not needed.
    """

    devbox: Optional[List[DevBox]] = Field(
        default=None,
        description="Development environment configurations. List of DevBox instances for coding and development.",
    )
    database: Optional[List[Database]] = Field(
        default=None,
        description="Database configurations. List of database instances for data storage.",
    )
    bucket: Optional[List[ObjectStorageBucket]] = Field(
        default=None,
        description="Object storage bucket configurations. List of storage buckets for media and file storage.",
    )
    app: Optional[List[App]] = Field(
        default=None,
        description="Application configurations. List of application deployments.",
    )


class ProjectProposal(BaseModel):
    """
    A structured project proposal with validated naming conventions.

    This model represents a complete project proposal including the project name,
    description, and required resources. All names must follow specific validation
    rules to ensure compatibility with deployment systems.
    """

    name: str = Field(
        ...,
        max_length=12,
        description="Project name (max 12 chars, lowercase letters, numbers, hyphens only). Examples: 'my-blog', 'web-app-1', 'nextjs-site'",
    )

    resources: ProjectResources = Field(
        description="Required project resources including development environment, databases, storage, and applications."
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """
        Validate project name format.

        Args:
            v: The project name to validate

        Returns:
            The validated project name

        Raises:
            ValueError: If the name doesn't match the required format
        """
        if not re.match(r"^[a-z0-9_-]+$", v):
            raise ValueError(
                "Project name must contain only lowercase letters, numbers, and hyphens. "
                "Examples: 'my-blog', 'web-app-1', 'nextjs-site'. "
                f"Invalid name: '{v}'"
            )
        return v


class OrcaState(TypedDict):
    """
    Orca State

    Inherits from StateGraph and adds Orca-specific fields.
    """

    base_url: Optional[str] = Field(
        default=None, description="Base URL for API endpoints"
    )
    api_key: Optional[str] = Field(
        default=None, description="API key for authentication"
    )
    model_name: Optional[str] = Field(
        default=None, description="Model name to use for AI operations"
    )
    region_url: Optional[str] = Field(
        default=None, description="Region URL for API endpoints"
    )
    kubeconfig: Optional[str] = Field(
        default=None, description="Kubeconfig for Kubernetes operations"
    )

    messages: Annotated[list[AnyMessage], add_messages]

    stage: Optional[
        Literal[
            "propose_project", "manage_project", "manage_resource", "deploy_project"
        ]
    ] = Field(default=None, description="Current stage of the Orca workflow")
    project_context: Optional[Any] = Field(
        default=None, description="Context information for the current project"
    )
    resource_context: Optional[Any] = Field(
        default=None, description="Context information for the current resource"
    )
