from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from reading_evidence.models import Note


INDEX_VERSION = 1
SUPPORTED_SUFFIXES = {".md", ".txt"}


def _title(path: Path, text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem.replace("-", " ").title()


def _note_id(path: Path) -> str:
    value = path.with_suffix("").as_posix().replace("/", "-")
    return value.lower()


def _content_hash(notes: list[Note]) -> str:
    digest = hashlib.sha256()
    for note in notes:
        digest.update(note.note_id.encode())
        digest.update(b"\0")
        digest.update(note.text.encode())
        digest.update(b"\0")
    return digest.hexdigest()


def _first_content_line(raw_text: str) -> int:
    for line_number, line in enumerate(raw_text.splitlines(), start=1):
        if line.strip():
            return line_number
    return 1


def ingest_corpus(corpus_path: Path, index_path: Path) -> dict[str, Any]:
    corpus_path = corpus_path.resolve()
    if not corpus_path.is_dir():
        raise ValueError(f"Corpus directory does not exist: {corpus_path}")

    notes: list[Note] = []
    for path in sorted(corpus_path.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        resolved = path.resolve()
        if not resolved.is_relative_to(corpus_path):
            raise ValueError(f"Corpus file resolves outside the corpus root: {path}")
        relative = path.relative_to(corpus_path)
        raw_text = path.read_text(encoding="utf-8")
        text = raw_text.strip()
        if not text:
            continue
        notes.append(
            Note(
                note_id=_note_id(relative),
                title=_title(path, text),
                text=text,
                source=relative.as_posix(),
                line_start=_first_content_line(raw_text),
            )
        )

    if not notes:
        raise ValueError("Corpus contains no non-empty .md or .txt notes")
    ids = [note.note_id for note in notes]
    if len(ids) != len(set(ids)):
        raise ValueError("Corpus produces duplicate note IDs")
    if any(Path(note.source).is_absolute() for note in notes):
        raise ValueError("Index sources must be relative to the corpus root")

    payload = {
        "version": INDEX_VERSION,
        "document_count": len(notes),
        "corpus_sha256": _content_hash(notes),
        "notes": [note.__dict__ for note in notes],
    }
    index_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = index_path.with_name(f".{index_path.name}.tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(index_path)
    return {key: value for key, value in payload.items() if key != "notes"}


def load_index(index_path: Path) -> tuple[list[Note], dict[str, Any]]:
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    if payload.get("version") != INDEX_VERSION:
        raise ValueError(f"Unsupported index version: {payload.get('version')}")
    notes = [Note(**value) for value in payload.get("notes", [])]
    if len(notes) != payload.get("document_count"):
        raise ValueError("Index document count does not match stored notes")
    if _content_hash(notes) != payload.get("corpus_sha256"):
        raise ValueError("Index corpus hash mismatch")
    if any(Path(note.source).is_absolute() for note in notes):
        raise ValueError("Index contains an absolute source path")
    metadata = {key: value for key, value in payload.items() if key != "notes"}
    return notes, metadata
