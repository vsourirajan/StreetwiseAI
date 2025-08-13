#!/usr/bin/env python3
"""
Test script to examine the actual contents of the Pinecone database.
This will show what metadata is available for each vector.
"""

import sys
import argparse
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from citybrain.config import PINECONE_INDEX_NAME
from citybrain.ingest.embeddings import _init_pinecone


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")


def examine_pinecone_contents():
    """Examine what's actually stored in the Pinecone database."""
    logger = logging.getLogger(__name__)
    
    try:
        pc = _init_pinecone()
        index = pc.Index(PINECONE_INDEX_NAME)
        
        # Get index stats
        stats = index.describe_index_stats()
        logger.info(f"Index stats: {stats}")
        
        # Query for a few sample vectors to see their metadata
        logger.info("Querying for sample vectors...")
        
        # Use a simple query to get some results
        sample_query = "zoning regulations"
        
        # We need to create a dummy vector of the right dimension
        # For all-MiniLM-L6-v2, this is 384 dimensions
        dummy_vector = [0.0] * 384
        
        try:
            results = index.query(
                vector=dummy_vector,
                top_k=5,
                include_metadata=True,
                namespace="zoning-nyc"
            )
            
            logger.info(f"Query results: {results}")
            
            # Extract matches
            matches = getattr(results, "matches", []) or results.get("matches", [])
            
            if matches:
                logger.info(f"Found {len(matches)} matches")
                for i, match in enumerate(matches):
                    logger.info(f"\n--- Match {i+1} ---")
                    logger.info(f"ID: {match.get('id')}")
                    logger.info(f"Score: {match.get('score')}")
                    
                    metadata = match.get("metadata") if isinstance(match, dict) else getattr(match, "metadata", {})
                    logger.info(f"Metadata keys: {list(metadata.keys())}")
                    logger.info(f"Metadata: {metadata}")
                    
                    # Check if text is in metadata
                    if "text" in metadata:
                        logger.info(f"Text content: {metadata['text'][:200]}...")
                    else:
                        logger.info("No text content in metadata")
                        
            else:
                logger.warning("No matches found")
                
        except Exception as e:
            logger.error(f"Error querying index: {e}")
            
    except Exception as e:
        logger.error(f"Error accessing Pinecone: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(description="Examine Pinecone database contents")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args()
    setup_logging(args.verbose)

    try:
        examine_pinecone_contents()
    except Exception as e:
        print(f"Error examining Pinecone contents: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 