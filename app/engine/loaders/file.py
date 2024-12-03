import os
import logging
from typing import Dict
from llama_parse import LlamaParse
from pydantic import BaseModel

from app.config import DATA_DIR

logger = logging.getLogger(__name__)


class FileLoaderConfig(BaseModel):
    use_llama_parse: bool = False


def llama_parse_parser():
    if os.getenv("LLAMA_CLOUD_API_KEY") is None:
        raise ValueError(
            "LLAMA_CLOUD_API_KEY environment variable is not set. "
            "Please set it in .env file or in your shell environment then run again!"
        )
    parser = LlamaParse(
        result_type="markdown",
        verbose=True,
        language="en",
        ignore_errors=False,
    )
    return parser


def llama_parse_extractor() -> Dict[str, LlamaParse]:
    from llama_parse.utils import SUPPORTED_FILE_TYPES

    parser = llama_parse_parser()
    return {file_type: parser for file_type in SUPPORTED_FILE_TYPES}


def get_file_documents(config: FileLoaderConfig):
    from llama_index.core.readers import SimpleDirectoryReader
    from app.engine.loaders.csv_loader import process_csv_file

    try:
        file_extractor = None
        if config.use_llama_parse:
            # LlamaParse is async first,
            # so we need to use nest_asyncio to run it in sync mode
            import nest_asyncio
            nest_asyncio.apply()
            file_extractor = llama_parse_extractor()

        # First, get all files in the directory
        all_files = []
        csv_files = []
        for root, _, files in os.walk(DATA_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                if file.lower().endswith('.csv'):
                    csv_files.append(file_path)
                else:
                    all_files.append(file_path)

        # Process non-CSV files using SimpleDirectoryReader
        documents = []
        if all_files:
            reader = SimpleDirectoryReader(
                input_files=all_files,
                file_extractor=file_extractor,
                filename_as_id=True,
            )
            documents.extend(reader.load_data())

        # Process CSV files using our custom processor
        for csv_file in csv_files:
            logger.info(f"Processing CSV file: {csv_file}")
            csv_documents = process_csv_file(csv_file)
            documents.extend(csv_documents)

        return documents
    except Exception as e:
        logger.error(f"Error in get_file_documents: {str(e)}")
        raise
