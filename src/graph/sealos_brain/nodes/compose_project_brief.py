"""
Compose project brief node for the Sealos Brain agent.
Generates and optimizes project requirements based on user input.
"""

from typing_extensions import Literal
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from src.provider.backbone_provider import get_sealos_model
from src.utils.context_utils import get_state_values
from copilotkit.langgraph import (
    copilotkit_customize_config,
    copilotkit_emit_state,
)
from src.prompts.nodes.compose_project_brief_prompts import (
    PROJECT_BRIEF_GENERATION_PROMPT,
    PROJECT_BRIEF_MODIFICATION_PROMPT,
)

from src.graph.sealos_brain.schemas import ProjectRequirements
from src.graph.sealos_brain.state import SealosBrainState


async def _optimize_requirements(
    requirements: list[str], model, config: RunnableConfig
) -> list[str]:
    """
    Optimize requirements to minimize resources and use modern tech stacks.
    """
    if not requirements:
        return requirements

    # Create optimization prompt
    optimization_prompt = f"""
You are a cloud resource optimization expert. Analyze these project requirements and optimize them to:

1. MINIMIZE RESOURCES: Use the fewest possible DevBoxes, Databases, and Buckets
2. MODERN TECH STACK: Prefer modern technologies over older ones
3. CONSOLIDATE: Combine similar requirements where possible

Current requirements:
{chr(10).join(requirements)}

Optimization rules:
- DevBoxes: Prefer Next.js over PHP, React over jQuery, Node.js over older runtimes
- Databases: Use one database type when possible, prefer PostgreSQL over MySQL
- Buckets: Consolidate storage needs into fewer buckets
- Remove redundant or overlapping requirements
- Keep only essential, non-negotiable requirements

Return 2-6 optimized requirement sentences, one per line, without numbering or bullets.
Focus on what's absolutely necessary for the project to function.
"""

    try:
        # Get optimized requirements from the model
        optimization_response = await model.ainvoke(
            [SystemMessage(content=optimization_prompt)], config=config
        )

        # Split the response into individual requirements
        optimized_text = optimization_response.content.strip()
        optimized_requirements = [
            req.strip()
            for req in optimized_text.split("\n")
            if req.strip()
            and not req.strip().startswith(("-", "•", "*", "1.", "2.", "3."))
        ]

        # Fallback to original requirements if optimization fails
        if not optimized_requirements:
            return requirements

        return optimized_requirements[:6]  # Limit to 6 requirements max

    except Exception:
        # If optimization fails, return original requirements
        return requirements


async def compose_project_brief(
    state: SealosBrainState, config: RunnableConfig
) -> Command[Literal["compose_new_project"]]:
    """
    Generate project brief requirements based on user input.
    This node creates structured requirement sentences for the project.
    """
    (
        messages,
        base_url,
        api_key,
        model_name,
        project_plan,
    ) = get_state_values(
        state,
        {
            "messages": [],
            "base_url": None,
            "api_key": None,
            "model": None,
            "project_plan": None,
        },
    )

    has_existing_project = (
        project_plan and hasattr(project_plan, "name") and project_plan.name
    )

    modified_config = copilotkit_customize_config(
        config, emit_messages=False, emit_tool_calls=False
    )

    # Use gpt-5-mini for content generation with structured output
    content_model = get_sealos_model("gpt-4o", base_url, api_key)
    structured_content = content_model.with_structured_output(ProjectRequirements)

    # Generate project brief requirements
    if has_existing_project:
        content_prompt = PROJECT_BRIEF_MODIFICATION_PROMPT
    else:
        content_prompt = PROJECT_BRIEF_GENERATION_PROMPT

    requirements_response: ProjectRequirements = await structured_content.ainvoke(
        [SystemMessage(content=content_prompt), *messages], config=modified_config
    )

    # Get the structured requirements list
    requirements_list = requirements_response.requirements

    # Resource minimization and modern tech stack optimization
    optimized_requirements = await _optimize_requirements(
        requirements_list, content_model, modified_config
    )

    state["project_brief"] = {"briefs": optimized_requirements, "status": "completed"}
    # await asyncio.sleep(2)
    state["project_plan"] = {
        "name": project_plan.get("name", "Unnamed Project"),
        "description": project_plan.get("description", "No description"),
        "resources": project_plan.get("resources", {}),
        "status": "active",
    }
    await copilotkit_emit_state(config, state)

    return Command(
        goto="compose_new_project",
        update={
            "project_brief": {"briefs": optimized_requirements, "status": "completed"},
            "project_plan": {
                "name": project_plan.get("name", "Unnamed Project"),
                "description": project_plan.get("description", "No description"),
                "resources": project_plan.get("resources", {}),
                "status": "active",
            },
        },
    )
