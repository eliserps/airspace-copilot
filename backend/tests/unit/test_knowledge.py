import hashlib
import math
from pathlib import Path
from typing import Any, cast

import pytest
from chromadb import Documents, EmbeddingFunction, Embeddings

from app.weather.knowledge import KnowledgeBase

pytestmark = pytest.mark.anyio

DIMENSIONS = 64


class BagOfWords(EmbeddingFunction[Documents]):
    def __init__(self) -> None:
        pass

    def __call__(self, input: Documents) -> Embeddings:
        vectors = []
        for text in input:
            vector = [0.0] * DIMENSIONS
            for word in text.lower().split():
                bucket = int(hashlib.md5(word.encode()).hexdigest(), 16) % DIMENSIONS
                vector[bucket] += 1.0
            norm = math.sqrt(sum(v * v for v in vector)) or 1.0
            vectors.append([v / norm for v in vector])
        return cast(Embeddings, vectors)

    @staticmethod
    def name() -> str:
        return "bag-of-words-test"

    def get_config(self) -> dict[str, Any]:
        return {}

    @staticmethod
    def build_from_config(config: dict[str, Any]) -> "BagOfWords":
        return BagOfWords()


@pytest.fixture
def knowledge(tmp_path: Path) -> KnowledgeBase:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "metar.md").write_text(
        "# METAR\n## Wind\nVRB means variable wind direction\n"
        "## Clouds\nBKN broken clouds OVC overcast ceiling\n",
        encoding="utf-8",
    )
    return KnowledgeBase(tmp_path / "store", docs, embedding_function=BagOfWords())


async def test_first_search_ingests_and_finds_the_relevant_section(
    knowledge: KnowledgeBase,
) -> None:
    assert knowledge.ready is False
    chunks = await knowledge.search("overcast ceiling BKN", n_results=1)
    assert knowledge.ready is True
    assert chunks[0].source == "metar.md"
    assert chunks[0].text.startswith("Clouds")


async def test_n_results_is_capped_at_the_number_of_chunks(knowledge: KnowledgeBase) -> None:
    assert len(await knowledge.search("wind", n_results=50)) == 3


def test_ingest_replaces_previous_chunks_of_a_file(knowledge: KnowledgeBase) -> None:
    assert knowledge.ingest() == 3
    assert knowledge.ingest() == 3
    assert len(knowledge.search_sync("wind", n_results=50)) == 3


class Unavailable(KnowledgeBase):
    def _open(self) -> Any:
        raise RuntimeError("store unavailable")


def test_warm_up_swallows_failures(tmp_path: Path) -> None:
    broken = Unavailable(tmp_path / "store", tmp_path / "docs")
    broken.warm_up()
    assert broken.ready is False
