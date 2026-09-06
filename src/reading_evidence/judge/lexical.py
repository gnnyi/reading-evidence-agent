from __future__ import annotations

from reading_evidence.citation import citation_for
from reading_evidence.models import Relation, RelationJudgment, RetrievalCandidate
from reading_evidence.relation import classify_candidate


class LexicalJudge:
    """Adapter preserving the deterministic V0.1 relation classifier."""

    judge_id = "lexical-polarity-v0.1"
    citation_mode = "lexical"

    def empty_trace(self) -> None:
        return None

    def judge(
        self,
        question: str,
        candidate: RetrievalCandidate,
    ) -> RelationJudgment:
        relation, confidence, reason = classify_candidate(question, candidate)
        evidence_line: int | None = None
        evidence_quote: str | None = None
        if relation != Relation.IRRELEVANT:
            citation = citation_for(candidate.note, question, relation)
            evidence_line = int(citation.rsplit("#L", 1)[1])
            evidence_quote = candidate.note.text.splitlines()[
                evidence_line - candidate.note.line_start
            ]
        return RelationJudgment(
            relation=relation,
            confidence=confidence,
            reason=reason,
            evidence_line=evidence_line,
            evidence_quote=evidence_quote,
        )
