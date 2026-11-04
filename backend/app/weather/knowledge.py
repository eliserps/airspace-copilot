import logging
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import anyio.to_thread

log = logging.getLogger(__name__)

COLLECTION_NAME = "aviation_docs"


@dataclass(frozen=True, slots=True)
class Chunk:
    text: str
    source: str


class KnowledgeSearch(Protocol):
    async def search(self, query: str, n_results: int = 3) -> list[Chunk]: ...


def chunk_markdown(text: str) -> list[str]:
    return [s.strip() for s in text.split("\n## ") if s.strip()]


class KnowledgeBase:
    def __init__(self, store_path: Path, knowledge_dir: Path, embedding_function: Any = None):
        self.store_path = store_path
        self.knowledge_dir = knowledge_dir
        self.embedding_function = embedding_function
        self._collection: Any = None
        self._lock = threading.Lock()

    def _open(self) -> Any:
        import chromadb

        client = chromadb.PersistentClient(path=str(self.store_path))
        if self.embedding_function is None:
            return client.get_or_create_collection(COLLECTION_NAME)
        return client.get_or_create_collection(
            COLLECTION_NAME, embedding_function=self.embedding_function
        )

    def ingest(self, collection: Any = None) -> int:
        collection = collection or self._open()
        total = 0
        for file in sorted(self.knowledge_dir.glob("*.md")):
            chunks = chunk_markdown(file.read_text(encoding="utf-8"))
            collection.delete(where={"source": file.name})
            collection.upsert(
                documents=chunks,
                ids=[f"{file.stem}-{i}" for i in range(len(chunks))],
                metadatas=[{"source": file.name} for _ in chunks],
            )
            log.info("ingested %d chunks from %s", len(chunks), file.name)
            total += len(chunks)
        return total

    @property
    def ready(self) -> bool:
        return self._collection is not None

    def _collection_ready(self) -> Any:
        with self._lock:
            if self._collection is None:
                collection = self._open()
                if collection.count() == 0:
                    self.ingest(collection)
                self._collection = collection
            return self._collection

    def search_sync(self, query: str, n_results: int = 3) -> list[Chunk]:
        collection = self._collection_ready()
        n_results = max(1, min(n_results, collection.count()))
        results = collection.query(query_texts=[query], n_results=n_results)
        return [
            Chunk(text=doc, source=meta["source"])
            for doc, meta in zip(results["documents"][0], results["metadatas"][0], strict=True)
        ]

    async def search(self, query: str, n_results: int = 3) -> list[Chunk]:
        return await anyio.to_thread.run_sync(self.search_sync, query, n_results)

    def warm_up(self) -> None:
        try:
            self.search_sync("METAR", n_results=1)
        except Exception:
            log.exception("knowledge base warm-up failed; it will retry on the first METAR request")
