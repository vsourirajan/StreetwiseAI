from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterable, List, Dict

from citybrain.config import OPENAI_API_KEY, PINECONE_API_KEY, PINECONE_INDEX_NAME


def _init_openai():
    from openai import OpenAI  # type: ignore

    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set")
    return OpenAI(api_key=OPENAI_API_KEY)


def _init_pinecone():
    from pinecone import Pinecone  # type: ignore

    if not PINECONE_API_KEY:
        raise RuntimeError("PINECONE_API_KEY not set")
    return Pinecone(api_key=PINECONE_API_KEY)


def ensure_pinecone_index(index_name: str = PINECONE_INDEX_NAME, dimension: int = 3072) -> None:
    logger = logging.getLogger(__name__)
    pc = _init_pinecone()
    existing = {idx["name"] for idx in pc.list_indexes()}
    
    if index_name not in existing:
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


def embed_texts(texts: List[str], model: str = "text-embedding-3-large") -> List[List[float]]:
    logger = logging.getLogger(__name__)
    client = _init_openai()
    
    logger.info(f"Generating embeddings for {len(texts)} texts using {model}")
    
    # OpenAI API supports batching
    try:
        resp = client.embeddings.create(model=model, input=texts)
        vectors = [d.embedding for d in resp.data]
        logger.info(f"✓ Generated {len(vectors)} embeddings successfully")
        return vectors
    except Exception as e:
        logger.error(f"✗ Failed to generate embeddings: {e}")
        raise


def index_documents(docs: List[Dict], namespace: str | None = None, index_name: str = PINECONE_INDEX_NAME) -> int:
    logger = logging.getLogger(__name__)
    pc = _init_pinecone()
    index = pc.Index(index_name)
    
    logger.info(f"Indexing {len(docs)} documents to Pinecone index: {index_name}")
    if namespace:
        logger.info(f"Using namespace: {namespace}")
    
    texts = [d["text"] for d in docs]
    logger.info("Generating embeddings...")
    vecs = embed_texts(texts)

    upserts = []
    for i, (doc, vec) in enumerate(zip(docs, vecs)):
        vid = doc.get("id") or f"doc-{i}"
        metadata = {k: v for k, v in doc.items() if k not in ["text", "id"]}
        upserts.append({"id": vid, "values": vec, "metadata": metadata})

    # Chunk upserts to avoid payload size limits
    BATCH = 100
    total = 0
    logger.info(f"Uploading in batches of {BATCH}...")
    
    for s in range(0, len(upserts), BATCH):
        chunk = upserts[s : s + BATCH]
        batch_num = (s // BATCH) + 1
        total_batches = (len(upserts) + BATCH - 1) // BATCH
        
        logger.info(f"Uploading batch {batch_num}/{total_batches} ({len(chunk)} documents)")
        index.upsert(vectors=chunk, namespace=namespace)
        total += len(chunk)
    
    logger.info(f"✓ Successfully indexed {total} documents to Pinecone")
    return total


def index_jsonl(jsonl_path: Path, namespace: str | None = None, index_name: str = PINECONE_INDEX_NAME) -> int:
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting JSONL indexing from: {jsonl_path}")
    
    ensure_pinecone_index(index_name)
    
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
    
    return index_documents(docs, namespace=namespace, index_name=index_name)