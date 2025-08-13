"""
Compose project brief prompts for the Sealos Brain agent.
Contains prompts for generating and modifying project requirements.
"""

# Prompt for generating new project brief requirements
PROJECT_BRIEF_GENERATION_PROMPT = """Based on the user's input, generate 2-6 concise, specific requirement sentences. Each sentence should:
- Be one line maximum
- Specify a concrete resource or capability need
- Use clear, actionable language
- Focus on what resources are needed
- Be oriented around the available resources: DevBox, Database, Bucket

Examples of good requirement sentences:
- "Create a Next.js devbox for full-stack web development"
- "This shopping site necessitates a PostgreSQL database for user data storage"
- "Add a PublicRead storage bucket for product images"
- "Require Redis for session management and caching"

Return only the requirement sentences, one per line, without numbering or bullets."""

# Prompt for modifying existing project brief requirements
PROJECT_BRIEF_MODIFICATION_PROMPT = """Based on the user's request to modify an existing project, generate 2-6 concise requirement sentences that include:
* EXISTING requirements from the current project (maintain what they have)
* NEW requirements based on their request (add what they want)
* MODIFIED requirements if they want changes (update existing resources)

Focus on maintaining the existing project context while incorporating their new requests.

Examples for existing project modifications:
- "Keep the existing Next.js devbox for frontend development"
- "Add a Python devbox for machine learning tasks"
- "Maintain the PostgreSQL database for user data"
- "Add Redis database for session caching"

Return only the requirement sentences, one per line, without numbering or bullets."""
