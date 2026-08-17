from __future__ import annotations

from pathlib import Path

from reading_evidence.abstention import abstention_decision
from reading_evidence.citation import citation_for
from reading_evidence.ingest import load_index
from reading_evidence.models import Answer, EvidenceItem, Relation
from reading_evidence.query import decompose_query
from reading_evidence.relation import classify_candidate
from reading_evidence.retrieval import retrieve
from reading_evidence.text import excerpt
from reading_evidence.trace import build_trace


def ask(
    question: str,
    index_path: Path,
    *,
    max_per_relation: int = 1,
) -> Answer:
    notes, _ = load_index(index_path)
    plan = decompose_query(question)
    candidates = retrieve(notes, plan)
    decisions: list[EvidenceItem] = []
    relation_counts: dict[Relation, int] = {}
    for candidate in candidates:
        relation, confidence, reason = classify_candidate(question, candidate)
        if relation == Relation.IRRELEVANT:
            continue
        if relation_counts.get(relation, 0) >= max_per_relation:
            continue
        decisions.append(
            EvidenceItem(
                note_id=candidate.note.note_id,
                title=candidate.note.title,
                excerpt=excerpt(candidate.note.text),
                relation=relation,
                confidence=round(confidence, 3),
                citation=citation_for(candidate.note),
                reason=reason,
            )
        )
        relation_counts[relation] = relation_counts.get(relation, 0) + 1

    abstained, reason = abstention_decision(decisions)
    return Answer(
        question=question,
        evidence=decisions,
        abstained=abstained,
        abstention_reason=reason,
        trace=build_trace(plan, candidates, decisions),
    )
