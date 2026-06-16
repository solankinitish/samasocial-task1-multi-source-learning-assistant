import requests
import json
import sys
import os

BASE_URL = "http://127.0.0.1:8000/api/v1"

def create_session():
    response = requests.post(f"{BASE_URL}/session/create")
    session_id = response.json()["session_id"]
    print(f"✓ Session created: {session_id}")
    return session_id

def test_pdf(session_id, file_path):
    print("\n--- Testing PDF Ingestion ---")
    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/session/{session_id}/ingest",
            data={"source_type": "pdf", "source_label": filename},
            files={"file": f}
        )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_youtube(session_id, url, label):
    print("\n--- Testing YouTube Ingestion ---")
    response = requests.post(
        f"{BASE_URL}/session/{session_id}/ingest",
        data={"source_type": "youtube", "source_label": label, "url": url}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_url(session_id, url, label):
    print("\n--- Testing URL Ingestion ---")
    response = requests.post(
        f"{BASE_URL}/session/{session_id}/ingest",
        data={"source_type": "url", "source_label": label, "url": url}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_pptx(session_id, file_path):
    print("\n--- Testing PPTX Ingestion ---")
    filename = os.path.basename(file_path)
    with open(file_path, "rb") as f:
        response = requests.post(
            f"{BASE_URL}/session/{session_id}/ingest",
            data={"source_type": "pptx", "source_label": filename},
            files={"file": f}
        )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

def test_chat(session_id, query):
    print(f"\n--- Testing Chat: '{query}' ---")
    response = requests.post(
        f"{BASE_URL}/session/{session_id}/chat",
        json={"query": query},
        stream=True
    )
    print("Response: ", end="", flush=True)
    for line in response.iter_lines():
        if line:
            decoded = line.decode("utf-8")
            if decoded.startswith("data: "):
                token = decoded[6:]
                if token != "[DONE]":
                    print(token, end="", flush=True)
    print()

def test_sources(session_id):
    print("\n--- Loaded Sources ---")
    response = requests.get(f"{BASE_URL}/session/{session_id}/sources")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else None
    youtube_url = sys.argv[2] if len(sys.argv) > 2 else "https://www.youtube.com/watch?v=DSmM_GcrFG0"
    webpage_url = sys.argv[3] if len(sys.argv) > 3 else "https://en.wikipedia.org/wiki/Jordan_Peterson"
    pptx_path = sys.argv[4] if len(sys.argv) > 4 else None

    session_id = create_session()

    if pdf_path:
        test_pdf(session_id, pdf_path)
    if youtube_url:
        test_youtube(session_id, youtube_url, "YouTube Source")
    if webpage_url:
        test_url(session_id, webpage_url, "Webpage Source")
    if pptx_path:
        test_pptx(session_id, pptx_path)

    test_sources(session_id)
    test_chat(session_id, "What are the main ideas discussed?")
