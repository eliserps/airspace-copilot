import truststore
truststore.inject_into_ssl()

import chromadb
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT / "knowledge"
COLLECTION_NAME = "aviation_docs"

client = chromadb.PersistentClient(path=str(ROOT / "chroma_db"))

def chunk_markdown(text: str) -> list[str]:
    """Splits the document by section headers. Each section becomes one chunk."""
    return [s.strip() for s in text.split("\n## ") if s.strip()]

def ingest() -> None:
    """Reads the knowledge base, chunks it, embeds it and stores it."""
    collection = client.get_or_create_collection(COLLECTION_NAME)
    for file in KNOWLEDGE_DIR.glob("*.md"):
        chunks = chunk_markdown(file.read_text(encoding="utf-8"))
        collection.upsert(
            documents=chunks,
            ids=[f"{file.stem}-{i}" for i in range(len(chunks))],
            metadatas=[{"source": file.name} for _ in chunks],
        )
        print(f"Ingested {len(chunks)} chunks from {file.name}")

def search(query: str, n_results: int = 3) -> list[dict]:
    """Finds the most semantically relevant chunks for a query."""
    collection = client.get_collection(COLLECTION_NAME)
    results = collection.query(query_texts=[query], n_results=n_results)

    return [
        {"text": doc, "source": meta["source"]}
        for doc, meta in zip(results["documents"][0], results["metadatas"][0])
    ]

if __name__ == "__main__":
    ingest()