from pydantic import BaseModel
from typing import Literal, Any

class Chunk(BaseModel):
    text: str
    source_type: Literal["pdf", "youtube", "pptx", "url"]
    source_label: str
    location: str

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class SessionState(BaseModel):
    chunks: list[Chunk] = []
    history: list[Message] = []

class IngestRequest(BaseModel):
    source_type: Literal["pdf", "youtube", "pptx", "url"]
    source_label: str
    url: str | None = None  # for youtube and url types

class ChatRequest(BaseModel):
    query: str

class SourceInfo(BaseModel):
    source_type: str
    source_label: str

class IngestResponse(BaseModel):
    message: str
    summary: str
    chunks_added: int

class SessionResponse(BaseModel):
    session_id: str

class SessionState(BaseModel):
    chunks: list[Chunk] = []
    history: list[Message] = []
    faiss_index: Any = None
