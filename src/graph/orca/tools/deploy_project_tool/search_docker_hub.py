"""
Docker Hub search tool for deploy project operations.
Searches Docker Hub repositories by query string.
"""

from langchain_core.tools import tool
import requests


@tool
def search_docker_hub(query: str) -> str:
    """
    Search Docker Hub repositories by a given query string.

    Args:
        query (str): The search term to query Docker Hub repositories.

    Returns:
        str: A newline-separated list of up to 20 repository names matching the query.
    """
    url = f"https://hub.docker.com/v2/search/repositories/?query={query}&page_size=20"
    response = requests.get(url)
    response.raise_for_status()  # Raise error for bad responses
    results = response.json().get("results", [])
    # Limit to a maximum of 20 results
    return "\n".join([repo["repo_name"] for repo in results[:20]])  # Format as needed


if __name__ == "__main__":
    # Test the Docker Hub search tool
    # Run with: python -m src.graph.orca.tools.deploy_project_tool.search_docker_hub

    print("Testing search_docker_hub...")
    try:
        result = search_docker_hub.invoke("nginx")
        print("✅ Docker Hub search successful!")
        print("Found repositories:")
        repos = result.split("\n")[:5]  # Show first 5 results
        for i, repo in enumerate(repos, 1):
            print(f"  {i}. {repo}")
        if len(result.split("\n")) > 5:
            print(f"  ... and {len(result.split('\n')) - 5} more")
    except Exception as e:
        print(f"❌ Docker Hub search failed: {e}")

    print(f"Tool name: {search_docker_hub.name}")
    print(f"Tool description: {search_docker_hub.description}")
