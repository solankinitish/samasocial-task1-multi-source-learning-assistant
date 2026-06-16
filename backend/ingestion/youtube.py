from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._transcripts import TranscriptList
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
    try:
        video_id = extract_video_id(url)
        if not video_id:
            raise ValueError("Could not extract video ID from URL")
        
        ytt = YouTubeTranscriptApi()
        transcript = ytt.fetch(video_id)
        snippet_list = list(transcript)
    except Exception as e:
        raise ValueError(f"Failed to fetch YouTube transcript: {str(e)}")

    chunks = []
    current_text = ""
    current_start = 0.0

    for entry in snippet_list:
        if not current_text:
            current_start = entry.start
        current_text += " " + entry.text
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
