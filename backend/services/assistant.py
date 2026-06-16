import os
from groq import Groq
from backend.session.store import create_session, get_session, add_chunks_to_session, add_message_to_session
from backend.ingestion.pdf import ingest_pdf
from backend.ingestion.youtube import ingest_youtube
from backend.ingestion.pptx import ingest_pptx
from backend.ingestion.webpage import ingest_webpage
from backend.retrieval.faiss_store import build_index, retrieve
from backend.retrieval.reranker import rerank
from backend.schemas.models import SourceInfo, IngestResponse
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """Answer the query from the context, follow these rules:

1. Use only the information provided in context to answer, if the context is insufficient, say "I don't know"
2. Be precise and clear in your framing.
3. Use the same language framing like that of query and context to answer.
4. Always end your answer with a citation in this format:
   - For PDF: "Answered using page {{page_number}} of {{source_label}}"
   - For PPTX: "Answered using slide {{slide_number}} of {{source_label}}"
   - For YouTube: "Answered using {{source_label}} from {{start}} to {{end}}"
   - For URL: "Answered using section {{section_number}} of {{source_label}}"

Context:
{context}"""

def create_new_session() -> str:
    return create_session()

def ingest(session_id: str, source_type: str, source_label: str, file_path: str = None, url: str = None) -> IngestResponse:
    session = get_session(session_id)
    if session is None:
        raise ValueError(f"Session {session_id} not found")

    if source_type == "pdf":
        chunks = ingest_pdf(file_path, source_label)
    elif source_type == "youtube":
        chunks = ingest_youtube(url, source_label)
    elif source_type == "pptx":
        chunks = ingest_pptx(file_path, source_label)
    elif source_type == "url":
        chunks = ingest_webpage(url, source_label)
    else:
        raise ValueError(f"Unsupported source type: {source_type}")

    add_chunks_to_session(session_id, chunks)
    session = get_session(session_id)
    session.faiss_index = build_index(session.chunks)

    summary = generate_summary(chunks[:5], source_label)

    return IngestResponse(
        message=f"Successfully ingested {source_label}",
        summary=summary,
        chunks_added=len(chunks)
    )

def generate_summary(chunks: list, source_label: str) -> str:
    context = "\n".join([c.text for c in chunks])
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": f"Summarize this content in 3-4 sentences:\n\n{context}"}
        ],
        max_tokens=200
    )
    return response.choices[0].message.content

def get_sources(session_id: str) -> list[SourceInfo]:
    session = get_session(session_id)
    if session is None:
        return []
    seen = set()
    sources = []
    for chunk in session.chunks:
        key = (chunk.source_type, chunk.source_label)
        if key not in seen:
            seen.add(key)
            sources.append(SourceInfo(source_type=chunk.source_type, source_label=chunk.source_label))
    return sources

def stream_chat(session_id: str, query: str):
    session = get_session(session_id)
    if session is None:
        yield "data: Session not found\n\n"
        return

    if not session.chunks:
        yield "data: No sources loaded. Please add a source first.\n\n"
        return

    candidates = retrieve(query, session.chunks, session.faiss_index)
    top_chunks = rerank(query, candidates)

    context = "\n\n".join([
        f"[{c.source_type} | {c.source_label} | {c.location}]\n{c.text}"
        for c in top_chunks
    ])

    messages = [{"role": m.role, "content": m.content} for m in session.history]
    messages.append({"role": "user", "content": query})

    add_message_to_session(session_id, "user", query)

    full_response = ""
    stream = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT.format(context=context)},
            *messages
        ],
        max_tokens=1000,
        stream=True
    )

    for chunk in stream:
        token = chunk.choices[0].delta.content
        if token:
            full_response += token
            yield f"data: {token}\n\n"

    add_message_to_session(session_id, "assistant", full_response)
    yield "data: [DONE]\n\n"
