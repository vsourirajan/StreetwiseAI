#!/usr/bin/env python3
"""Show the mapping from Pinecone IDs to actual text content."""

import json
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from citybrain.config import DATA_DIR


def show_text_mapping():
    """Show the mapping from IDs to text content."""
    chunks_path = DATA_DIR / "zoning" / "zoning_chunks.jsonl"
    
    if not chunks_path.exists():
        print(f"❌ Zoning chunks file not found: {chunks_path}")
        print("You need to run the ingestion pipeline first:")
        print("python scripts/local_ingest.py")
        return
    
    print(f"📁 Found zoning chunks file: {chunks_path}")
    print(f"📊 File size: {chunks_path.stat().st_size / 1024 / 1024:.1f} MB")
    print()
    
    # Load and show the mapping
    chunks_map = {}
    total_lines = 0
    
    with chunks_path.open() as f:
        for line_num, line in enumerate(f, 1):
            total_lines += 1
            try:
                chunk_data = json.loads(line.strip())
                chunk_id = chunk_data.get("id")
                chunk_text = chunk_data.get("text")
                
                if chunk_id and chunk_text:
                    chunks_map[chunk_id] = chunk_text
                    
                    # Show first 3 chunks in detail
                    if line_num <= 3:
                        print(f"🔍 --- Chunk {line_num} ---")
                        print(f"ID: {chunk_id}")
                        print(f"Text length: {len(chunk_text)} characters")
                        print(f"Full text content:")
                        print("=" * 50)
                        print(chunk_text)
                        print("=" * 50)
                        print()
                        
            except json.JSONDecodeError as e:
                print(f"❌ Error parsing line {line_num}: {e}")
                continue
    
    print(f"📈 Summary:")
    print(f"  Total lines processed: {total_lines}")
    print(f"  Valid chunks with text: {len(chunks_map)}")
    print(f"  Sample IDs: {list(chunks_map.keys())[:10]}")
    
    # Test lookup for a specific ID
    if chunks_map:
        sample_id = list(chunks_map.keys())[0]
        print(f"\n🧪 Test lookup for ID '{sample_id}':")
        print(f"Text content: {chunks_map[sample_id][:200]}...")


if __name__ == "__main__":
    show_text_mapping() 