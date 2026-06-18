# Multi-Source Learning Assistant
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red)
![Groq](https://img.shields.io/badge/LLM-Groq-orange)
![FAISS](https://img.shields.io/badge/Vector_Store-FAISS-yellow)
![Cloud Run](https://img.shields.io/badge/Deployed-Cloud_Run-blue)

An AI chatbot that ingests content from PDFs, YouTube videos, PowerPoint files, and web URLs — then answers questions grounded strictly in that content, with source citations on every response.

**Live:** https://task1-frontend-915504862406.us-central1.run.app  
**Backend API:** https://task1-backend-915504862406.us-central1.run.app/docs

---

## What it does

Load one or more sources into a session. Ask questions. The assistant retrieves the most relevant content, answers from it, and cites exactly where the answer came from — page number, slide number, timestamp, or section.

---

## Architecture

```
Streamlit Frontend
       ↓ HTTP + SSE
FastAPI Backend
       ↓
Ingestion Layer (PDF / YouTube / PPTX / URL)
       ↓ chunks with metadata
sentence-transformers Embeddings → FAISS Index
       ↓ top-10 candidates
Hybrid Reranker (cosine + noun keyword overlap) → top-3
       ↓
Groq LLM (llama-3.1-8b-instant) — streaming SSE
       ↓
Answer + Citation Badge
```

---

## Key Decisions

**Two-stage retrieval: FAISS top-10 → reranker top-3**  
FAISS retrieves broadly for recall. The hybrid reranker narrows for precision. Single-stage retrieval either misses relevant chunks or returns noisy ones — two stages handles both.

**Hybrid reranker: 0.5 cosine + 0.5 noun-only keyword overlap**  
Cosine similarity captures semantic meaning but misses exact term matches. Keyword overlap on nouns only (via spaCy) catches cases where the user uses a specific name or technical term verbatim. Equal weights, no tuning needed for trusted document sources.

**Source-aware chunking**  
PDF: 500 chars (dense, paragraph-level). YouTube: 800 chars (conversational, needs more context). URL: 600 chars (article prose). PPTX: one chunk per slide (slides are atomic units — splitting mid-slide breaks meaning). Each source type has a different natural unit of meaning.

**Chunk metadata enables zero-cost citations**  
Every chunk is tagged with `source_type`, `source_label`, and `location` at ingestion time. The LLM receives this metadata in the context and cites it directly — no post-processing, no separate citation lookup.

**Dropped answerability scoring**  
A previous project used spaCy-based answerability scoring to filter web-sourced content by answer intent. That's unnecessary here — uploaded documents are pre-verified and scoped, cosine + keyword overlap is sufficient.

**Free, evaluator-friendly stack**  
`sentence-transformers all-MiniLM-L6-v2` runs locally — no OpenAI embedding API needed. Groq API is free tier. Any evaluator can run this without API costs.

**Manual streaming with st.empty()**  
`st.write_stream` renders tokens but doesn't allow mid-stream interception. To split the answer from the citation badge during streaming, two `st.empty()` placeholders are used — one for answer text, one for the citation block. The split happens the moment "Answered using" appears in the accumulated token stream.

---

## Local Setup

**Requirements:** Python 3.11+, Groq API key (free at console.groq.com)

```bash
git clone https://github.com/solankinitish/samasocial-task1-multi-source-learning-assistant
cd samasocial-task1-multi-source-learning-assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

Create `.env`:
```
GROQ_API_KEY=your-key-here
```

```bash
# Terminal 1 — backend
uvicorn backend.main:app --reload

# Terminal 2 — frontend
streamlit run frontend/app.py
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Required. Get free at console.groq.com |
| `BACKEND_URL` | Frontend → backend URL. Defaults to `http://127.0.0.1:8000/api/v1` |

---

## API

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/session/create` | Create session |
| POST | `/api/v1/session/{id}/ingest` | Ingest PDF, PPTX, YouTube URL, or webpage |
| GET | `/api/v1/session/{id}/sources` | List loaded sources |
| POST | `/api/v1/session/{id}/chat` | Streaming chat (SSE) |

---

## Tradeoffs

- Session state is in-memory — server restart clears sessions. Production would use Redis.
- FAISS index rebuilds on every source addition — fine for demo scope, production would use incremental indexing.
- Cloud Run cold start is ~20-30 seconds on first request due to model load.
