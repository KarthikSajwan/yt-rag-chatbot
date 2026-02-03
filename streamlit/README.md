# YT RAG Chatbot – Streamlit frontend

## Setup

1. Install dependencies (from project root or this folder):

   ```bash
   pip install -r streamlit/requirements.txt
   ```

2. Ensure the **backend is running** (from `backend/`):

   ```bash
   uvicorn main:app --reload
   ```

## Run

**From the project root** (`YT Rag Chatbot`):

```bash
streamlit run streamlit/app.py
```

**Or from the `streamlit` folder**:

```bash
cd streamlit
streamlit run app.py
```

The app opens at http://localhost:8501 (or the URL shown in the terminal).

Optional: set `BACKEND_URL` if the API is not at the default:

```bash
set BACKEND_URL=http://127.0.0.1:8000
streamlit run app.py
```

## Flow

1. **Login** or **Register** – JWT is stored in session.
2. **Add your video** – Enter a YouTube video ID (one per account).
3. **Ask** – Up to 2 questions per account; answers are based on the transcript.
