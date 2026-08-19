"""Streamlit web interface for the Family Secret RAG assistant."""

import os
import sys
from pathlib import Path

import requests
import streamlit as st
from dotenv import load_dotenv
from qdrant_client import QdrantClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.lead_qualifier.knowledge_base import load_knowledge_chunks  # noqa: E402
from tools.lead_qualifier.rag_assistant import (  # noqa: E402
    GeminiGenerationClient,
    answer_from_results,
)
from tools.lead_qualifier.semantic_search import GeminiEmbeddingClient  # noqa: E402
from tools.lead_qualifier.vector_store import index_chunks, search_vector_store  # noqa: E402

load_dotenv()

st.set_page_config(page_title="Family Secret Assistant", page_icon="🍽️", layout="centered")
st.markdown(
    """
    <style>
    .stApp { background: #f7f1e7; color: #2d2118; }
    .fs-hero { padding: 2rem 0 1rem; text-align: center; }
    .fs-hero h1 { font-family: Georgia, serif; font-size: 3rem; margin-bottom: .3rem; }
    .fs-hero p { color: #725c4c; font-size: 1.05rem; }
    .fs-note { background: #fffaf2; border: 1px solid #e3d4bf; border-radius: 14px;
               padding: 1rem 1.2rem; margin: 1rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _secret(key: str) -> str:
    try:
        value = st.secrets.get(key)
    except (FileNotFoundError, AttributeError):
        value = None
    return str(value or os.getenv(key, ""))


@st.cache_resource
def _services() -> tuple[GeminiEmbeddingClient, GeminiGenerationClient, QdrantClient]:
    api_key = _secret("GEMINI_API_KEY")
    embedding_client = GeminiEmbeddingClient(api_key)
    generation_client = GeminiGenerationClient(api_key)
    qdrant = QdrantClient(":memory:")
    index_chunks(load_knowledge_chunks(), embedding_client, qdrant)
    return embedding_client, generation_client, qdrant


st.markdown(
    """
    <div class="fs-hero">
      <div>FAMILY SECRET · NHA TRANG</div>
      <h1>Restaurant Assistant</h1>
      <p>Ask about opening hours, reservations, the menu, or visiting with children.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    <div class="fs-note">
      Try: <b>«Во сколько закрывается кухня?»</b> or
      <b>«Есть ли детская зона?»</b>
    </div>
    """,
    unsafe_allow_html=True,
)

if "assistant_messages" not in st.session_state:
    st.session_state.assistant_messages = []

for message in st.session_state.assistant_messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input("Ask Family Secret… | Спросите о ресторане…")
if question:
    st.session_state.assistant_messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    answer = None
    with st.chat_message("assistant"):
        with st.spinner("Searching Family Secret knowledge…"):
            try:
                embedding_client, generation_client, qdrant = _services()
                results = search_vector_store(question, embedding_client, qdrant, limit=3)
                answer = answer_from_results(question, results, generation_client)
                st.markdown(answer.text)
                if answer.sources:
                    with st.expander("Sources used"):
                        for source in answer.sources:
                            st.caption(f"{source.heading} · {source.source_file}")
            except (requests.RequestException, ValueError, KeyError):
                st.error("The assistant is temporarily unavailable. Please try again shortly.")

    if answer is not None:
        st.session_state.assistant_messages.append(
            {"role": "assistant", "content": answer.text}
        )

st.divider()
st.caption("Family Secret · Lô 1 Trần Quang Khải, Nha Trang · 0354 057 942")
