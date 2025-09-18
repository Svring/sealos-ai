from langchain_tavily import TavilySearch
from langchain_core.tools import tool
import requests
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

web_search_tool = TavilySearch(max_results=3)


def find_relevant_text_segments(
    text_segments: list, keywords: list, top_k: int = 5
) -> list:
    """
    Find text segments most relevant to keywords using TF-IDF + Cosine Similarity.

    Args:
        text_segments (list): List of text segments to search through
        keywords (list): List of keywords to match against
        top_k (int): Number of top relevant segments to return (default: 5)

    Returns:
        list: List of tuples containing (segment, similarity_score) sorted by relevance
    """
    if not text_segments or not keywords:
        return []

    # Combine keywords into a single query string
    query = " ".join(keywords)

    # Create TF-IDF vectorizer
    vectorizer = TfidfVectorizer(stop_words="english", lowercase=True)

    # Combine query with text segments for vectorization
    all_texts = [query] + text_segments

    # Fit and transform the texts
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    # Calculate cosine similarity between query and all segments
    query_vector = tfidf_matrix[0:1]  # First row is the query
    segment_vectors = tfidf_matrix[1:]  # Rest are the segments

    similarities = cosine_similarity(query_vector, segment_vectors).flatten()

    # Create list of (segment, similarity_score) tuples
    results = list(zip(text_segments, similarities))

    # Sort by similarity score (descending) and return top_k
    results.sort(key=lambda x: x[1], reverse=True)

    return results[:top_k]


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


@tool
def search_app_store(keywords: str) -> str:
    """
    Search for App Store templates using TF-IDF + Cosine Similarity to find the most relevant matches.

    Args:
        keywords (str): Comma-separated keywords to search for (e.g., "nginx,web server,proxy")

    Returns:
        str: A JSON string containing the top 3 most relevant templates ranked by similarity score.
    """
    # Get all templates from the App Store
    url = "https://template.bja.sealos.run/api/listTemplate?language=en"
    response = requests.get(url)
    response.raise_for_status()

    try:
        # Check if response is JSON
        if response.headers.get("content-type", "").startswith("application/json"):
            templates_data = response.json()
        else:
            # If not JSON, try to parse as JSON string
            templates_data = json.loads(response.text)

        # Handle different response structures
        if isinstance(templates_data, dict):
            # Check if it's the expected structure: {"code": 200, "data": {"templates": [...]}}
            if (
                "data" in templates_data
                and isinstance(templates_data["data"], dict)
                and "templates" in templates_data["data"]
            ):
                templates = templates_data["data"]["templates"]
            elif "data" in templates_data:
                templates = templates_data["data"]
            else:
                templates = templates_data
        elif isinstance(templates_data, list):
            templates = templates_data
        else:
            return json.dumps(
                {"error": f"Unexpected response format: {type(templates_data)}"},
                indent=2,
            )

        if not templates:
            return json.dumps({"error": "No templates found"}, indent=2)

        # Extract text segments for similarity matching
        # Combine name, description, and tags for better matching
        text_segments = []
        for template in templates:
            segment_parts = []
            if template.get("name"):
                segment_parts.append(template["name"])
            if template.get("description"):
                segment_parts.append(template["description"])
            if template.get("tags"):
                if isinstance(template["tags"], list):
                    segment_parts.extend(template["tags"])
                else:
                    segment_parts.append(str(template["tags"]))

            text_segments.append(" ".join(segment_parts))

        # Parse keywords
        keyword_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]

        if not keyword_list:
            return json.dumps({"error": "No valid keywords provided"}, indent=2)

        # Find most relevant templates using TF-IDF similarity
        relevant_segments = find_relevant_text_segments(
            text_segments, keyword_list, top_k=3
        )

        # Map back to original template data
        relevant_templates = []
        for segment, similarity_score in relevant_segments:
            # Find the original template for this segment
            for template in templates:
                template_text = " ".join(
                    [
                        template.get("name", ""),
                        template.get("description", ""),
                        (
                            " ".join(template.get("tags", []))
                            if isinstance(template.get("tags"), list)
                            else str(template.get("tags", ""))
                        ),
                    ]
                )
                if template_text.strip() == segment.strip():
                    template_with_score = template.copy()
                    template_with_score["similarity_score"] = float(similarity_score)
                    relevant_templates.append(template_with_score)
                    break

        return json.dumps(
            {
                "query_keywords": keyword_list,
                "total_templates": len(templates),
                "relevant_templates": relevant_templates,
            },
            indent=2,
        )

    except json.JSONDecodeError:
        return json.dumps({"error": "Failed to parse App Store response"}, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Search failed: {str(e)}"}, indent=2)


deploy_project_tools = [
    web_search_tool,
    search_docker_hub,
    search_app_store,
]

# Example usage:
# result = web_search_tool.invoke("What's a 'node' in LangGraph?")
# result = search_docker_hub.invoke("nginx")
# result = search_app_store("nginx,web server,proxy")
# print(result)
