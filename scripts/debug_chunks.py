#!/usr/bin/env python3
"""Debug script to see exactly what's in the zoning chunks file."""

import json
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from citybrain.config import DATA_DIR


def debug_chunks():
    """Debug the zoning chunks file parsing."""
    chunks_path = DATA_DIR / "zoning" / "zoning_chunks.jsonl"
    
    if not chunks_path.exists():
        print(f"❌ File not found: {chunks_path}")
        return
    
    print(f"📁 File: {chunks_path}")
    print(f"📊 Size: {chunks_path.stat().st_size / 1024 / 1024:.1f} MB")
    print()
    
    # Read and examine the first few lines
    with chunks_path.open() as f:
        for line_num in range(1, 6):  # First 5 lines
            line = f.readline()
            if not line:
                break
                
            print(f"🔍 --- Line {line_num} ---")
            print(f"Raw line length: {len(line)} characters")
            print(f"Raw line (first 200 chars): {repr(line[:200])}")
            print()
            
            # Try to parse as JSON
            try:
                data = json.loads(line.strip())
                print(f"✅ JSON parsed successfully")
                print(f"Data type: {type(data)}")
                print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                
                if isinstance(data, dict):
                    for key, value in data.items():
                        if key == 'text':
                            print(f"Text key value type: {type(value)}")
                            print(f"Text key value length: {len(str(value)) if value else 0}")
                            print(f"Text key value preview: {repr(str(value)[:100]) if value else 'None'}")
                        else:
                            print(f"{key}: {type(value)} = {repr(value)[:100]}")
                print()
                
            except json.JSONDecodeError as e:
                print(f"❌ JSON parse error: {e}")
                print(f"Error position: {e.pos}")
                print(f"Line content around error: {line[max(0, e.pos-20):e.pos+20]}")
                print()
            except Exception as e:
                print(f"❌ Other error: {e}")
                print()


if __name__ == "__main__":
    debug_chunks() 