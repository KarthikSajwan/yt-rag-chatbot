"""
YT RAG Chatbot – Streamlit frontend.
Run from project root: streamlit run streamlit/app.py
Run from streamlit folder: streamlit run app.py
Requires: streamlit, requests. Backend must be running at BACKEND_URL (default http://127.0.0.1:8000).
"""
import os
import streamlit as st
import requests

BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")


def api_headers():
    token = st.session_state.get("token")
    if not token:
        return {}
    return {"Authorization": f"Bearer {token}"}


def register(email: str, password: str):
    r = requests.post(
        f"{BACKEND_URL}/auth/register",
        json={"email": email, "password": password},
        timeout=30,
    )
    if r.status_code == 200:
        st.session_state["token"] = r.json()["access_token"]
        return None
    try:
        return r.json().get("detail", r.text)
    except Exception:
        return r.text


def login(email: str, password: str):
    r = requests.post(
        f"{BACKEND_URL}/auth/login",
        json={"email": email, "password": password},
        timeout=30,
    )
    if r.status_code == 200:
        st.session_state["token"] = r.json()["access_token"]
        return None
    try:
        return r.json().get("detail", r.text)
    except Exception:
        return r.text


def get_video_info():
    r = requests.get(f"{BACKEND_URL}/api/video", headers=api_headers(), timeout=30)
    if r.status_code != 200:
        return None
    return r.json()


def add_video(video_id: str):
    r = requests.post(
        f"{BACKEND_URL}/api/video",
        json={"video_id": video_id.strip()},
        headers=api_headers(),
        timeout=120,
    )
    if r.status_code == 200:
        return None, r.json()
    try:
        detail = r.json().get("detail", r.text)
    except Exception:
        detail = r.text
    return detail, None


def ask_question(question: str):
    r = requests.post(
        f"{BACKEND_URL}/api/ask",
        json={"question": question.strip()},
        headers=api_headers(),
        timeout=60,
    )
    if r.status_code == 200:
        return None, r.json()
    try:
        detail = r.json().get("detail", r.text)
    except Exception:
        detail = r.text
    return detail, None


def main():
    st.set_page_config(page_title="YT RAG Chatbot", page_icon="🎬", layout="centered")
    st.title("YT RAG Chatbot")
    st.caption("One video per account · 2 questions max")

    if "token" not in st.session_state:
        st.session_state["token"] = None

    # ----- Not logged in: show login / register -----
    if not st.session_state["token"]:
        tab1, tab2 = st.tabs(["Login", "Register"])
        with tab1:
            with st.form("login"):
                st.subheader("Login")
                email = st.text_input("Email", type="default", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                if st.form_submit_button("Login"):
                    if email and password:
                        err = login(email, password)
                        if err:
                            st.error(err)
                        else:
                            st.rerun()
                    else:
                        st.warning("Enter email and password.")
        with tab2:
            with st.form("register"):
                st.subheader("Register")
                email = st.text_input("Email", type="default", key="reg_email")
                password = st.text_input("Password", type="password", key="reg_password")
                if st.form_submit_button("Register"):
                    if email and password:
                        err = register(email, password)
                        if err:
                            st.error(err)
                        else:
                            st.rerun()
                    else:
                        st.warning("Enter email and password.")
        return

    # ----- Logged in: dashboard -----
    st.sidebar.subheader("Account")
    if st.sidebar.button("Logout"):
        st.session_state["token"] = None
        st.rerun()

    info = get_video_info()
    if info is None:
        st.error("Could not load your data. Check that the backend is running and you are logged in.")
        return

    video_id = info.get("video_id")
    remaining = info.get("remaining_questions", 2)

    # ----- No video yet: add video form -----
    if not video_id:
        st.subheader("Add your video")
        st.markdown("Enter a **YouTube video ID** (e.g. from `youtube.com/watch?v=VIDEO_ID`).")
        with st.form("add_video"):
            vid = st.text_input("Video ID", placeholder="e.g. dQw4w9WgXcQ", key="video_id")
            if st.form_submit_button("Add video"):
                if vid and vid.strip():
                    err, data = add_video(vid.strip())
                    if err:
                        st.error(err)
                    else:
                        st.success(f"Video **{data['video_id']}** added. You can ask up to 2 questions.")
                        st.rerun()
                else:
                    st.warning("Enter a video ID.")
        return

    # ----- Has video: show status and ask form -----
    # Use stored remaining if we just asked (so banner updates after rerun)
    if "remaining_questions" in st.session_state and st.session_state.get("remaining_questions") is not None:
        remaining = st.session_state["remaining_questions"]
    st.subheader("Your video")
    st.info(f"**Video ID:** `{video_id}` · **Questions left:** {remaining}")

    # Show last answer if we have one (stored before st.rerun so it persists)
    if st.session_state.get("last_answer"):
        with st.expander("Last answer", expanded=True):
            st.markdown("**Question:**")
            st.write(st.session_state.get("last_question", ""))
            st.markdown("**Answer:**")
            st.write(st.session_state["last_answer"])

    if remaining <= 0:
        st.warning("You have used your 2 questions. No more questions allowed for this account.")
        return

    st.subheader("Ask a question")
    with st.form("ask"):
        question = st.text_area("Question", placeholder="Ask something about the transcript...", key="question")
        if st.form_submit_button("Ask"):
            if question and question.strip():
                err, data = ask_question(question.strip())
                if err:
                    st.error(err)
                else:
                    st.session_state["last_answer"] = data["answer"]
                    st.session_state["last_question"] = question.strip()
                    st.session_state["remaining_questions"] = data["remaining_questions"]
                    st.rerun()
            else:
                st.warning("Enter a question.")


if __name__ == "__main__":
    main()
