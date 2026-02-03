"""POST /api/ask – load FAISS, RAG, save question. Enforce max 2 questions."""
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import get_current_user_id
from config import Settings
from database import get_db
from models import UserDoc, Question
from rag_chain import load_faiss_retriever, build_rag_chain

router = APIRouter()
settings = Settings()


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str
    remaining_questions: int


@router.post("/ask", response_model=AskResponse)
def ask(
    body: AskRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
):
    user_doc = db.query(UserDoc).filter(UserDoc.user_id == user_id).first()
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Add a video first.",
        )
    question_count = db.query(Question).filter(Question.user_id == user_id).count()
    if question_count >= 2:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You have used your 2 questions.",
        )
    question_text = (body.question or "").strip()
    if not question_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="question is required")
    store_path = Path(settings.stores_path) / str(user_id)
    if not (store_path / "index.faiss").exists():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Add a video first.",
        )
    retriever = load_faiss_retriever(store_path, k=4)
    chain = build_rag_chain(retriever)
    answer = chain.invoke(question_text)
    q = Question(
        user_id=user_id,
        question_text=question_text,
        answer_text=answer,
    )
    db.add(q)
    db.commit()
    remaining = max(0, 2 - (question_count + 1))
    return AskResponse(answer=answer, remaining_questions=remaining)
