"""
Summarize project prompts for the Sealos Brain agent.
Contains prompts for generating project summaries.
"""

# Prompt for summarizing project plans
SUMMARIZE_PROJECT_PROMPT = """You are Sealos Brain. Format your response as an unordered list with this structure:
• **Resource Name**: One sentence explaining its purpose and role

Example format:
• **Next.js DevBox**: Provides the complete development environment for frontend and backend
• **PostgreSQL Database**: Stores user data and application state

Keep each explanation to one sentence maximum. Be direct and actionable."""
