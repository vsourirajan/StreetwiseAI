#!/usr/bin/env python3
"""Quick check of zoning chunks file structure."""

import json
from pathlib import Path

chunks_path = Path("data/zoning/zoning_chunks.jsonl")

if chunks_path.exists():
    print(f"File exists: {chunks_path}")
    print(f"File size: {chunks_path.stat().st_size / 1024 / 1024:.1f} MB")
    
    with chunks_path.open() as f:
        for i, line in enumerate(f):
            if i >= 3:  # Only show first 3 lines
                break
            try:
                data = json.loads(line.strip())
                print(f"\n--- Line {i+1} ---")
                print(f"Keys: {list(data.keys())}")
                print(f"ID: {data.get('id')}")
                print(f"Text length: {len(data.get('text', ''))}")
                print(f"Text preview: {data.get('text', '')[:100]}...")
            except Exception as e:
                print(f"Error parsing line {i+1}: {e}")
else:
    print(f"File not found: {chunks_path}") 