from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse, parse_qs
from backend.schemas.models import Chunk

def extract_video_id(url: str) -> str:
    parsed = urlparse(url)
    if parsed.hostname == "youtu.be":
        return parsed.path[1:]
    return parse_qs(parsed.query).get("v", [None])[0]

def format_timestamp(seconds: float) -> str:
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}:{secs:02d}"

def ingest_youtube(url: str, source_label: str) -> list[Chunk]:
    video_id = extract_video_id(url)
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    
    chunks = []
    current_text = ""
    current_start = 0.0

    for entry in transcript:
        if not current_text:
            current_start = entry["start"]
        current_text += " " + entry["text"]
        if len(current_text) >= 800:
            chunks.append(Chunk(
                text=current_text.strip(),
                source_type="youtube",
                source_label=source_label,
                location=f"at {format_timestamp(current_start)}"
            ))
            current_text = ""
            current_start = 0.0

    if current_text.strip():
        chunks.append(Chunk(
            text=current_text.strip(),
            source_type="youtube",
            source_label=source_label,
            location=f"at {format_timestamp(current_start)}"
        ))

    return chunks
