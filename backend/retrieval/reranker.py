import spacy
import numpy as np
from backend.schemas.models import Chunk
from backend.retrieval.embedder import embed_texts, embed_query

nlp = spacy.load("en_core_web_sm")

def extract_nouns(query: str) -> set[str]:
    doc = nlp(query.lower())
    return {token.text for token in doc if token.pos_ == "NOUN"}

def compute_keyword_scores(chunks: list[Chunk], nouns: set[str]) -> list[float]:
    if not nouns:
        return [0.0] * len(chunks)
    scores = []
    for chunk in chunks:
        chunk_lower = chunk.text.lower()
        matches = sum(1 for noun in nouns if noun in chunk_lower)
        scores.append(matches / len(nouns))
    return scores

def compute_cosine_scores(query: str, chunks: list[Chunk]) -> list[float]:
    query_vec = embed_query(query).reshape(1, -1).astype(np.float32)
    chunk_vecs = embed_texts([c.text for c in chunks]).astype(np.float32)
    query_vec /= np.linalg.norm(query_vec)
    chunk_vecs /= np.linalg.norm(chunk_vecs, axis=1, keepdims=True)
    return (chunk_vecs @ query_vec.T).flatten().tolist()

def rerank(query: str, candidates: list[Chunk], top_k: int = 3) -> list[Chunk]:
    nouns = extract_nouns(query)
    cosine = compute_cosine_scores(query, candidates)
    keyword = compute_keyword_scores(candidates, nouns)

    scored = []
    for i, chunk in enumerate(candidates):
        final_score = 0.5 * cosine[i] + 0.5 * keyword[i]
        scored.append((final_score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]
