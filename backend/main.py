"""FastAPI app: CORS, router includes. Tables created on startup."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db, get_db
from auth import router as auth_router
from video import router as video_router
from ask import router as ask_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    import os
    from config import Settings
    s = Settings()
    if s.openai_api_key:
        os.environ["OPENAI_API_KEY"] = s.openai_api_key
    init_db()
    yield


app = FastAPI(title="YT RAG Chatbot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(video_router, prefix="/api", tags=["video"])
app.include_router(ask_router, prefix="/api", tags=["ask"])


@app.get("/")
def root():
    return {"message": "YT RAG Chatbot API"}
