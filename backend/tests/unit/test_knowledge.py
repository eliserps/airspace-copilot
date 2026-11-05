from pathlib import Path

from app.core.config import Settings
from app.weather.knowledge import ReferenceDoc, format_reference, load_reference


def test_loads_every_markdown_file_in_name_order(tmp_path: Path) -> None:
    (tmp_path / "b.md").write_text("## Clouds\nBKN broken\n", encoding="utf-8")
    (tmp_path / "a.md").write_text("## Wind\nVRB variable\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("ignored", encoding="utf-8")
    assert load_reference(tmp_path) == [
        ReferenceDoc("a.md", "## Wind\nVRB variable"),
        ReferenceDoc("b.md", "## Clouds\nBKN broken"),
    ]


def test_format_labels_each_source() -> None:
    text = format_reference([ReferenceDoc("a.md", "A"), ReferenceDoc("b.md", "B")])
    assert text == "[source: a.md]\nA\n\n---\n\n[source: b.md]\nB"


def test_bundled_reference_is_loaded() -> None:
    docs = load_reference(Settings(_env_file=None).knowledge_dir)
    assert [d.source for d in docs] == ["metar_reference.md"]
    assert "CAVOK" in docs[0].text
