"""
Web search tool for deploy project operations.
Provides web search capabilities using Tavily.
"""

from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from typing import Dict, Any


@tool
def search_web(query: str) -> Dict[str, Any]:
    """
    Search the web using Tavily search engine.

    Args:
        query (str): The search query to execute.

    Returns:
        Dict containing the action and payload with search results.
    """
    tavily_search = TavilySearch(max_results=3)
    search_results = tavily_search.invoke(query)

    return {
        "action": "search_web",
        "payload": {"query": query, "results": search_results},
    }


if __name__ == "__main__":
    # Test the web search tool
    # Run with: python -m src.graph.orca.tools.deploy_project_tool.web_search_tool

    print("Testing web_search_tool...")
    try:
        result = search_web.invoke("What is LangGraph?")
        print("✅ Web search successful!")
        print(f"Action: {result['action']}")
        print(f"Query: {result['payload']['query']}")
        results = result["payload"]["results"]
        if isinstance(results, str):
            print(f"Results: {results[:200]}...")  # Show first 200 chars
        else:
            print(f"Results: {str(results)[:200]}...")  # Show first 200 chars
    except Exception as e:
        print(f"❌ Web search failed: {e}")

    print(f"Tool name: {search_web.name}")
    print(f"Tool description: {search_web.description}")
