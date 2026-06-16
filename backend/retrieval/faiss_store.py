import faiss
import numpy as np
from backend.schemas.models import Chunk
from backend.retrieval.embedder import embed_texts, embed_query

def build_index(chunks: list[Chunk]) -> faiss.IndexFlatIP:
    texts = [chunk.text for chunk in chunks]
    embeddings = embed_texts(texts).astype(np.float32)
    faiss.normalize_L2(embeddings)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    return index

def retrieve(query: str, chunks: list[Chunk], index: faiss.IndexFlatIP, top_k: int = 10) -> list[Chunk]:
    query_vector = embed_query(query).reshape(1, -1).astype(np.float32)
    faiss.normalize_L2(query_vector)
    _, indices = index.search(query_vector, top_k)
    return [chunks[i] for i in indices[0] if i < len(chunks)]
