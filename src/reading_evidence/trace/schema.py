from __future__ import annotations

from typing import Any

from reading_evidence.models import EvidenceItem, QueryPlan, RetrievalCandidate


TRACE_SCHEMA_VERSION = 2


def build_trace(
    plan: QueryPlan,
    candidates: list[RetrievalCandidate],
    decisions: list[EvidenceItem],
    *,
    candidate_decisions: list[dict[str, Any]] | None = None,
    config: dict[str, Any] | None = None,
    corpus_sha256: str | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": TRACE_SCHEMA_VERSION,
        "corpus_sha256": corpus_sha256,
        "config": config or {},
        "rewritten_queries": {
            "original": plan.original,
            "core": plan.core,
            "support": plan.support,
            "counter": plan.counter,
        },
        "candidates_retrieved": sum(len(item.matched_queries) for item in candidates),
        "candidates_deduplicated": len(candidates),
        "candidates": [
            {
                "note_id": candidate.note.note_id,
                "rrf_score": round(candidate.rrf_score, 12),
                "best_lexical_score": round(candidate.best_lexical_score, 6),
                "matched_queries": candidate.matched_queries,
            }
            for candidate in candidates
        ],
        "candidate_decisions": candidate_decisions or [],
        # Backward-compatible selected-only view used by the existing CLI summary.
        "relation_decisions": [
            {
                "note_id": item.note_id,
                "relation": item.relation.value,
                "confidence": item.confidence,
                "reason": item.reason,
            }
            for item in decisions
        ],
    }
