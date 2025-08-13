from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterable, List, Dict

from citybrain.config import PINECONE_API_KEY, PINECONE_INDEX_NAME


def _init_pinecone():
    from pinecone import Pinecone  # type: ignore

    if not PINECONE_API_KEY:
        raise RuntimeError("PINECONE_API_KEY not set")
    return Pinecone(api_key=PINECONE_API_KEY)


def _init_embedding_model(model_name: str = "all-MiniLM-L6-v2"):
    """Initialize Hugging Face sentence transformer model."""
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        logger = logging.getLogger(__name__)
        logger.info(f"Loading Hugging Face model: {model_name}")
        model = SentenceTransformer(model_name)
        logger.info(f"✓ Model loaded successfully (dimension: {model.get_sentence_embedding_dimension()})")
        return model
    except ImportError:
        raise RuntimeError(
            "sentence-transformers not installed. Install with: pip install sentence-transformers"
        )


def ensure_pinecone_index(index_name: str = PINECONE_INDEX_NAME, dimension: int = 384) -> None:
    """Ensure Pinecone index exists. Default dimension is for all-MiniLM-L6-v2."""
    logger = logging.getLogger(__name__)
    pc = _init_pinecone()
    
    try:
        # Check if index exists
        existing_indexes = pc.list_indexes()
        index_names = [idx.name for idx in existing_indexes]
        
        if index_name not in index_names:
            logger.info(f"Creating Pinecone index: {index_name} (dimension: {dimension})")
            pc.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",
                spec={"serverless": {"cloud": "aws", "region": "us-east-1"}},
            )
            logger.info(f"✓ Index '{index_name}' created successfully")
        else:
            logger.info(f"✓ Index '{index_name}' already exists")
            
    except Exception as e:
        logger.error(f"Error checking/creating Pinecone index: {e}")
        raise


def embed_texts(texts: List[str], model_name: str = "all-MiniLM-L6-v2") -> List[List[float]]:
    """Generate embeddings using Hugging Face sentence transformers."""
    logger = logging.getLogger(__name__)
    model = _init_embedding_model(model_name)
    
    logger.info(f"Generating embeddings for {len(texts)} texts using {model_name}")
    
    try:
        # Generate embeddings in batches for efficiency
        batch_size = 32  # Adjust based on your GPU/memory
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = model.encode(batch, convert_to_tensor=False)
            all_embeddings.extend(batch_embeddings.tolist())
            
            logger.debug(f"Processed batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
        
        logger.info(f"✓ Generated {len(all_embeddings)} embeddings successfully")
        return all_embeddings
        
    except Exception as e:
        logger.error(f"✗ Failed to generate embeddings: {e}")
        raise


def index_documents(docs: List[Dict], namespace: str | None = None, index_name: str = PINECONE_INDEX_NAME, model_name: str = "all-MiniLM-L6-v2") -> int:
    """Index documents to Pinecone using Hugging Face embeddings."""
    logger = logging.getLogger(__name__)
    pc = _init_pinecone()
    
    try:
        index = pc.Index(index_name)
    except Exception as e:
        logger.error(f"Error accessing Pinecone index '{index_name}': {e}")
        raise
    
    logger.info(f"Indexing {len(docs)} documents to Pinecone index: {index_name}")
    if namespace:
        logger.info(f"Using namespace: {namespace}")
    
    texts = [d["text"] for d in docs]
    logger.info("Generating embeddings...")
    vecs = embed_texts(texts, model_name=model_name)

    upserts = []
    for i, (doc, vec) in enumerate(zip(docs, vecs)):
        vid = doc.get("id") or f"doc-{i}"
        metadata = {k: v for k, v in doc.items() if k not in ["text", "id"]}
        upserts.append({"id": vid, "values": vec, "metadata": metadata})

    # Chunk upserts to avoid payload size limits
    BATCH = 100
    total = 0
    logger.info(f"Uploading in batches of {BATCH}...")
    
    try:
        for s in range(0, len(upserts), BATCH):
            chunk = upserts[s : s + BATCH]
            batch_num = (s // BATCH) + 1
            total_batches = (len(upserts) + BATCH - 1) // BATCH
            
            logger.info(f"Uploading batch {batch_num}/{total_batches} ({len(chunk)} documents)")
            
            # Convert to the format expected by new Pinecone API
            vectors = []
            for item in chunk:
                vectors.append({
                    "id": item["id"],
                    "values": item["values"],
                    "metadata": item["metadata"]
                })
            
            index.upsert(vectors=vectors, namespace=namespace)
            total += len(chunk)
        
        logger.info(f"✓ Successfully indexed {total} documents to Pinecone")
        return total
        
    except Exception as e:
        logger.error(f"Error during Pinecone upsert: {e}")
        raise


def index_jsonl(jsonl_path: Path, namespace: str | None = None, index_name: str = PINECONE_INDEX_NAME, model_name: str = "all-MiniLM-L6-v2") -> int:
    """Index documents from JSONL file to Pinecone."""
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting JSONL indexing from: {jsonl_path}")
    
    # Get the embedding dimension for the model
    model = _init_embedding_model(model_name)
    dimension = model.get_sentence_embedding_dimension()
    
    ensure_pinecone_index(index_name, dimension=dimension)
    
    docs: List[Dict] = []
    logger.info("Reading JSONL file...")
    
    with jsonl_path.open() as f:
        for i, line in enumerate(f):
            d = json.loads(line)
            if "id" not in d:
                d["id"] = f"zoning-{i}"
            docs.append(d)
    
    logger.info(f"Loaded {len(docs)} documents from JSONL")
    
    # Log some sample metadata
    if docs:
        sample_meta = docs[0].get("metadata", {})
        logger.info(f"Sample metadata keys: {list(sample_meta.keys())}")
    
    return index_documents(docs, namespace=namespace, index_name=index_name, model_name=model_name)


def get_available_models() -> List[str]:
    """Get list of recommended sentence transformer models."""
    return [
        "all-MiniLM-L6-v2",      # 384d, fast, good quality
        "all-mpnet-base-v2",     # 768d, slower, better quality
        "all-MiniLM-L12-v2",     # 384d, medium speed, good quality
        "paraphrase-MiniLM-L3-v2", # 384d, very fast, decent quality
        "multi-qa-MiniLM-L6-v2", # 384d, optimized for Q&A
    ]


def get_model_info(model_name: str = "all-MiniLM-L6-v2") -> Dict[str, any]:
    """Get information about a specific model."""
    try:
        model = _init_embedding_model(model_name)
        return {
            "name": model_name,
            "dimension": model.get_sentence_embedding_dimension(),
            "max_seq_length": model.max_seq_length,
            "device": str(model.device),
        }
    except Exception as e:
        return {"error": str(e)}