from dotenv import load_dotenv
load_dotenv()

import logging
import os
import subprocess
import sys
import threading
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "static")
_NO_CACHE = {"Cache-Control": "no-cache, no-store, must-revalidate"}

from app.presentation.api.chat import router as chat_router
from app.presentation.api.ingest import router as ingest_router
from app.presentation.api.memory import router as memory_router
from app.presentation.api.metrics import router as metrics_router
from app.shared.utils.embedders.text_embedder import embed_text

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("chatrag")

_WORKER_MODULES = [
    "workers.ocr_worker",
    "workers.chunk_worker",
    "workers.embedding_worker",
]
_CONCURRENCY = int(os.environ.get("WORKER_CONCURRENCY", 1))
_stop = threading.Event()
_procs: list[subprocess.Popen] = []


def _spawn(module: str) -> subprocess.Popen:
    kwargs = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    return subprocess.Popen(
        [sys.executable, "-m", module],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        **kwargs,
    )


def _watchdog():
    while not _stop.is_set():
        for i, proc in enumerate(_procs):
            if proc.poll() is not None:
                module = _WORKER_MODULES[i % len(_WORKER_MODULES)]
                logger.warning(f"[watchdog] {module} (pid {proc.pid}) died, restarting")
                _procs[i] = _spawn(module)
        time.sleep(3)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _stop.clear()
    for module in _WORKER_MODULES:
        for _ in range(_CONCURRENCY):
            _procs.append(_spawn(module))
            logger.info(f"[lifespan] spawned {module}")

    t = threading.Thread(target=_watchdog, daemon=True)
    t.start()

    # Load the embedding model now instead of on the first user request — importing
    # sentence-transformers/torch and moving the model onto the GPU takes ~15-20s,
    # which otherwise stalls whichever user happens to ask the first question.
    try:
        t0 = time.time()
        embed_text("warmup")
        logger.info(f"[lifespan] embedding model warmed up in {time.time() - t0:.1f}s")
    except Exception as exc:
        logger.warning(f"[lifespan] embedding model warmup failed (will load on first request): {exc}")

    yield

    _stop.set()
    for proc in _procs:
        proc.terminate()
    _procs.clear()


app = FastAPI(title="ChatRAG API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(ingest_router)
app.include_router(memory_router)
app.include_router(metrics_router)


@app.get("/")
def index():
    return FileResponse(os.path.join(_STATIC_DIR, "index.html"), headers=_NO_CACHE)


@app.get("/health")
def health():
    return {"status": "ok"}


app.mount("/assets", StaticFiles(directory=os.path.join(_STATIC_DIR, "assets")), name="assets")
# Serve root-level files (favicon, etc.) and SPA fallback. Must be mounted last
# so API routes and the explicit "/" handler take precedence.
app.mount("/", StaticFiles(directory=_STATIC_DIR, html=True), name="root")
