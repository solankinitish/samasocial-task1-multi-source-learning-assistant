import trafilatura
from backend.schemas.models import Chunk

def ingest_webpage(url: str, source_label: str) -> list[Chunk]:
    downloaded = trafilatura.fetch_url(url)
    text = trafilatura.extract(downloaded)
    
    if not text:
        return []
    
    chunks = []
    for i in range(0, len(text), 600):
        chunk_text = text[i:i+600].strip()
        if chunk_text:
            chunks.append(Chunk(
                text=chunk_text,
                source_type="url",
                source_label=source_label,
                location=f"section {i//600 + 1}"
            ))
    
    return chunks
