from reading_evidence.models import Note
from reading_evidence.text import topic_tokens


def citation_for(note: Note, question: str) -> str:
    question_tokens = set(topic_tokens(question))
    lines = note.text.splitlines()
    candidates = [
        (line_number, line, set(topic_tokens(line)))
        for line_number, line in enumerate(lines, start=1)
        if line.strip()
    ]
    if not candidates or not question_tokens:
        return f"{note.source}#L{note.line_start}"

    first_line_number, first_line, first_tokens = candidates[0]
    if first_line.lstrip().startswith("#") and len(question_tokens & first_tokens) >= 2:
        return f"{note.source}#L{first_line_number}"

    best_line_number, _, _ = max(
        candidates,
        key=lambda item: (
            len(question_tokens & item[2]),
            len(question_tokens & item[2]) / max(len(item[2]), 1),
            -item[0],
        ),
    )
    return f"{note.source}#L{best_line_number}"
