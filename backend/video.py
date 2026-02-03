"""POST /api/video – transcript + FAISS + save. Enforce one doc per user."""
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import get_current_user_id
from config import Settings
from database import get_db
from models import UserDoc
from rag_chain import (
    fetch_and_format_transcript,
    transcript_to_documents,
    build_faiss_from_documents,
)

router = APIRouter()
settings = Settings()


class VideoRequest(BaseModel):
    video_id: str


class VideoResponse(BaseModel):
    video_id: str
    message: str


@router.post("/video", response_model=VideoResponse)
def add_video(
    body: VideoRequest,
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
):
    existing = db.query(UserDoc).filter(UserDoc.user_id == user_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have one video. Only one allowed.",
        )
    video_id = body.video_id.strip()
    if not video_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="video_id is required")
    try:
        formatted = fetch_and_format_transcript(video_id, languages=["en"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not fetch transcript for this video: {e!s}",
        )
    if not formatted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transcript available for this video.",
        )
    docs = transcript_to_documents(formatted)
    store_path = Path(settings.stores_path) / str(user_id)
    store_path.mkdir(parents=True, exist_ok=True)
    build_faiss_from_documents(docs, store_path)
    user_doc = UserDoc(user_id=user_id, video_id=video_id)
    db.add(user_doc)
    db.commit()
    return VideoResponse(video_id=video_id, message="Video added successfully.")


@router.get("/video")
def get_video(
    user_id: Annotated[int, Depends(get_current_user_id)],
    db: Annotated[Session, Depends(get_db)],
):
    """Return the user's video_id and remaining question count (for dashboard)."""
    from sqlalchemy import func
    from models import Question

    user_doc = db.query(UserDoc).filter(UserDoc.user_id == user_id).first()
    if not user_doc:
        return {"video_id": None, "remaining_questions": 2}
    count = db.query(func.count(Question.id)).filter(Question.user_id == user_id).scalar() or 0
    remaining = max(0, 2 - count)
    return {"video_id": user_doc.video_id, "remaining_questions": remaining}
