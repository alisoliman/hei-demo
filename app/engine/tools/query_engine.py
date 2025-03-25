import os
from typing import Optional, List, Dict

from llama_index.core.tools.query_engine import QueryEngineTool
from llama_index.core.query_engine import RetrieverQueryEngine
from app.engine.index import IndexType, IndexConfig, get_index
from llama_index.core.callbacks import CallbackManager
from .tripadvisor import get_tools as get_tripadvisor_tools
from .bing_search import get_tools as get_bing_tools


def create_query_engine(index, callback_manager: Optional[CallbackManager] = None, **kwargs):
    """
    Create a query engine for the given index.

    Args:
        index: The index to create a query engine for.
        callback_manager: Optional callback manager for the query engine
        kwargs: Additional parameters for the query engine, e.g: similarity_top_k
    """
    # Create a clean copy of kwargs to avoid modifying the original
    query_kwargs = kwargs.copy()
    
    # Remove callback_manager from kwargs if it exists to avoid duplicate
    query_kwargs.pop('callback_manager', None)
    
    # Handle top_k parameter
    top_k = int(os.getenv("TOP_K", 4))
    if top_k != 0 and query_kwargs.get("filters") is None:
        query_kwargs["similarity_top_k"] = top_k
    
    # If index is LlamaCloudIndex use auto_routed mode for better query results
    if (
        index.__class__.__name__ == "LlamaCloudIndex"
        and query_kwargs.get("auto_routed") is None
    ):
        query_kwargs["auto_routed"] = True

    # Create retriever with the cleaned kwargs
    retriever = index.as_retriever(**query_kwargs)
    
    # Create query engine directly using RetrieverQueryEngine
    return RetrieverQueryEngine(
        retriever=retriever,
        callback_manager=callback_manager
    )


def get_venue_query_tool(callback_manager: Optional[CallbackManager] = None, **kwargs) -> Optional[QueryEngineTool]:
    """
    Get a specialized query tool for venue-related queries.
    This tool is optimized for questions about bars, restaurants, and venues.
    
    Example queries:
    - Find bars in Sao Paulo that serve draft beer
    - What are the highest rated restaurants in Rio?
    - Show me venues with outdoor seating in Belo Horizonte
    - Which places have active Heineken promotions?
    """
    config = IndexConfig(index_type=IndexType.VENUE, callback_manager=callback_manager)
    index = get_index(config)
    if not index:
        return None
        
    description = """Use this tool for general questions about venues, bars, and restaurants.
    This tool is best for broad queries about multiple venues or discovering new places.
    
    For specific venues or making reservations:
    - Use 'search_venues_by_name' to find a specific venue and its TripAdvisor ID
    - Use 'make_reservation' with the TripAdvisor ID to make a reservation
    
    This tool provides information about:
    - Location (city, state, address)
    - Features (outdoor seating, beer types served)
    - Ratings and reviews
    - Opening hours
    - Promotions and special offers
    - Accessibility features
    - TripAdvisor information
    
    Example queries:
    - What bars in Sao Paulo serve draft beer?
    - Which restaurants have outdoor seating?
    - Tell me about venues with active promotions
    - What are the popular dining spots in this area?
    
    Note: For finding a specific venue or making reservations, use 'search_venues_by_name' instead."""
    
    query_engine = create_query_engine(index, callback_manager=callback_manager, **kwargs)
    return QueryEngineTool.from_defaults(
        query_engine=query_engine,
        name="venue_query",
        description=description,
    )


def get_general_query_tool(callback_manager: Optional[CallbackManager] = None, **kwargs) -> Optional[QueryEngineTool]:
    """
    Get a query tool for general document queries.
    This tool handles all non-venue related information.
    """
    config = IndexConfig(index_type=IndexType.GENERAL, callback_manager=callback_manager)
    index = get_index(config)
    if not index:
        return None
        
    description = """Use this tool to query general documentation and information.
    This includes any non-venue related content such as:
    - Company policies
    - General documentation
    - Product information
    - Other business documents
    
    Do not use this tool for venue-specific queries."""
    
    query_engine = create_query_engine(index, callback_manager=callback_manager, **kwargs)
    return QueryEngineTool.from_defaults(
        query_engine=query_engine,
        name="general_query",
        description=description,
    )


def get_all_query_tools(callback_manager: Optional[CallbackManager] = None, **kwargs) -> List[QueryEngineTool]:
    """Get all available query tools."""
    tools = []
    
    # Temporarily disabled venue query tool
    # venue_tool = get_venue_query_tool(callback_manager=callback_manager, **kwargs)
    # if venue_tool:
    #     tools.append(venue_tool)
        
    # Add general query tool
    general_tool = get_general_query_tool(callback_manager=callback_manager, **kwargs)
    if general_tool:
        tools.append(general_tool)
    
    # Add Bing search tool
    tools.extend(get_bing_tools())
    
    # Add TripAdvisor tool
    tools.extend(get_tripadvisor_tools())
    
    return tools


# Legacy support for old code
def get_query_engine_tool(
    index,
    name: Optional[str] = None,
    description: Optional[str] = None,
    callback_manager: Optional[CallbackManager] = None,
    **kwargs,
) -> QueryEngineTool:
    """Legacy function for backward compatibility."""
    if name is None:
        name = "query_index"
    if description is None:
        description = (
            "Use this tool to retrieve information about the text corpus from an index."
        )
    query_engine = create_query_engine(index, callback_manager=callback_manager, **kwargs)
    return QueryEngineTool.from_defaults(
        query_engine=query_engine,
        name=name,
        description=description,
    )
