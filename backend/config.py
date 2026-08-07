import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BACKEND_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_ROOT.parent

UPLOADS_ROOT = Path(os.getenv("UPLOADS_DIR", str(BACKEND_ROOT / "uploads")))
VECTOR_ROOT = Path(os.getenv("VECTORSTORE_DIR", str(BACKEND_ROOT / "vectorstore")))
FRONTEND_ROOT = Path(os.getenv("FRONTEND_DIR", str(PROJECT_ROOT / "frontend")))

# Ensure runtime directories exist at import (safe for local dev).
UPLOADS_ROOT.mkdir(parents=True, exist_ok=True)
VECTOR_ROOT.mkdir(parents=True, exist_ok=True)
