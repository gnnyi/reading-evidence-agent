from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from reading_evidence.models import Relation, RelationJudgment, RetrievalCandidate


@runtime_checkable
class RelationJudge(Protocol):
    """Candidate-level relation judge used by the evidence pipeline."""

    judge_id: str
    citation_mode: str

    def judge(
        self,
        question: str,
        candidate: RetrievalCandidate,
    ) -> RelationJudgment:
        """Judge one retrieved candidate against the question or claim."""
        ...

    def empty_trace(self) -> dict[str, Any] | None:
        """Return safe zero-request metadata when retrieval yields no candidates."""
        ...


def judgment_contract_error(judgment: Any) -> str | None:
    if not isinstance(getattr(judgment, "trace", None), dict):
        return "trace must be an object"
    relation = getattr(judgment, "relation", None)
    if not isinstance(relation, Relation):
        return "relation must be a Relation enum value"

    confidence = getattr(judgment, "confidence", None)
    if (
        isinstance(confidence, bool)
        or not isinstance(confidence, (int, float))
        or not 0 <= confidence <= 1
    ):
        return "confidence must be a number from 0 to 1"

    reason = getattr(judgment, "reason", None)
    if not isinstance(reason, str) or not reason.strip():
        return "reason must be a non-empty string"

    evidence_line = getattr(judgment, "evidence_line", None)
    evidence_quote = getattr(judgment, "evidence_quote", None)
    if relation == Relation.IRRELEVANT:
        if evidence_line is not None or evidence_quote is not None:
            return "IRRELEVANT must not include evidence"
        return None

    if isinstance(evidence_line, bool) or not isinstance(evidence_line, int):
        return "non-IRRELEVANT judgments require an integer evidence line"
    if not isinstance(evidence_quote, str) or not evidence_quote:
        return "non-IRRELEVANT judgments require a non-empty evidence quote"
    if "\n" in evidence_quote or "\r" in evidence_quote:
        return "evidence quote must be a single line"
    return None
