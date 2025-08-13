import sys
import logging
import time
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from citybrain.ingest.zoning_text import download_zoning_text, chunk_and_write_embeddings_corpus
from citybrain.ingest.zoning_shapes import download_zoning_shapes
from citybrain.ingest.traffic_counts import download_traffic_counts
# from citybrain.ingest.demographics import download_demographics


def setup_logging():
    """Configure logging with timestamps and formatting."""
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Create logs directory if it doesn't exist
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"ingestion_{timestamp}.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting ingestion process at {datetime.now()}")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Project root: {project_root}")
    
    return logger


def run_with_logging(func, func_name, logger):
    """Execute a function with timing and error logging."""
    start_time = time.time()
    logger.info(f"Starting {func_name}...")
    
    try:
        result = func()
        elapsed = time.time() - start_time
        logger.info(f"✓ {func_name} completed successfully in {elapsed:.2f} seconds")
        return result
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"✗ {func_name} failed after {elapsed:.2f} seconds: {str(e)}")
        logger.exception(f"Full error details for {func_name}:")
        raise


def main():
    logger = setup_logging()
    
    try:
        logger.info("=" * 60)
        logger.info("CITY BRAIN DATA INGESTION PIPELINE")
        logger.info("=" * 60)
        
        # Step 1: Zoning Text
        logger.info("\n" + "-" * 40)
        logger.info("STEP 1: NYC Zoning Resolution Text")
        logger.info("-" * 40)
        run_with_logging(download_zoning_text, "Zoning text download", logger)
        
        # Step 2: Zoning Text Chunking
        logger.info("\n" + "-" * 40)
        logger.info("STEP 2: Zoning Text Chunking & Embeddings Corpus")
        logger.info("-" * 40)
        run_with_logging(chunk_and_write_embeddings_corpus, "Zoning text chunking", logger)
        
        # Step 3: Zoning Shapes
        logger.info("\n" + "-" * 40)
        logger.info("STEP 3: NYC Zoning District Shapes")
        logger.info("-" * 40)
        run_with_logging(download_zoning_shapes, "Zoning shapes download", logger)
        
        # Step 4: Traffic Counts
        logger.info("\n" + "-" * 40)
        logger.info("STEP 4: NYC DOT Traffic Counts")
        logger.info("-" * 40)
        run_with_logging(download_traffic_counts, "Traffic counts download", logger)
        
        # Step 6: Demographics (commented out)
        # logger.info("\n" + "-" * 40)
        # logger.info("STEP 6: NYC Demographics & Census Data")
        # logger.info("-" * 40)
        # run_with_logging(download_demographics, "Demographics download", logger)
        
        # Summary
        total_time = time.time() - time.time()  # This will be 0, need to track properly
        logger.info("\n" + "=" * 60)
        logger.info("INGESTION PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info("Next steps:")
        logger.info("1. Review the generated data files in the 'data/' directory")
        logger.info("2. Run 'python scripts/index_zoning.py' to index zoning chunks to Pinecone")
        logger.info("3. Check logs for any warnings or issues")
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error("INGESTION PIPELINE FAILED!")
        logger.error("=" * 60)
        logger.error(f"Error: {str(e)}")
        logger.exception("Full error details:")
        sys.exit(1)


if __name__ == "__main__":
    main()