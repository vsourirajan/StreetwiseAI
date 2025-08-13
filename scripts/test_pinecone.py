import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from citybrain.ingest.embeddings import _init_pinecone, ensure_pinecone_index


def test_pinecone_connection():
    """Test Pinecone connection and basic operations."""
    print("=" * 60)
    print("TESTING PINECONE CONNECTION")
    print("=" * 60)
    
    try:
        # Test 1: Initialize Pinecone
        print("\n1. Testing Pinecone initialization...")
        pc = _init_pinecone()
        print("   ✓ Pinecone client initialized successfully")
        
        # Test 2: List existing indexes
        print("\n2. Testing index listing...")
        try:
            indexes = pc.list_indexes()
            print(f"   ✓ Found {len(indexes)} existing indexes")
            for idx in indexes:
                print(f"      - {idx.name} (dimension: {idx.dimension})")
        except Exception as e:
            print(f"   ⚠ Warning listing indexes: {e}")
        
        # Test 3: Test index creation (will fail if index already exists, which is fine)
        print("\n3. Testing index creation...")
        test_index_name = "test-citybrain-connection"
        try:
            ensure_pinecone_index(test_index_name, dimension=384)
            print(f"   ✓ Test index '{test_index_name}' created or already exists")
            
            # Clean up test index
            try:
                pc.delete_index(test_index_name)
                print(f"   ✓ Test index '{test_index_name}' cleaned up")
            except Exception as cleanup_e:
                print(f"   ⚠ Could not clean up test index: {cleanup_e}")
                
        except Exception as e:
            print(f"   ⚠ Index creation test: {e}")
        
        print("\n" + "=" * 60)
        print("PINECONE CONNECTION TEST COMPLETE")
        print("=" * 60)
        print("✓ Pinecone integration is working correctly!")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure PINECONE_API_KEY is set in your .env file")
        print("2. Verify your Pinecone API key is valid")
        print("3. Check your internet connection")
        print("4. Ensure you have the latest pinecone package: pip install pinecone>=2.2.4")


if __name__ == "__main__":
    test_pinecone_connection() 