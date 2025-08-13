from typing import List, Dict, Optional
import logging
import json
from pathlib import Path

from citybrain.config import HF_EMBEDDING_MODEL, PINECONE_INDEX_NAME, DATA_DIR
from citybrain.ingest.embeddings import _init_pinecone, embed_texts

logger = logging.getLogger(__name__)


def _load_zoning_chunks() -> Dict[str, str]:
    """Load the original zoning chunks to map IDs back to text content."""
    chunks_path = DATA_DIR / "zoning" / "zoning_chunks.jsonl"
    if not chunks_path.exists():
        logger.warning(f"Zoning chunks file not found: {chunks_path}")
        return {}
    
    chunks_map = {}
    try:
        with chunks_path.open() as f:
            for line_num, line in enumerate(f):
                chunk_data = json.loads(line.strip())
                chunk_text = chunk_data.get("text")
                
                # Use the same ID generation logic as in index_jsonl
                chunk_id = f"zoning-{line_num}"
                
                if chunk_text:
                    chunks_map[chunk_id] = chunk_text
                    # Log the first few for debugging
                    if line_num < 3:
                        logger.debug(f"Loaded chunk {chunk_id}: {chunk_text[:100]}...")
        
        logger.info(f"Loaded {len(chunks_map)} zoning chunks for text retrieval")
        logger.info(f"Sample IDs: {list(chunks_map.keys())[:5]}")
    except Exception as e:
        logger.error(f"Error loading zoning chunks: {e}")
        return {}
    
    return chunks_map


def search_zoning_chunks(query: str, top_k: int = 8, namespace: Optional[str] = "zoning-nyc") -> List[Dict]:
    logger.info("Searching zoning chunks via semantic search")
    pc = _init_pinecone()
    index = pc.Index(PINECONE_INDEX_NAME)

    logger.debug("Embedding query text for semantic search")
    emb = embed_texts([query], model_name=HF_EMBEDDING_MODEL)[0]

    try:
        res = index.query(vector=emb, top_k=top_k, include_metadata=True, namespace=namespace)
        logger.info("Pinecone query completed: top_k=%d namespace=%s", top_k, namespace)
    except Exception as e:
        logger.error(f"Error querying Pinecone: {e}")
        raise

    # Load the original text content
    chunks_map = _load_zoning_chunks()

    items: List[Dict] = []
    matches = getattr(res, "matches", []) or res.get("matches", [])  # type: ignore
    logger.debug("Received %d matches from Pinecone", len(matches))
    
    for m in matches:
        meta = m.get("metadata") if isinstance(m, dict) else getattr(m, "metadata", {})
        score = m.get("score") if isinstance(m, dict) else getattr(m, "score", None)
        chunk_id = m.get("id") if isinstance(m, dict) else getattr(m, "id", None)
        
        # Retrieve the full text content
        full_text = chunks_map.get(chunk_id, "Text content not available")
        
        items.append({
            "id": chunk_id,
            "score": score,
            "metadata": meta,
            "text": full_text,  # Now contains the actual text content
        })
    
    logger.info("Returning %d zoning references with full text", len(items))
    return items