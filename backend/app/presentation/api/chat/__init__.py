from fastapi import APIRouter
from pydantic import BaseModel

from app.application.retrieval.ask_question import ask

router = APIRouter(prefix="/chat", tags=["chat"])


class QuestionRequest(BaseModel):
    question: str


@router.post("")
def chat(body: QuestionRequest):
    return ask(body.question)
