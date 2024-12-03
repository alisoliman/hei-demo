import logging
import os
from typing import List

import pandas as pd
from llama_index.core import Document
from llama_index.core.schema import MetadataMode

logger = logging.getLogger(__name__)

def process_csv_file(file_path: str) -> List[Document]:
    """
    Process a CSV file and create structured documents that preserve the tabular format.
    Each row becomes a document with minimal metadata to avoid size issues.
    """
    try:
        # Read CSV file
        df = pd.read_csv(file_path)
        
        # Convert DataFrame to list of documents
        documents = []
        
        # Get the filename without extension
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Process each row
        for idx, row in df.iterrows():
            # Create content string with all information
            content_parts = []
            metadata = {
                "src": file_name,
                "idx": idx,
                "type": "row"
            }
            
            # Select key columns for metadata (adjust these based on your needs)
            key_columns = ["Venue Name", "City", "State"]  # Add important columns here
            
            for col in df.columns:
                value = str(row[col])
                content_parts.append(f"{col}: {value}")
                
                # Only add important columns to metadata
                if col in key_columns:
                    key = col.lower().replace(" ", "_")[:10]  # Limit key length
                    metadata[key] = value[:100]  # Limit value length
            
            # Create document
            content = "\n".join(content_parts)
            doc = Document(
                text=content,
                metadata=metadata,
                metadata_mode=MetadataMode.ALL,
                excluded_llm_metadata_keys=["idx", "src", "type"]
            )
            documents.append(doc)
            
        return documents
        
    except Exception as e:
        logger.error(f"Error processing CSV file {file_path}: {str(e)}")
        raise
