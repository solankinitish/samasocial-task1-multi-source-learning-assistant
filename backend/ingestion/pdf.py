import pdfplumber
from backend.schemas.models import Chunk

def ingest_pdf(file_path: str, source_label: str) -> list[Chunk]:
    try:
        chunks = []
        with pdfplumber.open(file_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if not text:
                    continue
                for i in range(0, len(text), 500):
                    chunk_text = text[i:i+500].strip()
                    if chunk_text:
                        chunks.append(Chunk(
                            text=chunk_text,
                            source_type="pdf",
                            source_label=source_label,
                            location=f"page {page_num}"
                        ))
        return chunks
    except Exception as e:
        raise ValueError(f"Failed to process PDF {source_label}: {str(e)}")
