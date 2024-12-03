# flake8: noqa: E402
from dotenv import load_dotenv

load_dotenv()

import logging
import os
from typing import List, Optional

from app.engine.index import IndexType, get_storage_path
from app.engine.loaders import get_documents
from app.settings import init_settings
from llama_index.core import Document
from llama_index.core.indices import (
    VectorStoreIndex,
)
from llama_index.core.node_parser import SentenceSplitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


def generate_index(documents: List[Document], index_type: IndexType):
    """Generate an index for the given documents and index type."""
    storage_dir = get_storage_path(index_type)
    
    # Set private=false to mark the document as public (required for filtering)
    for doc in documents:
        doc.metadata["private"] = "false"

    # Configure node parser with appropriate chunk size
    chunk_size = 4096 if index_type == IndexType.VENUE else 1024
    node_parser = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=20)

    # Create index with settings
    logger.info(f"Creating new {index_type.value} index")
    index = VectorStoreIndex.from_documents(
        documents,
        show_progress=True,
        node_parser=node_parser,
    )
    
    # Store it for later
    os.makedirs(storage_dir, exist_ok=True)
    index.storage_context.persist(storage_dir)
    logger.info(f"Finished creating {index_type.value} index. Stored in {storage_dir}")


def generate_datasource(index_type: Optional[IndexType] = None):
    """Generate indices for the datasource. If index_type is specified, only generate that type."""
    init_settings()
    
    # Get all documents
    documents = get_documents()
    
    if index_type:
        # Generate specific index type
        generate_index(documents, index_type)
    else:
        # Generate both indices
        # Split documents based on type (venue vs general)
        venue_docs = [doc for doc in documents if doc.metadata.get("type") == "row"]
        general_docs = [doc for doc in documents if doc.metadata.get("type") != "row"]
        
        if venue_docs:
            generate_index(venue_docs, IndexType.VENUE)
        if general_docs:
            generate_index(general_docs, IndexType.GENERAL)


if __name__ == "__main__":
    import sys
    # Check if index type is specified as argument
    if len(sys.argv) > 1:
        try:
            index_type = IndexType(sys.argv[1].lower())
            generate_datasource(index_type)
        except ValueError:
            print(f"Invalid index type. Must be one of: {', '.join([t.value for t in IndexType])}")
            sys.exit(1)
    else:
        generate_datasource()
