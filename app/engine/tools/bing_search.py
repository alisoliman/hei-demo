import os
import requests
from typing import List
from pydantic import BaseModel, Field
from llama_index.core.tools import FunctionTool


class BingSearchResults(BaseModel):
    """Results from Bing search."""
    query: str = Field(..., description="The search query")
    results: List[str] = Field(..., description="List of search results")


def bing_search(query: str, k: int = 3) -> BingSearchResults:
    """
    Search Bing for information about a query using the REST API.
    
    Args:
        query (str): The search query
        k (int): Number of results to return (default: 3)
        
    Returns:
        BingSearchResults: Search results from Bing
    """
    subscription_key = os.getenv("BING_SEARCH_KEY")
    
    if not subscription_key:
        raise ValueError("BING_SEARCH_KEY environment variable is not set")

    search_url = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    params = {
        "q": query,
        "count": k,
        "textDecorations": True,
        "textFormat": "HTML",
        "safeSearch": "Strict",
        "mkt": "en-US"
    }

    try:
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        
        search_results = response.json()
        results = []
        
        # Extract web page results
        if "webPages" in search_results and "value" in search_results["webPages"]:
            for page in search_results["webPages"]["value"][:k]:
                result = f"{page['name']}: {page['snippet']}"
                results.append(result)
                
        # If no web pages, try news results
        if not results and "news" in search_results and "value" in search_results["news"]:
            for news in search_results["news"]["value"][:k]:
                result = f"[News] {news['name']}: {news['description']}"
                results.append(result)

        return BingSearchResults(query=query, results=results)

    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        if response.status_code == 401:
            error_msg = "Invalid or expired Bing Search API key. Please check your API key."
        elif response.status_code == 403:
            error_msg = "Access denied. Please check if your API key has the correct permissions."
        elif response.status_code == 429:
            error_msg = "Rate limit exceeded. Please try again later."
        
        raise Exception(f"Error performing Bing search: {error_msg}")


def get_tools(**kwargs) -> List[FunctionTool]:
    """Get the Bing search tool."""
    return [
        FunctionTool.from_defaults(
            fn=bing_search,
            name="bing_search",
            description="""Use this tool ONLY when information cannot be found in our existing knowledge base and when the query requires current or external information. Specifically:

1. For general world knowledge or current events NOT related to venues or company information
2. For technical information about programming, frameworks, or tools
3. For verification of external facts or statistics

DO NOT use this tool for:
- Venue-related queries (use venue_query instead)
- Company documentation or policies (use general_query instead)
- Internal business information

Example appropriate queries:
- "What are the latest web development best practices?"
- "What is the current weather in Amsterdam?"
- "What are recent changes in beer industry regulations?"
"""
        )
    ]
