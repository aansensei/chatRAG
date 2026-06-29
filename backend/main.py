from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.presentation.api.chat import router as chat_router
from app.presentation.api.ingest import router as ingest_router

app = FastAPI(title="ChatRAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(chat_router)
app.include_router(ingest_router)


@app.get("/")
def index():
    return FileResponse("app/static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}
