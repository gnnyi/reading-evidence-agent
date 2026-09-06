from __future__ import annotations

from pathlib import Path
from typing import Any

from reading_evidence.abstention import DIRECTIONAL_CONFIDENCE_THRESHOLD, abstention_decision
from reading_evidence.citation import citation_for, citation_for_evidence, validate_evidence_quote
from reading_evidence.ingest import load_index
from reading_evidence.judge import JudgeError, LexicalJudge, RelationJudge
from reading_evidence.judge.base import judgment_contract_error
from reading_evidence.models import Answer, EvidenceItem, Relation, RelationJudgment
from reading_evidence.query import decompose_query
from reading_evidence.retrieval import DEFAULT_RRF_K, DEFAULT_TOP_K_PER_QUERY, retrieve
from reading_evidence.text import excerpt
from reading_evidence.trace import build_trace, summarize_judge_traces


DEFAULT_MAX_PER_RELATION = 1


def _evidence_item(
    question: str,
    candidate,
    judgment: RelationJudgment,
    *,
    use_exact_evidence: bool,
) -> EvidenceItem:
    if use_exact_evidence:
        item_excerpt = judgment.evidence_quote
        citation = citation_for_evidence(
            candidate.note,
            judgment.evidence_line,
            judgment.evidence_quote,
        )
    else:
        item_excerpt = excerpt(candidate.note.text)
        citation = citation_for(candidate.note, question, judgment.relation)
    return EvidenceItem(
        note_id=candidate.note.note_id,
        title=candidate.note.title,
        excerpt=item_excerpt,
        relation=judgment.relation,
        confidence=round(judgment.confidence, 3),
        citation=citation,
        reason=judgment.reason,
    )


def _config(max_per_relation: int, judge: RelationJudge) -> dict[str, Any]:
    return {
        "top_k_per_query": DEFAULT_TOP_K_PER_QUERY,
        "rrf_k": DEFAULT_RRF_K,
        "max_per_relation": max_per_relation,
        "abstention_confidence_threshold": DIRECTIONAL_CONFIDENCE_THRESHOLD,
        "relation_classifier": judge.judge_id,
    }


def _judge_trace(
    judge: RelationJudge,
    traces: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if traces:
        return summarize_judge_traces(traces)
    empty = judge.empty_trace()
    return summarize_judge_traces([empty]) if empty else None


def analyze(
    question: str,
    index_path: Path,
    *,
    max_per_relation: int = DEFAULT_MAX_PER_RELATION,
    judge: RelationJudge | None = None,
) -> tuple[Answer, list[EvidenceItem]]:
    """Run the pipeline once and expose uncapped classifications for Eval."""
    if max_per_relation < 1:
        raise ValueError("max_per_relation must be at least 1")

    notes, metadata = load_index(index_path)
    active_judge = judge or LexicalJudge()
    plan = decompose_query(question)
    candidates = retrieve(notes, plan)
    classified: list[EvidenceItem] = []
    selected: list[EvidenceItem] = []
    candidate_decisions: list[dict[str, Any]] = []
    judge_traces: list[dict[str, Any]] = []
    relation_counts: dict[Relation, int] = {}

    for candidate_index, candidate in enumerate(candidates):
        try:
            judgment = active_judge.judge(question, candidate)
            contract_error = judgment_contract_error(judgment)
            error_code = "invalid_judgment_schema"
            if (
                contract_error is None
                and active_judge.citation_mode == "exact_quote"
                and judgment.relation != Relation.IRRELEVANT
            ):
                valid, reason = validate_evidence_quote(
                    candidate.note, judgment.evidence_line, judgment.evidence_quote,
                )
                if not valid:
                    contract_error = reason
                    error_code = "invalid_evidence_quote"
            if contract_error is not None:
                raw_trace = getattr(judgment, "trace", {})
                safe_trace = dict(raw_trace) if isinstance(raw_trace, dict) else {}
                safe_trace["error"] = {"code": error_code, "message": contract_error}
                raise JudgeError(error_code, contract_error, trace=safe_trace)
        except JudgeError as error:
            for decision in candidate_decisions:
                decision["selected"] = False
                if decision["drop_reason"] != "irrelevant":
                    decision["drop_reason"] = "judge_error_invalidated_answer"
            error_decision = {
                "note_id": candidate.note.note_id,
                "relation": None,
                "confidence": None,
                "reason": None,
                "citation": None,
                "selected": False,
                "drop_reason": "judge_error",
                "judge_trace": error.trace,
            }
            candidate_decisions.append(error_decision)
            for pending in candidates[candidate_index + 1 :]:
                candidate_decisions.append(
                    {
                        "note_id": pending.note.note_id,
                        "relation": None,
                        "confidence": None,
                        "reason": None,
                        "citation": None,
                        "selected": False,
                        "drop_reason": "judge_error_not_evaluated",
                    }
                )
            judge_traces.append(error.trace)
            trace = build_trace(
                plan,
                candidates,
                [],
                candidate_decisions=candidate_decisions,
                corpus_sha256=metadata.get("corpus_sha256"),
                config=_config(max_per_relation, active_judge),
                judge_trace=_judge_trace(active_judge, judge_traces),
            )
            return (
                Answer(
                    question=question,
                    evidence=[],
                    abstained=True,
                    abstention_reason="Evidence judgment failed; no evidence decision was produced",
                    trace=trace,
                    status="JUDGE_ERROR",
                ),
                [],
            )

        relation = judgment.relation
        confidence = judgment.confidence
        reason = judgment.reason
        rounded_confidence = round(confidence, 3)
        if judgment.trace:
            judge_traces.append(judgment.trace)
        item: EvidenceItem | None = None
        selected_for_output = False
        drop_reason: str | None = None

        if relation == Relation.IRRELEVANT:
            drop_reason = "irrelevant"
        else:
            item = _evidence_item(
                question,
                candidate,
                judgment,
                use_exact_evidence=active_judge.citation_mode == "exact_quote",
            )
            classified.append(item)
            if relation_counts.get(relation, 0) >= max_per_relation:
                drop_reason = "max_per_relation"
            else:
                selected.append(item)
                selected_for_output = True
                relation_counts[relation] = relation_counts.get(relation, 0) + 1

        decision = {
            "note_id": candidate.note.note_id,
            "relation": relation.value,
            "confidence": rounded_confidence,
            "reason": reason,
            "citation": item.citation if item is not None else None,
            "selected": selected_for_output,
            "drop_reason": drop_reason,
        }
        if judgment.trace:
            decision["judge_trace"] = judgment.trace
        candidate_decisions.append(decision)

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
        config=_config(max_per_relation, active_judge),
        judge_trace=_judge_trace(active_judge, judge_traces),
    )
    return (
        Answer(
            question=question,
            evidence=selected,
            abstained=abstained,
            abstention_reason=reason,
            trace=trace,
            status="ABSTAINED" if abstained else "OK",
        ),
        classified,
    )


def ask(
    question: str,
    index_path: Path,
    *,
    max_per_relation: int = DEFAULT_MAX_PER_RELATION,
    judge: RelationJudge | None = None,
) -> Answer:
    answer, _ = analyze(
        question,
        index_path,
        max_per_relation=max_per_relation,
        judge=judge,
    )
    return answer
