from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from backend.schemas.models import ChatRequest, IngestResponse, SessionResponse, SourceInfo
from backend.services import assistant as assistant_service
import tempfile
import os

router = APIRouter()

@router.post("/session/create", response_model=SessionResponse)
async def create_session():
    session_id = assistant_service.create_new_session()
    return SessionResponse(session_id=session_id)

@router.post("/session/{session_id}/ingest")
async def ingest_source(
    session_id: str,
    source_type: str = Form(...),
    source_label: str = Form(...),
    url: str = Form(None),
    file: UploadFile = File(None)
):
    if file:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await file.read())
            tmp_path = tmp.name
        result = assistant_service.ingest(session_id, source_type, source_label, file_path=tmp_path)
        os.unlink(tmp_path)
    else:
        result = assistant_service.ingest(session_id, source_type, source_label, url=url)
    
    return result

@router.get("/session/{session_id}/sources", response_model=list[SourceInfo])
async def get_sources(session_id: str):
    return assistant_service.get_sources(session_id)

@router.post("/session/{session_id}/chat")
async def chat(session_id: str, request: ChatRequest):
    return StreamingResponse(
        assistant_service.stream_chat(session_id, request.query),
        media_type="text/event-stream"
    )
