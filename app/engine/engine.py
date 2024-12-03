import os
from typing import List

from llama_index.core.agent import AgentRunner
from llama_index.core.callbacks import CallbackManager
from llama_index.core.settings import Settings
from llama_index.core.tools import BaseTool

from app.engine.index import IndexConfig
from app.engine.tools import ToolFactory
from app.engine.tools.query_engine import get_all_query_tools


def get_chat_engine(params=None, event_handlers=None, **kwargs):
    system_prompt = os.getenv("SYSTEM_PROMPT", """You are a helpful assistant with access to multiple knowledge bases. 
    For venue-related questions (about bars, restaurants, locations, etc.), use the venue_query tool. 
    For all other queries about company information, documentation, or general topics, use the general_query tool.""")
    
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
