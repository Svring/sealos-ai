"""
Web search tool for deploy project operations.
Provides web search capabilities using Tavily.
"""

from langchain_tavily import TavilySearch

web_search_tool = TavilySearch(max_results=3)


if __name__ == "__main__":
    # Test the web search tool
    # Run with: python -m src.graph.orca.tools.deploy_project_tool.web_search_tool

    print("Testing web_search_tool...")
    try:
        result = web_search_tool.invoke("What is LangGraph?")
        print("✅ Web search successful!")
        print(f"Result: {result[:200]}...")  # Show first 200 chars
    except Exception as e:
        print(f"❌ Web search failed: {e}")

    print(f"Tool name: {web_search_tool.name}")
    print(f"Tool description: {web_search_tool.description}")
