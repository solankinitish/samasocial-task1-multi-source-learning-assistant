import streamlit as st
import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"

SOURCE_ICONS = {
    "pdf": "📄",
    "youtube": "🎥",
    "pptx": "📊",
    "url": "🌐"
}

def create_session():
    response = requests.post(f"{BASE_URL}/session/create")
    return response.json()["session_id"]

def ingest_source(session_id, source_type, source_label, file=None, url=None):
    if file:
        response = requests.post(
            f"{BASE_URL}/session/{session_id}/ingest",
            data={"source_type": source_type, "source_label": source_label},
            files={"file": file}
        )
    else:
        response = requests.post(
            f"{BASE_URL}/session/{session_id}/ingest",
            data={"source_type": source_type, "source_label": source_label, "url": url}
        )
    return response

def stream_chat(session_id, query):
    try:
        with requests.post(
            f"{BASE_URL}/session/{session_id}/chat",
            json={"query": query},
            stream=True,
            timeout=60
        ) as response:
            for line in response.iter_lines():
                if line:
                    decoded = line.decode("utf-8")
                    if decoded.startswith("data: "):
                        token = decoded[6:]
                        if token != "[DONE]":
                            yield token
    except requests.exceptions.ChunkedEncodingError:
        return
    except Exception as e:
        yield f"\n\n[Error: {str(e)}]"

def parse_citation(text: str):
    if "Answered using" in text:
        parts = text.split("Answered using", 1)
        answer = parts[0].strip().rstrip(".-")
        citation = "Answered using " + parts[1].strip()
        return answer, citation
    return text, None

# --- Init session state ---
if "session_id" not in st.session_state:
    st.session_state.session_id = create_session()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "sources" not in st.session_state:
    st.session_state.sources = []

# --- Page config ---
st.set_page_config(page_title="Multi-Source Learning Assistant", layout="wide")
st.title("🧠 Multi-Source Learning Assistant")

# --- Sidebar ---
with st.sidebar:
    st.header("Add Knowledge Sources")

    source_type = st.selectbox(
        "Source Type",
        options=["pdf", "youtube", "pptx", "url"],
        format_func=lambda x: f"{SOURCE_ICONS[x]} {x.upper()}"
    )

    if source_type in ["pdf", "pptx"]:
        uploaded_file = st.file_uploader(
            "Upload File",
            type=["pdf"] if source_type == "pdf" else ["pptx"]
        )
        url_input = None
    else:
        uploaded_file = None
        url_input = st.text_input("Enter URL", key=f"url_input_{source_type}")

    if st.button("Add Source", use_container_width=True):
        if source_type in ["pdf", "pptx"] and uploaded_file:
            with st.spinner(f"Processing {uploaded_file.name}..."):
                response = ingest_source(
                    st.session_state.session_id,
                    source_type,
                    uploaded_file.name,
                    file=(uploaded_file.name, uploaded_file.getvalue())
                )
            if response.status_code == 200:
                data = response.json()
                st.session_state.sources.append({
                    "type": source_type,
                    "label": uploaded_file.name,
                    "summary": data["summary"],
                    "chunks": data["chunks_added"]
                })
                st.success(f"Added {uploaded_file.name} — {data['chunks_added']} chunks")
            else:
                st.error(f"Failed: {response.json().get('detail', 'Unknown error')}")

        elif source_type in ["youtube", "url"] and url_input:
            label = url_input.split("/")[-1][:30]
            with st.spinner(f"Processing {url_input}..."):
                response = ingest_source(
                    st.session_state.session_id,
                    source_type,
                    label,
                    url=url_input
                )
            if response.status_code == 200:
                data = response.json()
                st.session_state.sources.append({
                    "type": source_type,
                    "label": label,
                    "summary": data["summary"],
                    "chunks": data["chunks_added"]
                })
                st.success(f"Added {label} — {data['chunks_added']} chunks")
            else:
                st.error(f"Failed: {response.json().get('detail', 'Unknown error')}")
        else:
            st.warning("Please provide a file or URL.")

    # --- Source badges ---
    if st.session_state.sources:
        st.divider()
        st.subheader("Loaded Sources")
        for source in st.session_state.sources:
            icon = SOURCE_ICONS[source["type"]]
            with st.expander(f"{icon} {source['label']} ({source['chunks']} chunks)"):
                st.caption(source["summary"])

# --- Chat area ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        answer, citation = parse_citation(message["content"])
        st.markdown(answer)
        if citation:
            st.markdown(
                f'<div style="margin-top:8px;padding:6px 10px;background:#1e3a5f;border-left:3px solid #4a9eff;border-radius:4px;font-size:0.8em;color:#a8c8ff;">📎 {citation}</div>',
                unsafe_allow_html=True
            )

if prompt := st.chat_input("Ask a question about your sources..."):
    if not st.session_state.sources:
        st.warning("Please add at least one source before asking questions.")
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            answer_placeholder = st.empty()
            citation_placeholder = st.empty()
            
            full_response = ""
            answer_text = ""
            citation_text = ""
            
            for token in stream_chat(st.session_state.session_id, prompt):
                full_response += token
                if "Answered using" in full_response:
                    parts = full_response.split("Answered using", 1)
                    answer_text = parts[0].strip()
                    citation_text = "Answered using " + parts[1].strip()
                    answer_placeholder.markdown(answer_text)
                    citation_placeholder.markdown(
                        f'<div style="margin-top:8px;padding:6px 10px;background:#1e3a5f;border-left:3px solid #4a9eff;border-radius:4px;font-size:0.8em;color:#a8c8ff;">📎 {citation_text}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    answer_placeholder.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})
