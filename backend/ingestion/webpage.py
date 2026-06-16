import trafilatura
from backend.schemas.models import Chunk

def ingest_webpage(url: str, source_label: str) -> list[Chunk]:
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            raise ValueError(f"Could not fetch URL: {url}")
        text = trafilatura.extract(downloaded)
        if not text:
            raise ValueError(f"Could not extract content from URL: {url}")
    except Exception as e:
        raise ValueError(f"Failed to process webpage {url}: {str(e)}")

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
