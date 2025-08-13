from typing import Iterable, List, Dict

try:
    import tiktoken  # type: ignore
except Exception:  # pragma: no cover
    tiktoken = None


def tokenize_length(text: str, model: str = "gpt-4o-mini") -> int:
    if not tiktoken:
        return max(1, len(text.split()))
    try:
        enc = tiktoken.get_encoding("cl100k_base")
    except Exception:
        enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
    return len(enc.encode(text))


def chunk_text(
    text: str,
    max_tokens: int = 800,
    overlap_tokens: int = 100,
) -> List[str]:
    if not tiktoken:
        words = text.split()
        chunks: List[str] = []
        start = 0
        step = max(1, max_tokens - overlap_tokens)
        while start < len(words):
            end = min(len(words), start + max_tokens)
            chunks.append(" ".join(words[start:end]))
            start += step
        return chunks

    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    chunks = []
    step = max(1, max_tokens - overlap_tokens)
    for i in range(0, len(tokens), step):
        window = tokens[i : i + max_tokens]
        if not window:
            break
        chunks.append(enc.decode(window))
    return chunks


def attach_metadata(chunks: Iterable[str], base_meta: Dict) -> List[Dict]:
    return [
        {"text": c, **base_meta, "char_length": len(c), "token_estimate": tokenize_length(c)}
        for c in chunks
    ]