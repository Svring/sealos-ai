"""
App Store search tool for deploy project operations.
Searches for App Store templates using TF-IDF + Cosine Similarity.
"""

from langchain_core.tools import tool
import requests
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import Dict, Any


def process_template_data(template: dict) -> dict:
    """
    Process template data to include only important fields.

    Args:
        template (dict): Raw template data from the API

    Returns:
        dict: Processed template with only important fields
    """
    description = (
        template.get("spec", {}).get("i18n", {}).get("en", {}).get("description")
        or template.get("spec", {}).get("description")
        or "No description available"
    )
    processed = {
        "name": template.get("metadata", {}).get("name", ""),
        "gitRepo": template.get("spec", {}).get("gitRepo", ""),
        "description": description,
        "inputs": template.get("spec", {}).get("inputs", {}),
    }
    return processed


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
def search_app_store(keywords: str) -> Dict[str, Any]:
    """
    Search for App Store templates using TF-IDF + Cosine Similarity to find the most relevant matches.

    Args:
        keywords (str): Comma-separated keywords to search for (e.g., "nginx,web server,proxy")

    Returns:
        Dict containing the action and payload with the top 3 most relevant templates ranked by similarity score.
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
            return {
                "action": "search_app_store",
                "payload": {
                    "error": f"Unexpected response format: {type(templates_data)}"
                },
            }

        if not templates:
            return {
                "action": "search_app_store",
                "payload": {"error": "No templates found"},
            }

        # Extract text segments for similarity matching
        # Combine title, description, and categories for better matching
        text_segments = []
        for template in templates:
            segment_parts = []
            spec = template.get("spec", {})
            if spec.get("title"):
                segment_parts.append(spec["title"])
            if spec.get("description"):
                segment_parts.append(spec["description"])
            if spec.get("categories"):
                if isinstance(spec["categories"], list):
                    segment_parts.extend(spec["categories"])
                else:
                    segment_parts.append(str(spec["categories"]))

            text_segments.append(" ".join(segment_parts))

        # Parse keywords
        keyword_list = [kw.strip() for kw in keywords.split(",") if kw.strip()]

        if not keyword_list:
            return {
                "action": "search_app_store",
                "payload": {"error": "No valid keywords provided"},
            }

        # Find most relevant templates using TF-IDF similarity
        relevant_segments = find_relevant_text_segments(
            text_segments, keyword_list, top_k=3
        )

        # Map back to original template data and process
        relevant_templates = []
        for segment, similarity_score in relevant_segments:
            # Find the original template for this segment
            for template in templates:
                template_text = " ".join(
                    [
                        template.get("spec", {}).get("title", ""),
                        template.get("spec", {}).get("description", ""),
                        " ".join(template.get("spec", {}).get("categories", [])),
                    ]
                )
                if template_text.strip() == segment.strip():
                    # Process template to include only important fields
                    processed_template = process_template_data(template)
                    processed_template["similarity_score"] = float(similarity_score)
                    relevant_templates.append(processed_template)
                    break

        return {
            "action": "search_app_store",
            "payload": {
                "query_keywords": keyword_list,
                "total_templates": len(templates),
                "relevant_templates": relevant_templates,
            },
        }

    except json.JSONDecodeError:
        return {
            "action": "search_app_store",
            "payload": {"error": "Failed to parse App Store response"},
        }
    except Exception as e:
        return {
            "action": "search_app_store",
            "payload": {"error": f"Search failed: {str(e)}"},
        }


if __name__ == "__main__":
    # Test the App Store search tool
    # Run with: python -m src.graph.orca.tools.deploy_project_tool.search_app_store

    print("Testing search_app_store...")
    try:
        result = search_app_store.invoke("wrenai")
        print("✅ App Store search successful!")
        print(result)
    except Exception as e:
        print(f"❌ App Store search failed: {e}")

    print(f"Tool name: {search_app_store.name}")
    print(f"Tool description: {search_app_store.description}")
