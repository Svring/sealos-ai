"""
Docker Hub search tool for deploy project operations.
Searches Docker Hub repositories by query string.
"""

from langchain_core.tools import tool
import requests
from typing import Dict, Any


@tool
def search_docker_hub(query: str) -> Dict[str, Any]:
    """
    Search Docker Hub repositories by a given query string.

    Args:
        query (str): The search term to query Docker Hub repositories.

    Returns:
        Dict containing the action and payload with detailed repository information.
    """
    url = f"https://hub.docker.com/v2/search/repositories/?query={query}&page_size=20"
    response = requests.get(url)
    response.raise_for_status()  # Raise error for bad responses
    results = response.json().get("results", [])

    # Process results to include more specific information
    processed_results = []
    for repo in results[:20]:  # Limit to 20 results
        repo_info = {
            "name": repo.get("repo_name", ""),
            "description": repo.get("short_description", ""),
            "star_count": repo.get("star_count", 0),
            "pull_count": repo.get("pull_count", 0),
            "is_automated": repo.get("is_automated", False),
            "is_official": repo.get("is_official", False),
            "last_updated": repo.get("last_updated", ""),
            "tags": (
                repo.get("tags", [])[:5] if repo.get("tags") else []
            ),  # Show first 5 tags
        }
        processed_results.append(repo_info)

    return {
        "action": "search_docker_hub",
        "payload": {
            "query": query,
            "total_results": len(processed_results),
            "repositories": processed_results,
        },
    }


if __name__ == "__main__":
    # Test the Docker Hub search tool
    # Run with: python -m src.graph.orca.tools.deploy_project_tool.search_docker_hub

    print("Testing search_docker_hub...")
    try:
        result = search_docker_hub.invoke("nginx")
        print("✅ Docker Hub search successful!")
        print(f"Action: {result['action']}")
        print(f"Query: {result['payload']['query']}")
        print(f"Total results: {result['payload']['total_results']}")
        print(f"First repository: {result['payload']['repositories'][0]['name']}")
    except Exception as e:
        print(f"❌ Docker Hub search failed: {e}")

    print(f"\nTool name: {search_docker_hub.name}")
    print(f"Tool description: {search_docker_hub.description}")
