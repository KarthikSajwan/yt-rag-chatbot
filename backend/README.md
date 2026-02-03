# YT RAG Chatbot – Backend

FastAPI backend: auth (register/login), one video per user, max 2 questions per user.

## Setup

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv venv
   venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

2. Copy `.env.example` from the project root to `backend/.env` (or set env vars). Required:

   - `OPENAI_API_KEY` – your OpenAI API key
   - `SECRET_KEY` – long random string for JWT signing
   - `DATABASE_URL` – default `sqlite:///./yt_rag.db`
   - `STORES_PATH` – default `./data/stores` (FAISS per user)

## Run

From the `backend` directory:

```bash
uvicorn main:app --reload
```

API: http://127.0.0.1:8000  
Docs: http://127.0.0.1:8000/docs

## API Summary

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/register` | No | Register with `email`, `password`; returns JWT |
| POST | `/auth/login` | No | Login with `email`, `password`; returns JWT |
| GET | `/api/video` | Bearer | Get current video_id and remaining_questions (or 404) |
| POST | `/api/video` | Bearer | Add one video by `video_id` (409 if already have one) |
| POST | `/api/ask` | Bearer | Ask `question`; returns answer and remaining_questions (403 after 2 questions) |

Use header: `Authorization: Bearer <token>` for protected routes.

## Quick test (after server is running)

1. Register: `POST /auth/register` with `{"email": "you@example.com", "password": "secret"}`.
2. Use the returned `access_token` in `Authorization: Bearer <token>`.
3. Add video: `POST /api/video` with `{"video_id": "dQw4w9WgXcQ"}` (or any video with English transcript).
4. Ask: `POST /api/ask` with `{"question": "What is this video about?"}` (up to 2 times).
