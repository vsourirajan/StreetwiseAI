import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from citybrain.ingest.embeddings import get_available_models, get_model_info, embed_texts


def test_embeddings():
    """Test Hugging Face embeddings functionality."""
    print("=" * 60)
    print("TESTING HUGGING FACE EMBEDDINGS")
    print("=" * 60)
    
    # Test 1: List available models
    print("\n1. Available Models:")
    models = get_available_models()
    for i, model in enumerate(models, 1):
        print(f"   {i}. {model}")
    
    # Test 2: Get model info for default model
    print("\n2. Default Model Info:")
    default_model = "all-MiniLM-L6-v2"
    info = get_model_info(default_model)
    if "error" not in info:
        print(f"   Model: {info['name']}")
        print(f"   Dimension: {info['dimension']}")
        print(f"   Max Sequence Length: {info['max_seq_length']}")
        print(f"   Device: {info['device']}")
    else:
        print(f"   Error: {info['error']}")
        return
    
    # Test 3: Generate sample embeddings
    print("\n3. Testing Embedding Generation:")
    sample_texts = [
        "This is a test sentence about urban planning.",
        "Zoning regulations control building heights and uses.",
        "Traffic patterns affect neighborhood development."
    ]
    
    try:
        embeddings = embed_texts(sample_texts, model_name=default_model)
        print(f"   ✓ Generated {len(embeddings)} embeddings")
        print(f"   ✓ Each embedding has {len(embeddings[0])} dimensions")
        
        # Show first few values of first embedding
        first_embedding = embeddings[0][:5]
        print(f"   ✓ Sample values: {[f'{x:.4f}' for x in first_embedding]}...")
        
    except Exception as e:
        print(f"   ✗ Error generating embeddings: {e}")
        return
    
    # Test 4: Performance test with larger batch
    print("\n4. Performance Test:")
    larger_texts = [f"Sample text number {i} for testing embedding generation." for i in range(100)]
    
    try:
        import time
        start_time = time.time()
        embeddings = embed_texts(larger_texts, model_name=default_model)
        end_time = time.time()
        
        print(f"   ✓ Generated {len(embeddings)} embeddings in {end_time - start_time:.2f} seconds")
        print(f"   ✓ Rate: {len(embeddings)/(end_time - start_time):.1f} embeddings/second")
        
    except Exception as e:
        print(f"   ✗ Error in performance test: {e}")
    
    print("\n" + "=" * 60)
    print("EMBEDDING TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    test_embeddings() 