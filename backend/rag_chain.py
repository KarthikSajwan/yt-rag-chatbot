"""RAG pipeline: transcript fetch, format, split, FAISS build/load, retriever, chain."""
from pathlib import Path
from typing import List

from youtube_transcript_api import YouTubeTranscriptApi
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser

from config import Settings

settings = Settings()

# Embeddings and LLM (lazy / reused)
_embeddings = None
_llm = None


def get_embeddings() -> OpenAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        api_key = settings.openai_api_key
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. Add it to .env in the project root or set the environment variable."
            )
        _embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=api_key)
    return _embeddings


def get_llm() -> ChatOpenAI:
    global _llm
    if _llm is None:
        api_key = settings.openai_api_key
        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. Add it to .env in the project root or set the environment variable."
            )
        _llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2, api_key=api_key)
    return _llm


def fetch_and_format_transcript(video_id: str, languages: List[str] | None = None) -> List[dict]:
    """Fetch transcript and return list of {text, start, duration}. Uses instance API: .fetch()."""
    if languages is None:
        languages = ["en"]
    ytt_api = YouTubeTranscriptApi()
    fetched_transcript = ytt_api.fetch(video_id, languages=languages)
    return [
        {"text": snippet.text, "start": snippet.start, "duration": snippet.duration}
        for snippet in fetched_transcript
    ]


def transcript_to_documents(formatted: List[dict]) -> List[Document]:
    """Convert formatted transcript to LangChain Documents with metadata."""
    return [
        Document(
            page_content=item["text"],
            metadata={"start": item["start"], "duration": item["duration"]},
        )
        for item in formatted
    ]


def build_faiss_from_documents(docs: List[Document], store_path: str | Path) -> None:
    """Chunk docs, build FAISS, save to store_path."""
    path = Path(store_path)
    path.mkdir(parents=True, exist_ok=True)
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunked = splitter.split_documents(docs)
    embeddings = get_embeddings()
    vector_store = FAISS.from_documents(chunked, embeddings)
    vector_store.save_local(str(path))


def load_faiss_retriever(store_path: str | Path, k: int = 4):
    """Load FAISS from disk and return a retriever."""
    embeddings = get_embeddings()
    vector_store = FAISS.load_local(str(store_path), embeddings, allow_dangerous_deserialization=True)
    return vector_store.as_retriever(search_type="similarity", search_kwargs={"k": k})


def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


def build_rag_chain(retriever):
    """Build the RAG chain: parallel context + question -> prompt -> LLM -> parser."""
    prompt = PromptTemplate(
        template="""You are a helpful assistant.
Answer ONLY from the provided transcript context.
If the context is insufficient, say "I don't know."

Context:
{context}

Question:
{question}
""",
        input_variables=["context", "question"],
    )
    llm = get_llm()
    parser = StrOutputParser()
    parallel = RunnableParallel(
        {"context": retriever | RunnableLambda(format_docs), "question": RunnablePassthrough()}
    )
    return parallel | prompt | llm | parser
