import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from citybrain.ingest.embeddings import index_jsonl


def setup_logging():
    """Configure logging for the indexing script."""
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Create logs directory if it doesn't exist
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(logs_dir / "indexing.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)


def main():
    logger = setup_logging()
    
    logger.info("=" * 50)
    logger.info("NYC ZONING CHUNKS INDEXING TO PINECONE")
    logger.info("=" * 50)
    
    jsonl_path = Path("data/zoning/zoning_chunks.jsonl")
    
    if not jsonl_path.exists():
        logger.error(f"Zoning chunks file not found: {jsonl_path}")
        logger.error("Run scripts/local_ingest.py first to generate zoning_chunks.jsonl")
        sys.exit(1)
    
    logger.info(f"Found zoning chunks file: {jsonl_path}")
    logger.info(f"File size: {jsonl_path.stat().st_size:,} bytes")
    
    try:
        n = index_jsonl(jsonl_path, namespace="zoning-nyc")
        logger.info("=" * 50)
        logger.info(f"✓ SUCCESS: Indexed {n} zoning chunks to Pinecone")
        logger.info("=" * 50)
        logger.info("Next steps:")
        logger.info("1. Your zoning regulations are now searchable in Pinecone")
        logger.info("2. You can use the retrieval layer to query relevant zoning rules")
        logger.info("3. Check the logs for any warnings or issues")
        
    except Exception as e:
        logger.error("=" * 50)
        logger.error("✗ INDEXING FAILED!")
        logger.error("=" * 50)
        logger.error(f"Error: {str(e)}")
        logger.exception("Full error details:")
        sys.exit(1)


if __name__ == "__main__":
    main()