from __future__ import annotations

from reading_evidence.models import Note, Relation
from reading_evidence.text import PREDICATE_HINTS, claim_has_negative_polarity, topic_tokens


def _line_candidates(note: Note) -> list[tuple[int, str, set[str]]]:
    return [
        (line_number, line, set(topic_tokens(line)))
        for line_number, line in enumerate(note.text.splitlines(), start=note.line_start)
        if line.strip()
    ]


def _line_supports_relation(question: str, line: str, relation: Relation) -> bool:
    ordered_question_tokens = topic_tokens(question)
    question_tokens = set(ordered_question_tokens)
    line_tokens = set(topic_tokens(line))
    overlap = question_tokens & line_tokens
    if not overlap:
        return False

    if relation == Relation.RELATED:
        return bool(overlap - PREDICATE_HINTS)
    if relation not in {Relation.SUPPORT, Relation.COUNTER_EVIDENCE} or len(overlap) < 2:
        return False

    anchors = (question_tokens & PREDICATE_HINTS) or set(ordered_question_tokens[-2:])
    question_negative = claim_has_negative_polarity(question, anchors)
    line_negative = claim_has_negative_polarity(line, anchors)
    if relation == Relation.SUPPORT:
        return question_negative == line_negative
    return question_negative != line_negative


def citation_for(note: Note, question: str, relation: Relation | None = None) -> str:
    question_tokens = set(topic_tokens(question))
    candidates = _line_candidates(note)
    if not candidates or not question_tokens:
        return f"{note.source}#L{note.line_start}"

    if relation is not None:
        relation_candidates = [
            item for item in candidates if _line_supports_relation(question, item[1], relation)
        ]
        if relation_candidates:
            first_line_number, first_line, first_tokens = relation_candidates[0]
            if first_line.lstrip().startswith("#") and len(question_tokens & first_tokens) >= 2:
                return f"{note.source}#L{first_line_number}"
            best_line_number, _, _ = max(
                relation_candidates,
                key=lambda item: (
                    len(question_tokens & item[2]),
                    len(question_tokens & item[2]) / max(len(item[2]), 1),
                    -item[0],
                ),
            )
            return f"{note.source}#L{best_line_number}"

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


def validate_evidence_quote(
    note: Note,
    evidence_line: int,
    evidence_quote: str,
) -> tuple[bool, str]:
    """Validate an exact, complete single-line quote against an indexed note."""
    if "\n" in evidence_quote or "\r" in evidence_quote:
        return False, "evidence_quote_not_single_line"
    internal_index = evidence_line - note.line_start
    lines = note.text.splitlines()
    if internal_index < 0 or internal_index >= len(lines):
        return False, "evidence_line_out_of_range"
    if not lines[internal_index].strip():
        return False, "evidence_line_blank"
    if evidence_quote != lines[internal_index]:
        return False, "evidence_quote_not_exact"
    return True, "ok"


def citation_for_evidence(note: Note, evidence_line: int, evidence_quote: str) -> str:
    """Build a citation only after exact source-line grounding succeeds."""
    valid, reason = validate_evidence_quote(note, evidence_line, evidence_quote)
    if not valid:
        raise ValueError(f"Invalid evidence quote: {reason}")
    return f"{note.source}#L{evidence_line}"


def validate_citation(
    note: Note,
    question: str,
    relation: Relation,
    citation: str,
) -> tuple[bool, str]:
    prefix = f"{note.source}#L"
    if not citation.startswith(prefix):
        return False, "citation_source_mismatch"
    try:
        line_number = int(citation[len(prefix) :])
    except ValueError:
        return False, "citation_line_invalid"

    internal_index = line_number - note.line_start
    lines = note.text.splitlines()
    if internal_index < 0 or internal_index >= len(lines):
        return False, "citation_line_out_of_range"
    line = lines[internal_index]
    if not line.strip():
        return False, "citation_line_blank"
    if not _line_supports_relation(question, line, relation):
        return False, "citation_line_not_relation_consistent"
    return True, "ok"
