"""RAG upload routes for agent-specific PDF ingestion."""

from bson import ObjectId
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from starlette.concurrency import run_in_threadpool

from config import UPLOADS_ROOT, VECTOR_ROOT
from database import get_db
from services.rag_service import build_vectorstore_from_pdf, record_upload
from utils.security import get_current_user_id

router = APIRouter(prefix="/agents", tags=["rag"])


def _get_agent(coll, user_id: str, agent_id: str):
    try:
        oid = ObjectId(agent_id)
    except Exception:
        return None
    return coll.find_one({"_id": oid, "user_id": user_id})


@router.post("/{agent_id}/rag/upload")
async def upload_pdf_for_agent(
    agent_id: str,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id),
):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only PDF uploads are supported")

    db = get_db()
    agents = db["agents"]

    agent = await run_in_threadpool(lambda: _get_agent(agents, user_id, agent_id))
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")
    if not agent.get("rag_enabled"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enable RAG on this agent before uploading PDFs")

    safe_name = file.filename.replace("..", "_").replace("/", "_").replace("\\", "_")
    dest_dir = UPLOADS_ROOT / agent_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / safe_name

    content = await file.read()
    if len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Max upload size is 20MB")

    dest_path.write_bytes(content)

    def _ingest():
        chunks = build_vectorstore_from_pdf(agent_id=agent_id, pdf_path=dest_path, vector_root=VECTOR_ROOT)
        record_upload(
            db["uploaded_files"],
            user_id=user_id,
            agent_id=agent_id,
            filename=file.filename,
            stored_path=str(dest_path),
            chunks=chunks,
        )
        return chunks

    chunks = await run_in_threadpool(_ingest)
    return {"status": "ok", "chunks_indexed": chunks, "filename": file.filename}
