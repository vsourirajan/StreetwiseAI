#!/usr/bin/env python3
"""
Test script to examine the zoning chunks file and verify text content.
"""

import sys
import argparse
import logging
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from citybrain.config import DATA_DIR


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")


def examine_zoning_chunks():
    """Examine the zoning chunks file to see what text content is available."""
    logger = logging.getLogger(__name__)
    
    chunks_path = DATA_DIR / "zoning" / "zoning_chunks.jsonl"
    
    if not chunks_path.exists():
        logger.error(f"Zoning chunks file not found: {chunks_path}")
        logger.info("You may need to run the ingestion pipeline first:")
        logger.info("python scripts/local_ingest.py")
        return
    
    logger.info(f"Found zoning chunks file: {chunks_path}")
    
    # Count lines and examine content
    chunks = []
    try:
        with chunks_path.open() as f:
            for line_num, line in enumerate(f, 1):
                try:
                    chunk_data = json.loads(line.strip())
                    chunks.append(chunk_data)
                    
                    # Show first few chunks in detail
                    if line_num <= 3:
                        logger.info(f"\n--- Chunk {line_num} ---")
                        logger.info(f"ID: {chunk_data.get('id')}")
                        logger.info(f"Text length: {len(chunk_data.get('text', ''))}")
                        logger.info(f"Metadata keys: {list(chunk_data.get('metadata', {}).keys())}")
                        logger.info(f"Sample text: {chunk_data.get('text', '')[:200]}...")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing line {line_num}: {e}")
                    continue
        
        logger.info(f"\nTotal chunks: {len(chunks)}")
        
        if chunks:
            # Show some statistics
            text_lengths = [len(chunk.get('text', '')) for chunk in chunks]
            logger.info(f"Text length stats:")
            logger.info(f"  Min: {min(text_lengths)} chars")
            logger.info(f"  Max: {max(text_lengths)} chars")
            logger.info(f"  Avg: {sum(text_lengths) / len(text_lengths):.1f} chars")
            
            # Check for text content
            chunks_with_text = [c for c in chunks if c.get('text')]
            logger.info(f"Chunks with text content: {len(chunks_with_text)}")
            
            if chunks_with_text:
                logger.info("✓ Text content is available for retrieval")
            else:
                logger.warning("✗ No text content found in chunks")
                
    except Exception as e:
        logger.error(f"Error reading zoning chunks file: {e}")


def main():
    parser = argparse.ArgumentParser(description="Examine zoning chunks file contents")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")

    args = parser.parse_args()
    setup_logging(args.verbose)

    try:
        examine_zoning_chunks()
    except Exception as e:
        print(f"Error examining zoning chunks: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 