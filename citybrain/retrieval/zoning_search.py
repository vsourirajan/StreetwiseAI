from typing import List, Dict, Optional
import logging
import json
import re
from pathlib import Path

from citybrain.config import HF_EMBEDDING_MODEL, PINECONE_INDEX_NAME, DATA_DIR
from citybrain.ingest.embeddings import _init_pinecone, embed_texts

logger = logging.getLogger(__name__)


def _load_zoning_chunks() -> Dict[str, str]:
    """Load the original zoning chunks to map IDs back to text content.
    Returns a map of multiple possible ids to the same text, supporting:
    - explicit 'id' field if present in the JSONL
    - fallback 'zoning-{line_num}' id used during indexing otherwise
    """
    chunks_path = DATA_DIR / "zoning" / "zoning_chunks.jsonl"
    if not chunks_path.exists():
        logger.warning(f"Zoning chunks file not found: {chunks_path}")
        return {}
    
    chunks_map: Dict[str, str] = {}
    try:
        with chunks_path.open() as f:
            for line_num, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    chunk_data = json.loads(line)
                except Exception as e:
                    logger.warning(f"Invalid JSON at line {line_num+1}: {e}")
                    continue
                chunk_text = chunk_data.get("text")
                explicit_id = chunk_data.get("id")
                fallback_id = f"zoning-{line_num}"

                if not chunk_text:
                    # Skip empty text lines to avoid mapping noise
                    continue

                # Map by explicit id if present
                if explicit_id:
                    chunks_map[str(explicit_id)] = chunk_text
                # Always map by fallback id as well
                chunks_map[fallback_id] = chunk_text

                if line_num < 3:
                    logger.debug(f"Loaded chunk ids {[explicit_id, fallback_id]}: {chunk_text[:100]}...")
        logger.info(f"Loaded {len(chunks_map)} zoning chunk id->text mappings from {chunks_path}")
    except Exception as e:
        logger.error(f"Error loading zoning chunks: {e}")
        return {}
    
    return chunks_map


def _map_id_to_text(chunk_id: Optional[str], meta: Dict, chunks_map: Dict[str, str]) -> str:
    """Resolve text for a Pinecone match using multiple strategies.
    Strategies:
      1) Direct lookup by chunk_id
      2) Extract first integer from id and try 'zoning-{int}'
      3) Fallback to metadata fields 'text' or 'content'
    """
    if not chunk_id:
        meta_text = (meta or {}).get("text") or (meta or {}).get("content")
        return meta_text or "Text content not available"

    # 1) Direct lookup
    if chunk_id in chunks_map:
        return chunks_map[chunk_id]

    # 2) Try integer extraction
    m = re.search(r"(\d+)", str(chunk_id))
    if m:
        candidate = f"zoning-{m.group(1)}"
        if candidate in chunks_map:
            logger.debug(f"Mapped id {chunk_id} -> {candidate}")
            return chunks_map[candidate]

    # 3) Fallback to metadata
    meta_text = (meta or {}).get("text") or (meta or {}).get("content")
    if meta_text:
        logger.debug(f"Using text from metadata for id {chunk_id}")
        return meta_text

    # 4) Give up
    logger.debug(f"No text found for id {chunk_id}")
    return "Text content not available"


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
    logger.info("Received %d matches from Pinecone", len(matches))
    if not chunks_map:
        logger.warning("Zoning chunks map is empty; will rely on Pinecone metadata for text if present")
    
    misses = 0
    hits = 0
    for idx, m in enumerate(matches):
        meta = m.get("metadata") if isinstance(m, dict) else getattr(m, "metadata", {})
        score = m.get("score") if isinstance(m, dict) else getattr(m, "score", None)
        chunk_id = m.get("id") if isinstance(m, dict) else getattr(m, "id", None)

        full_text = _map_id_to_text(chunk_id, meta, chunks_map)
        if full_text == "Text content not available":
            misses += 1
            if idx < 5:
                logger.warning(f"No text for id={chunk_id}; meta keys={list(meta.keys()) if isinstance(meta, dict) else 'N/A'}")
        else:
            hits += 1

        items.append({
            "id": chunk_id,
            "score": score,
            "metadata": meta,
            "text": full_text,
        })
    logger.info("Returning %d zoning references; text hits=%d, misses=%d", len(items), hits, misses)
    return items