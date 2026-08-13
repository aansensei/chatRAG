from dotenv import load_dotenv
load_dotenv()

import logging
import os
import subprocess
import sys
import threading
import time
from contextlib import asynccontextmanager

# Must be set before the first embed_text/embed_chunks call in this process (see
# app/shared/utils/embedders/text_embedder.py) — this process only ever embeds
# single short chat-query strings, so GPU latency isn't worth a second full model
# copy competing with the embedding_worker subprocess for VRAM on a 4GB GPU.
os.environ.setdefault("EMBEDDING_DEVICE", "cpu")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

_STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app", "static")
_NO_CACHE = {"Cache-Control": "no-cache, no-store, must-revalidate"}

from app.presentation.api.auth import router as auth_router, bootstrap_admin, get_current_user
from app.infrastructure.storage.local.local_storage import migrate_legacy_chat_sessions
from app.presentation.api.chat import router as chat_router
from app.presentation.api.ingest import router as ingest_router
from app.presentation.api.memory import router as memory_router, migrate_legacy_memories
from app.presentation.api.metrics import router as metrics_router
from app.presentation.api.chat import _OLLAMA_URL, _OLLAMA_MODEL
from app.presentation.middleware.rate_limit import RateLimitMiddleware
from app.presentation.middleware.upload_limit import MaxUploadSizeMiddleware
from app.presentation.middleware.security_headers import SecurityHeadersMiddleware
from app.infrastructure.queue.redis.publisher import iter_jobs, set_job_status
from app.shared.utils.embedders.text_embedder import embed_text

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("chatrag")

_WORKER_MODULES = [
    "workers.ocr_worker",
    "workers.chunk_worker",
    "workers.embedding_worker",
]
_STEP_TO_MODULE = {
    "ocr": "workers.ocr_worker",
    "chunk": "workers.chunk_worker",
    "embed": "workers.embedding_worker",
}
# A worker can hang forever inside a blocking call (e.g. a CUDA driver fault)
# without ever exiting or raising a catchable exception — the process stays
# alive so the plain exit-code watchdog below never notices, and the job it
# was holding just sits at the same progress % permanently. Detect that by
# job staleness instead of process liveness.
_STALE_JOB_SECONDS = 90
_CONCURRENCY = int(os.environ.get("WORKER_CONCURRENCY", 1))
_stop = threading.Event()
_procs: list[subprocess.Popen] = []


def _spawn(module: str) -> subprocess.Popen:
    kwargs = {}
    if sys.platform == "win32":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
    # subprocess.Popen inherits the parent's environment by default — the
    # EMBEDDING_DEVICE=cpu override above is meant only for this process's own
    # query embeddings, not for worker subprocesses doing bulk document
    # embedding, which still want the GPU. Strip it so it doesn't leak down.
    env = os.environ.copy()
    env.pop("EMBEDDING_DEVICE", None)
    return subprocess.Popen(
        [sys.executable, "-m", module],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        env=env,
        **kwargs,
    )


def _warm_ollama():
    # Preloads the suggestions model into Ollama's memory in the background so
    # the first "/chat/suggestions" call after a restart doesn't hit the model's
    # cold-start latency and silently fall back to static templates.
    import httpx
    try:
        httpx.post(
            f"{_OLLAMA_URL}/api/generate",
            json={"model": _OLLAMA_MODEL, "prompt": "hi", "stream": False, "keep_alive": "30m"},
            timeout=httpx.Timeout(connect=3.0, read=30.0, write=2.0, pool=2.0),
        )
        logger.info(f"[lifespan] Ollama model {_OLLAMA_MODEL} warmed up")
    except Exception as exc:
        logger.warning(f"[lifespan] Ollama warmup failed (will load on first request): {exc}")


def _cleanup_orphaned_workers():
    # A force-killed uvicorn parent (taskkill/Stop-Process) skips this lifespan's shutdown
    # handler, leaving its ocr/chunk/embedding worker subprocesses running and competing
    # for resources on the next start. Since _procs is still empty at this point, any
    # matching process found here must be debris from a previous run.
    import psutil
    killed = 0
    for proc in psutil.process_iter(["pid", "cmdline"]):
        try:
            cmdline = " ".join(proc.info["cmdline"] or [])
            if any(module in cmdline for module in _WORKER_MODULES):
                proc.kill()
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    if killed:
        logger.warning(f"[lifespan] cleaned up {killed} orphaned worker process(es) from a previous run")


