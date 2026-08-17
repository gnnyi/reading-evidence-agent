from __future__ import annotations

from typing import Any

from reading_evidence.models import EvidenceItem, QueryPlan, RetrievalCandidate


TRACE_SCHEMA_VERSION = 1


def build_trace(
    plan: QueryPlan,
    candidates: list[RetrievalCandidate],
    decisions: list[EvidenceItem],
) -> dict[str, Any]:
    return {
        "schema_version": TRACE_SCHEMA_VERSION,
        "rewritten_queries": {
            "original": plan.original,
            "core": plan.core,
            "support": plan.support,
            "counter": plan.counter,
        },
        "candidates_retrieved": sum(len(item.matched_queries) for item in candidates),
        "candidates_deduplicated": len(candidates),
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
