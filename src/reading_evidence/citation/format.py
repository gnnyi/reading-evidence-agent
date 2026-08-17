from reading_evidence.models import Note


def citation_for(note: Note) -> str:
    return f"{note.source}#L{note.line_start}"
