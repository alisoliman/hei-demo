import logging
import os
from datetime import timedelta
from enum import Enum
from typing import Optional

from cachetools import TTLCache, cached  # type: ignore
from llama_index.core.callbacks import CallbackManager
from llama_index.core.indices import load_index_from_storage
from llama_index.core.storage import StorageContext
from pydantic import BaseModel, Field

logger = logging.getLogger("uvicorn")


class IndexType(str, Enum):
    GENERAL = "general"
    VENUE = "venue"


class IndexConfig(BaseModel):
    callback_manager: Optional[CallbackManager] = Field(default=None)
    index_type: IndexType = Field(default=IndexType.GENERAL)


def get_storage_path(index_type: IndexType) -> str:
    """Get the storage path for a specific index type."""
    base_dir = os.getenv("STORAGE_DIR", "storage")
    if index_type == IndexType.VENUE:
        return os.path.join(base_dir, "venue")
    return os.path.join(base_dir, "general")


def get_index(config: IndexConfig = None):
    if config is None:
        config = IndexConfig()

    storage_dir = get_storage_path(config.index_type)
    
    # check if storage already exists
    if not os.path.exists(storage_dir):
        return None

    # load the existing index
    logger.info(f"Loading {config.index_type.value} index from {storage_dir}...")
    storage_context = get_storage_context(storage_dir)
    index = load_index_from_storage(
        storage_context, callback_manager=config.callback_manager
    )
    logger.info(f"Finished loading {config.index_type.value} index from {storage_dir}")
    return index


@cached(
    TTLCache(maxsize=20, ttl=timedelta(minutes=5).total_seconds()),
    key=lambda persist_dir, *args, **kwargs: f"storage_context_{persist_dir}",
)
def get_storage_context(persist_dir: str) -> StorageContext:
    return StorageContext.from_defaults(persist_dir=persist_dir)
