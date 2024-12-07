import logging
import os
from typing import List

import pandas as pd
from llama_index.core import Document
from llama_index.core.schema import MetadataMode

logger = logging.getLogger(__name__)

def process_csv_file(file_path: str) -> List[Document]:
    """
    Process a CSV file and create structured documents.
    Each row becomes a document with its own chunk, preserving column names as context.
    """
    try:
        # Read CSV file
        df = pd.read_csv(file_path)
        
        # Get the filename without extension
        file_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # Create a list to store documents
        documents = []
        
        # Process each row
        for idx, row in df.iterrows():
            # Create metadata dictionary
            metadata = {
                "src": file_name,
                "idx": idx,
                "type": "row"
            }
            
            # Build content with column names as context
            content_parts = []
            
            # First, add TripAdvisor ID if it exists (make it prominent)
            if 'TripAdvisor ID' in df.columns:
                tripadvisor_id = str(row['TripAdvisor ID']).strip()
                if tripadvisor_id:
                    content_parts.extend([
                        f"TripAdvisor ID: {tripadvisor_id}",
                        f"The TripAdvisor location ID for this venue is {tripadvisor_id}",
                        f"To get TripAdvisor reviews, use ID: {tripadvisor_id}",
                        ""  # Empty line for separation
                    ])
                    metadata["tripadvisor_id"] = tripadvisor_id
            
            # Add venue name if it exists (also make it prominent)
            venue_name_cols = ['OutletName', 'Venue Name', 'g_name']
            for col in venue_name_cols:
                if col in df.columns:
                    value = str(row[col]).strip()
                    if value:
                        content_parts.extend([
                            f"Venue Name: {value}",
                            ""  # Empty line for separation
                        ])
                        metadata["venue_name"] = value
                        break
            
            # Add all other fields with their column names
            for col in df.columns:
                value = str(row[col]).strip()
                if value and col not in ['TripAdvisor ID']:  # Skip TripAdvisor ID as it's already added
                    content_parts.append(f"{col}: {value}")
            
            # Create document with the formatted content
            content = "\n".join(content_parts)
            doc = Document(
                text=content,
                metadata=metadata,
            )
            documents.append(doc)
        
        return documents
        
    except Exception as e:
        logger.error(f"Error processing CSV file {file_path}: {str(e)}")
        raise
