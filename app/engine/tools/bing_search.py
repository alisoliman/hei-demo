import os
from typing import List

import requests
from llama_index.core.tools import FunctionTool
from pydantic import BaseModel, Field


class BingSearchResults(BaseModel):
    """Results from Bing search."""
    query: str = Field(..., description="The search query")
    results: List[str] = Field(..., description="List of search results")


def bing_search(query: str, k: int = 3) -> BingSearchResults:
    """
    Search Bing for information about a query.
    
    Args:
        query (str): The search query
        k (int): Number of results to return (default: 3)
        
    Returns:
        BingSearchResults: Search results from Bing
    """
    subscription_key = os.getenv("BING_SEARCH_KEY")
    if not subscription_key:
        raise ValueError("BING_SEARCH_KEY environment variable is not set")

    endpoint = "https://api.bing.microsoft.com/v7.0/search"
    headers = {"Ocp-Apim-Subscription-Key": subscription_key}
    params = {
        "q": query,
        "count": k,
        "textDecorations": True,
        "textFormat": "HTML"
    }

    try:
        response = requests.get(endpoint, headers=headers, params=params)
        response.raise_for_status()
        search_results = response.json()
        
        # Extract snippets from search results
        results = []
        for item in search_results.get("webPages", {}).get("value", []):
            snippet = f"{item['name']}: {item['snippet']}"
            results.append(snippet)
            
        return BingSearchResults(query=query, results=results)
    except Exception as e:
        raise Exception(f"Error performing Bing search: {str(e)}")


def get_tools(**kwargs) -> List[FunctionTool]:
    """Get the Bing search tool."""
    return [
        FunctionTool.from_defaults(
            fn=bing_search,
            name="bing_search",
            description="Search Bing for information about a topic when the answer cannot be found in the existing knowledge base."
        )
    ]
