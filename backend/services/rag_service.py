"""RAG: PDF ingestion, chunking, embeddings, and FAISS vector store per agent."""

import os
from pathlib import Path
from typing import List, Optional

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pymongo.collection import Collection

EMBED_MODEL = os.getenv("HF_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


def _vector_dir(base: Path, agent_id: str) -> Path:
    return base / agent_id


def build_vectorstore_from_pdf(
    *,
    agent_id: str,
    pdf_path: Path,
    vector_root: Path,
) -> int:
    loader = PyPDFLoader(str(pdf_path))
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(docs)
    if not chunks:
        return 0

    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    out_dir = _vector_dir(vector_root, agent_id)
    out_dir.mkdir(parents=True, exist_ok=True)

    if (out_dir / "index.faiss").exists():
        store = FAISS.load_local(
            str(out_dir),
            embeddings,
            allow_dangerous_deserialization=True,
        )
        store.add_documents(chunks)
    else:
        store = FAISS.from_documents(chunks, embeddings)
    store.save_local(str(out_dir))
    return len(chunks)


def load_vectorstore(agent_id: str, vector_root: Path) -> Optional[FAISS]:
    out_dir = _vector_dir(vector_root, agent_id)
    if not (out_dir / "index.faiss").exists():
        return None
    embeddings = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
    return FAISS.load_local(str(out_dir), embeddings, allow_dangerous_deserialization=True)


def retrieve_context(agent_id: str, query: str, vector_root: Path, k: int = 4) -> str:
    store = load_vectorstore(agent_id, vector_root)
    if store is None:
        return ""
    docs = store.similarity_search(query, k=k)
    parts: List[str] = []
    for i, d in enumerate(docs, start=1):
        parts.append(f"[{i}] {d.page_content}")
    return "\n\n".join(parts)


def record_upload(
    files_coll: Collection,
    *,
    user_id: str,
    agent_id: str,
    filename: str,
    stored_path: str,
    chunks: int,
) -> None:
    from datetime import datetime, timezone

    files_coll.insert_one(
        {
            "user_id": user_id,
            "agent_id": agent_id,
            "filename": filename,
            "stored_path": stored_path,
            "chunks": chunks,
            "created_at": datetime.now(timezone.utc),
        }
    )
