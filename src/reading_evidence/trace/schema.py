from __future__ import annotations

from typing import Any

from reading_evidence.models import EvidenceItem, QueryPlan, RetrievalCandidate


TRACE_SCHEMA_VERSION = 2


def summarize_judge_traces(traces: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Aggregate safe candidate-level telemetry without request content or credentials."""
    if not traces:
        return None

    tokens: dict[str, int | None] = {
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None,
    }
    for trace in traces:
        current = trace.get("tokens") or {}
        for key in tokens:
            value = current.get(key)
            if isinstance(value, int) and not isinstance(value, bool):
                tokens[key] = (tokens[key] or 0) + value

    first = traces[0]
    request_fingerprints = [
        value
        for value in (trace.get("request_fingerprint") for trace in traces)
        if isinstance(value, str)
    ]
    system_fingerprints = sorted(
        {
            value
            for value in (trace.get("system_fingerprint") for trace in traces)
            if isinstance(value, str)
        }
    )
    error = next((trace.get("error") for trace in traces if trace.get("error")), None)
    return {
        "provider": first.get("provider"),
        "model": first.get("model"),
        "prompt_version": first.get("prompt_version"),
        "schema_version": first.get("schema_version"),
        "request_fingerprints": request_fingerprints,
        "system_fingerprints": system_fingerprints,
        "latency_ms": sum(
            value
            for value in (trace.get("latency_ms") for trace in traces)
            if isinstance(value, int) and not isinstance(value, bool)
        ),
        "tokens": tokens,
        "request_count": sum(int(trace.get("request_count", 0)) for trace in traces),
        "retry_count": sum(int(trace.get("retry_count", 0)) for trace in traces),
        "error": error,
    }


def build_trace(
    plan: QueryPlan,
    candidates: list[RetrievalCandidate],
    decisions: list[EvidenceItem],
    *,
    candidate_decisions: list[dict[str, Any]] | None = None,
    config: dict[str, Any] | None = None,
    corpus_sha256: str | None = None,
    judge_trace: dict[str, Any] | None = None,
) -> dict[str, Any]:
    trace = {
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
    if judge_trace is not None:
        trace["judge"] = judge_trace
    return trace
