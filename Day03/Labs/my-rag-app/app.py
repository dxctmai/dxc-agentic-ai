"""PDF Policy Buddy: a small PDF-only retrieval app."""
import hashlib
import io
import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import streamlit as st
from pypdf import PdfReader

# Add the repository root first so the shared AskIT helpers can be imported.
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from askit_core import bedrock, config

EMBED_MODEL = "amazon.titan-embed-text-v2:0"
NO_ANSWER = "I could not find that in the PDF."

# Keep the page focused on the uploaded PDF and make the chat easy to scan.
st.set_page_config(page_title="PDF Policy Buddy", page_icon="🤖")
st.markdown("""
<style>
.stApp { background: #102b2b; color: #e7f3ef; }
[data-testid="stHeader"] { background: #102b2b; }
.title-band { background: #176b67; padding: 18px 22px; border-radius: 12px; }
[data-testid="stChatMessage"] { background: #1b3b39; border-radius: 14px; }
.stButton > button, .stDownloadButton > button { background: #20a39e; color: #071f1d; border: 0; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)
st.markdown('<div class="title-band"><h1>🤖 PDF Policy Buddy</h1><p>Upload. Ask. Done.</p></div>', unsafe_allow_html=True)

# Store only the active PDF's index and conversation so reruns do not rebuild work.
for key, initial in {"upload_id": None, "chunks": [], "vectors": [], "index_settings": None, "chat": []}.items():
    if key not in st.session_state:
        st.session_state[key] = initial

# These controls define retrieval and chunking; changing chunk settings requires reindexing.
with st.sidebar:
    st.markdown(f"### About me\n**Thanh Mai**\n\n{date.today():%B %d, %Y}\n\nA good innings starts with a steady first delivery.")
    top_k = st.slider("Top-K", 1, 6, 4)
    chunk_size = st.slider("Chunk size (words)", 60, 240, 120, 10)
    overlap = st.slider("Overlap (words)", 0, 60, 30, 5)
    if st.button("Clear chat"):
        st.session_state.chat = []

# A changed or removed upload discards its old index and conversation.
upload = st.file_uploader("Upload a PDF", type="pdf")
pdf_bytes = upload.getvalue() if upload else None
upload_id = hashlib.sha256(pdf_bytes).hexdigest() if pdf_bytes else None
if upload_id != st.session_state.upload_id:
    st.session_state.upload_id = upload_id
    st.session_state.chunks, st.session_state.vectors = [], []
    st.session_state.index_settings, st.session_state.chat = None, []

# Split each page independently so every retrieved passage retains its PDF page number.
def make_chunks(page_text, size, step):
    words = page_text.split()
    return [" ".join(words[start:start + size]) for start in range(0, len(words), step) if words[start:start + size]]

# Titan returns one normalized vector per text; process at most four sequentially at once.
def embed_text(text):
    response = bedrock.client().invoke_model(
        modelId=EMBED_MODEL,
        body=json.dumps({"inputText": text, "dimensions": 512, "normalize": True}),
    )
    return json.loads(response["body"].read())["embedding"]

# Cosine similarity ranks passages by their direction, independent of vector length.
def cosine_scores(query_vector, vectors):
    query = np.asarray(query_vector, dtype=float)
    matrix = np.asarray(vectors, dtype=float)
    denom = np.linalg.norm(matrix, axis=1) * np.linalg.norm(query)
    return np.divide(matrix @ query, denom, out=np.zeros(len(vectors)), where=denom != 0)

# Build a fresh page-aware index only after the user requests it.
if upload and st.button("Build index", type="primary"):
    st.session_state.chunks, st.session_state.vectors = [], []
    st.session_state.index_settings = None
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        passages = [(page_number, chunk) for page_number, page in enumerate(reader.pages, 1)
                    for chunk in make_chunks(page.extract_text() or "", chunk_size, chunk_size - overlap)]
        if not passages:
            st.warning("This PDF has no selectable text. It may be scanned; try a text-based PDF.")
        else:
            progress = st.progress(0)
            vectors = []
            for group_start in range(0, len(passages), 4):
                for _, text in passages[group_start:group_start + 4]:
                    vectors.append(embed_text(text))
                    progress.progress(len(vectors) / len(passages))
            st.session_state.chunks = [{"page": page, "text": text} for page, text in passages]
            st.session_state.vectors = vectors
            st.session_state.index_settings = (chunk_size, overlap)
            st.success(f"Indexed {len(reader.pages)} pages and {len(passages)} chunks.")
    except Exception:
        st.error("Could not build the index. Check .env keys, AWS region, and Titan model access, then retry.")

# Refuse stale indexes so slider changes take effect only after Build index.
ready = bool(st.session_state.chunks) and st.session_state.index_settings == (chunk_size, overlap)
if st.session_state.chunks and not ready:
    st.info("Chunk settings changed. Select Build index to apply them.")

# Retrieve context, enforce PDF-only answers, and keep the source passages with the reply.
def answer_question(question):
    query_vector = embed_text(question)
    scores = cosine_scores(query_vector, st.session_state.vectors)
    selected = np.argsort(scores)[::-1][:top_k]
    sources = [{**st.session_state.chunks[index], "score": float(scores[index])} for index in selected]
    if not sources or sources[0]["score"] < 0.35:
        return NO_ANSWER, sources, "weak match"
    context = "\n\n".join(f"[p.{item['page']}] {item['text']}" for item in sources)
    prompt = ("Answer ONLY from the context. If the answer is not in the context, say you could not "
              "find it in the PDF. Cite the page like [p.3]. Be formal, calm, and helpful, like a senior "
              "engineer, cricket commentator, friendly Chennai auto-anna, and polite teacher. "
              "Your tone must not add facts beyond the PDF.\n\n"
              f"Context:\n{context}\n\nQuestion: {question}")
    result = bedrock.client().converse(
        modelId=config.SMALL_MODEL, messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 500, "temperature": 0.2},
    )
    text = result["output"]["message"]["content"][0]["text"]
    return text, sources, "grounded" if sources[0]["score"] >= 0.35 else "weak match"

# Handle typed and sample outside-PDF questions through the same retrieval path.
question = st.chat_input("Ask a question about your PDF") if ready else None
if st.button("Not in my PDF?", disabled=not ready):
    question = "Who won the last cricket world cup?"
if question and ready:
    st.session_state.chat.append({"role": "user", "text": question})
    try:
        reply, sources, badge = answer_question(question)
        st.session_state.chat.append({"role": "assistant", "text": reply, "sources": sources, "badge": badge})
    except Exception:
        st.session_state.chat.append({"role": "assistant", "text": "I could not reach the answer service. Check .env keys, AWS region, and Titan model access, then retry.", "sources": [], "badge": "weak match"})

# Replay saved messages after each Streamlit rerun, with citations directly under answers.
for message in st.session_state.chat:
    with st.chat_message(message["role"], avatar="🤖" if message["role"] == "assistant" else None):
        st.markdown(message["text"])
        if message["role"] == "assistant":
            st.caption(message["badge"])
            with st.expander("Sources"):
                for source in message["sources"]:
                    st.markdown(f"**Page {source['page']} · Similarity {source['score']:.2f}**\n\n{source['text']}")

# Offer a portable transcript only when there is something to export.
if st.session_state.chat:
    transcript = "\n\n".join(f"## {item['role'].title()}\n\n{item['text']}" for item in st.session_state.chat)
    st.download_button("Download chat (.md)", transcript, file_name="pdf-policy-buddy-chat.md", mime="text/markdown")
st.markdown("<div style='text-align:center; color:#a8c6c0; padding:18px'>Built by Thanh Mai with vibe coding at DevPro Academy</div>", unsafe_allow_html=True)
