import uuid
from backend.schemas.models import SessionState

sessions: dict[str, SessionState] = {}

def create_session() -> str:
    session_id = str(uuid.uuid4())
    sessions[session_id] = SessionState()
    return session_id

def get_session(session_id: str) -> SessionState | None:
    return sessions.get(session_id)

def add_chunks_to_session(session_id: str, chunks: list) -> None:
    sessions[session_id].chunks.extend(chunks)

def add_message_to_session(session_id: str, role: str, content: str) -> None:
    sessions[session_id].history.append({"role": role, "content": content})
