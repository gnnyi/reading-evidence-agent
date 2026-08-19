from __future__ import annotations

from pathlib import Path
from typing import Any

from reading_evidence.abstention import DIRECTIONAL_CONFIDENCE_THRESHOLD, abstention_decision
from reading_evidence.citation import citation_for
from reading_evidence.ingest import load_index
from reading_evidence.models import Answer, EvidenceItem, Relation
from reading_evidence.query import decompose_query
from reading_evidence.relation import classify_candidate
from reading_evidence.retrieval import DEFAULT_RRF_K, DEFAULT_TOP_K_PER_QUERY, retrieve
from reading_evidence.text import excerpt
from reading_evidence.trace import build_trace


DEFAULT_MAX_PER_RELATION = 1
RELATION_CLASSIFIER_ID = "lexical-polarity-v0.1"


def _evidence_item(question: str, candidate, relation: Relation, confidence: float, reason: str) -> EvidenceItem:
    return EvidenceItem(
        note_id=candidate.note.note_id,
        title=candidate.note.title,
        excerpt=excerpt(candidate.note.text),
        relation=relation,
        confidence=round(confidence, 3),
        citation=citation_for(candidate.note, question, relation),
        reason=reason,
    )


def analyze(
    question: str,
    index_path: Path,
    *,
    max_per_relation: int = DEFAULT_MAX_PER_RELATION,
) -> tuple[Answer, list[EvidenceItem]]:
    """Run the deterministic pipeline once and expose uncapped classifications for Eval."""
    if max_per_relation < 1:
        raise ValueError("max_per_relation must be at least 1")

    notes, metadata = load_index(index_path)
    plan = decompose_query(question)
    candidates = retrieve(notes, plan)
    classified: list[EvidenceItem] = []
    selected: list[EvidenceItem] = []
    candidate_decisions: list[dict[str, Any]] = []
    relation_counts: dict[Relation, int] = {}

    for candidate in candidates:
        relation, confidence, reason = classify_candidate(question, candidate)
        rounded_confidence = round(confidence, 3)
        item: EvidenceItem | None = None
        selected_for_output = False
        drop_reason: str | None = None

        if relation == Relation.IRRELEVANT:
            drop_reason = "irrelevant"
        else:
            item = _evidence_item(question, candidate, relation, confidence, reason)
            classified.append(item)
            if relation_counts.get(relation, 0) >= max_per_relation:
                drop_reason = "max_per_relation"
            else:
                selected.append(item)
                selected_for_output = True
                relation_counts[relation] = relation_counts.get(relation, 0) + 1

        candidate_decisions.append(
            {
                "note_id": candidate.note.note_id,
                "relation": relation.value,
                "confidence": rounded_confidence,
                "reason": reason,
                "citation": item.citation if item is not None else None,
                "selected": selected_for_output,
                "drop_reason": drop_reason,
            }
        )

    # Abstention is a claim-level policy, so it uses every classified candidate rather
    # than the presentation cap. With the default cap this preserves V0.1 output while
    # preventing presentation policy from becoming part of the Eval contract.
    abstained, reason = abstention_decision(classified)
    trace = build_trace(
        plan,
        candidates,
        selected,
        candidate_decisions=candidate_decisions,
        corpus_sha256=metadata.get("corpus_sha256"),
        config={
            "top_k_per_query": DEFAULT_TOP_K_PER_QUERY,
            "rrf_k": DEFAULT_RRF_K,
            "max_per_relation": max_per_relation,
            "abstention_confidence_threshold": DIRECTIONAL_CONFIDENCE_THRESHOLD,
            "relation_classifier": RELATION_CLASSIFIER_ID,
        },
    )
    return (
        Answer(
            question=question,
            evidence=selected,
            abstained=abstained,
            abstention_reason=reason,
            trace=trace,
        ),
        classified,
    )


def ask(
    question: str,
    index_path: Path,
    *,
    max_per_relation: int = DEFAULT_MAX_PER_RELATION,
) -> Answer:
    answer, _ = analyze(question, index_path, max_per_relation=max_per_relation)
    return answer
