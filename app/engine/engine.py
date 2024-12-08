import os
from typing import List

from llama_index.core.agent import AgentRunner
from llama_index.core.callbacks import CallbackManager
from llama_index.core.settings import Settings
from llama_index.core.tools import BaseTool

from app.engine.index import IndexConfig
from app.engine.tools import ToolFactory
from app.engine.tools.query_engine import get_all_query_tools
from app.engine.tools.tripadvisor import get_tools as get_tripadvisor_tools
from app.engine.tools.chinchin_api import get_tools as get_chinchin_tools

def get_chat_engine(params=None, event_handlers=None, **kwargs):
    system_prompt = os.getenv("SYSTEM_PROMPT", """You are a helpful assistant with access to multiple knowledge bases. 
    Follow these rules when handling queries:
    
    1. When asked about reviews or ratings for a venue:
       ALWAYS break it down into two explicit steps:
       Step 1: Say "Let me first find the TripAdvisor ID for this venue" and use venue_query with this exact query format:
              "[Venue Name], TripAdvisor ID"
       Step 2: Look for these specific patterns in the response:
              - "TripAdvisor ID: [number]"
              - "The TripAdvisor location ID for this venue is [number]"
              - "To get TripAdvisor reviews, use ID: [number]"
       Step 3: Only after finding a valid TripAdvisor ID (5-10 digit number), use the tripadvisor tool
       
    2. For other venue-related questions (about bars, restaurants, locations):
       - Use the venue_query tool to get venue details
       - NEVER pass venue names directly to the tripadvisor tool
       
    3. For all other queries about company information or general topics:
       - Use the general_query tool
       
    4. TripAdvisor Rules:
       - Valid TripAdvisor IDs are 5-10 digit numbers (e.g., 12345 or 1234567890)
       - NEVER use street numbers, phone numbers, or other numeric values as IDs
       - NEVER use the tripadvisor tool without first finding a valid ID
       - If you can't find a TripAdvisor ID, inform the user and provide other available venue information""")
    
    tools: List[BaseTool] = []
    callback_manager = CallbackManager(handlers=event_handlers or [])

    # Prepare parameters, excluding callback_manager to avoid duplication
    query_params = (params or {}).copy()
    query_params.pop('callback_manager', None)
    kwargs.pop('callback_manager', None)

    # Add specialized query tools
    query_tools = get_all_query_tools(
        callback_manager=callback_manager,
        **query_params,
        **kwargs
    )
    tools.extend(query_tools)

    # Add TripAdvisor tools
    tools.extend(get_tripadvisor_tools())
    
    # Add Chinchin API tools
    tools.extend(get_chinchin_tools())

    # Add additional tools
    configured_tools: List[BaseTool] = ToolFactory.from_env()
    tools.extend(configured_tools)

    return AgentRunner.from_llm(
        llm=Settings.llm,
        tools=tools,
        system_prompt=system_prompt,
        callback_manager=callback_manager,
        verbose=True,
    )
