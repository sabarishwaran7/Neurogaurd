"""FastAPI application entrypoint: API, static frontend, security middleware."""

import io
import os
import zipfile
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import FRONTEND_ROOT, PROJECT_ROOT
from database import close_client, ensure_indexes, get_db
from limiter_config import limiter
from routes.agent_routes import (
    agents_router,
    chat_router,
    dashboard_router,
    public_agent_router,
)
from routes.auth_routes import router as auth_router
from routes.rag_routes import router as rag_router
from routes.neuroguard_routes import router as neuroguard_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate Mongo connectivity early so misconfiguration fails fast.
    get_db().command("ping")
    ensure_indexes()
    yield
    close_client()


app = FastAPI(title="Agentic AI Platform", version="1.0.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/extension/download")
async def download_extension():
    """Zip the chrome-extension folder on the fly and serve as a download."""
    ext_dir = PROJECT_ROOT / "chrome-extension"
    if not ext_dir.exists():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Extension folder not found")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in ext_dir.rglob("*"):
            if file_path.is_file() and ".git" not in file_path.parts:
                arcname = f"neuroguard-extension/{file_path.relative_to(ext_dir)}"
                zf.write(file_path, arcname)
    buf.seek(0)

    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=neuroguard-extension.zip"},
    )


app.include_router(auth_router, prefix="/api")
app.include_router(agents_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(rag_router, prefix="/api")
app.include_router(neuroguard_router, prefix="/api")
app.include_router(public_agent_router)


def _mount_frontend() -> None:
    root = Path(FRONTEND_ROOT)
    if not root.exists():
        return

    static_dir = root / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    def make_file_handler(file_path: Path):
        async def _handler():
            return FileResponse(str(file_path))

        return _handler

    app.add_api_route("/", make_file_handler(root / "index.html"), methods=["GET"])

    page_routes = {
        "/login": root / "login.html",
        "/register": root / "register.html",
        "/dashboard": root / "dashboard.html",
        "/create-agent": root / "create-agent.html",
        "/chat": root / "chat.html",
        "/agents": root / "agents.html",
        "/extension": root / "extension.html",
        "/browse-dashboard": root / "browse-dashboard.html",
    }

    for route, file_path in page_routes.items():
        if file_path.exists():
            app.add_api_route(route, make_file_handler(file_path), methods=["GET"])


_mount_frontend()