def _sweep_orphaned_jobs():
    # Nothing can legitimately be mid-processing the instant this process starts —
    # any job still in a non-terminal status is debris from a previous run that
    # crashed, hung, or was force-killed before it could report failure. Left
    # alone, the frontend keeps polling that job_id and shows a progress bar
    # frozen at whatever % it last reported, forever.
    try:
        swept = 0
        for job_id, status in iter_jobs():
            if status.get("status") not in ("completed", "failed"):
                set_job_status(job_id, status="failed", error="Interrupted by server restart — please re-upload")
                swept += 1
        if swept:
            logger.warning(f"[lifespan] marked {swept} orphaned job(s) from a previous run as failed")
    except Exception as exc:
        # Redis being briefly unreachable at startup shouldn't take the whole
        # app down — this sweep is a best-effort cleanup, not a hard dependency.
        logger.warning(f"[lifespan] orphaned-job sweep skipped (Redis unavailable?): {exc}")


def _watchdog():
    while not _stop.is_set():
        try:
            for i, proc in enumerate(_procs):
                if proc.poll() is not None:
                    module = _WORKER_MODULES[i % len(_WORKER_MODULES)]
                    logger.warning(f"[watchdog] {module} (pid {proc.pid}) died, restarting")
                    _procs[i] = _spawn(module)

            # A worker can hang forever inside a blocking call without exiting or
            # raising — proc.poll() above stays None, so that check alone never
            # catches it. Detect it from the job side instead: a job whose status
            # hasn't moved in _STALE_JOB_SECONDS is either being processed by a
            # dead-but-not-exited worker, or was abandoned mid-flight some other
            # way — either way, force the matching worker to restart and fail the
            # job so the upload doesn't stay stuck at the same % indefinitely.
            now = time.time()
            for job_id, status in iter_jobs():
                if status.get("status") not in ("extracting", "chunking", "embedding"):
                    continue
                try:
                    updated_at = float(status.get("updated_at", 0))
                except ValueError:
                    continue
                if now - updated_at < _STALE_JOB_SECONDS:
                    continue
                module = _STEP_TO_MODULE.get(status.get("step", ""))
                logger.warning(f"[watchdog] job {job_id} stale for {now - updated_at:.0f}s on step={status.get('step')} — killing {module}")
                set_job_status(job_id, status="failed", error="Worker timed out — please re-upload")
                if module:
                    for i, m in enumerate(_WORKER_MODULES):
                        if m == module and i < len(_procs):
                            _procs[i].kill()
                            _procs[i] = _spawn(module)
                            break
        except Exception as exc:
            # A transient Redis hiccup must not silently kill this thread —
            # that would mean losing both the dead-process restart and the
            # stale-job detection for the rest of the process's lifetime.
            logger.warning(f"[watchdog] iteration failed, will retry: {exc}")
        time.sleep(3)


@asynccontextmanager
async def lifespan(app: FastAPI):
    _cleanup_orphaned_workers()
    _sweep_orphaned_jobs()
    bootstrap_admin()
    migrate_legacy_memories()
    migrate_legacy_chat_sessions()
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

    threading.Thread(target=_warm_ollama, daemon=True).start()

    yield

    _stop.set()
    for proc in _procs:
        proc.terminate()
    _procs.clear()


app = FastAPI(title="ChatRAG API", lifespan=lifespan)

# The frontend is served from this same FastAPI app (mounted static files below), so
# legitimate same-origin browser requests never need CORS headers at all — "*" only
# opened the door for OTHER origins (e.g. a page in another tab) to read responses
# from every unauthenticated endpoint. Configurable via CORS_ORIGINS (comma-separated)
# for when this gets deployed somewhere other than localhost.
_cors_origins = [o.strip() for o in os.environ.get(
    "CORS_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000"
).split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(MaxUploadSizeMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(auth_router)
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
