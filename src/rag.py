import threading
from pathlib import Path

from . import config  # noqa: F401

import chromadb

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT / "knowledge"
COLLECTION_NAME = "aviation_docs"

_collection = None
_lock = threading.Lock()


def chunk_markdown(text: str) -> list[str]:
    """Splits the document by section headers. Each section becomes one chunk."""
    return [s.strip() for s in text.split("\n## ") if s.strip()]


def _get_or_create_collection():
    client = chromadb.PersistentClient(path=str(ROOT / "chroma_db"))
    return client.get_or_create_collection(COLLECTION_NAME)


def ingest(collection=None) -> None:
    """Reads the knowledge base, chunks it, embeds it and stores it."""
    collection = collection or _get_or_create_collection()
    for file in KNOWLEDGE_DIR.glob("*.md"):
        chunks = chunk_markdown(file.read_text(encoding="utf-8"))
        collection.delete(where={"source": file.name})
        collection.upsert(
            documents=chunks,
            ids=[f"{file.stem}-{i}" for i in range(len(chunks))],
            metadatas=[{"source": file.name} for _ in chunks],
        )
        print(f"Ingested {len(chunks)} chunks from {file.name}")


def get_collection():
    global _collection
    with _lock:
        if _collection is None:
            collection = _get_or_create_collection()
            if collection.count() == 0:
                ingest(collection)
            _collection = collection
        return _collection


def warm_up() -> None:
    search("METAR", n_results=1)


def search(query: str, n_results: int = 3) -> list[dict]:
    """Finds the most semantically relevant chunks for a query."""
    collection = get_collection()
    n_results = max(1, min(n_results, collection.count()))
    results = collection.query(query_texts=[query], n_results=n_results)

    return [
        {"text": doc, "source": meta["source"]}
        for doc, meta in zip(results["documents"][0], results["metadatas"][0])
    ]


if __name__ == "__main__":
    ingest()
