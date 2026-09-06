from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from reading_evidence.citation import validate_evidence_quote
from reading_evidence.judge import JudgeError, RelationJudge
from reading_evidence.judge.base import judgment_contract_error
from reading_evidence.models import Note, Relation, RetrievalCandidate


@dataclass(frozen=True)
class JudgeEvalCase:
    case_id: str
    question: str
    note: Note
    expected_relation: Relation
    expected_evidence_line: int | None
    expected_evidence_quote: str | None
    tags: tuple[str, ...]


def _require_non_empty_string(value: Any, field: str, position: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Judge Eval item {position} requires a non-empty string '{field}'")
    return value


def _load_case(item: Any, position: int) -> JudgeEvalCase:
    if not isinstance(item, dict):
        raise ValueError(f"Judge Eval item {position} must be an object")

    case_id = _require_non_empty_string(item.get("id"), "id", position)
    question = _require_non_empty_string(item.get("question"), "question", position)
    note_value = item.get("note")
    if not isinstance(note_value, dict):
        raise ValueError(f"Judge Eval item {position} 'note' must be an object")

    note_id = _require_non_empty_string(note_value.get("note_id"), "note.note_id", position)
    title = _require_non_empty_string(note_value.get("title"), "note.title", position)
    text = _require_non_empty_string(note_value.get("text"), "note.text", position)
    source = _require_non_empty_string(note_value.get("source"), "note.source", position)
    if Path(source).is_absolute():
        raise ValueError(f"Judge Eval item {position} 'note.source' must be relative")
    line_start = note_value.get("line_start")
    if isinstance(line_start, bool) or not isinstance(line_start, int) or line_start < 1:
        raise ValueError(f"Judge Eval item {position} 'note.line_start' must be an integer >= 1")

    relation_value = item.get("expected_relation")
    try:
        expected_relation = Relation(relation_value)
    except (TypeError, ValueError) as error:
        allowed = ", ".join(relation.value for relation in Relation)
        raise ValueError(
            f"Judge Eval item {position} 'expected_relation' must be one of {allowed}"
        ) from error

    expected_line = item.get("expected_evidence_line")
    expected_quote = item.get("expected_evidence_quote")
    if expected_relation == Relation.IRRELEVANT:
        if expected_line is not None or expected_quote is not None:
            raise ValueError(
                f"Judge Eval item {position} IRRELEVANT evidence line and quote must be null"
            )
    else:
        if isinstance(expected_line, bool) or not isinstance(expected_line, int):
            raise ValueError(
                f"Judge Eval item {position} requires integer 'expected_evidence_line'"
            )
        if not isinstance(expected_quote, str) or not expected_quote.strip():
            raise ValueError(
                f"Judge Eval item {position} requires non-empty 'expected_evidence_quote'"
            )
        lines = text.splitlines()
        line_index = expected_line - line_start
        if line_index < 0 or line_index >= len(lines):
            raise ValueError(
                f"Judge Eval item {position} expected evidence line is outside note text"
            )
        if expected_quote not in lines[line_index]:
            raise ValueError(
                f"Judge Eval item {position} expected evidence quote is not on the expected line"
            )

    tags_value = item.get("tags")
    if not isinstance(tags_value, list) or any(
        not isinstance(tag, str) or not tag.strip() for tag in tags_value
    ):
        raise ValueError(f"Judge Eval item {position} 'tags' must be an array of non-empty strings")
    if len(set(tags_value)) != len(tags_value):
        raise ValueError(f"Judge Eval item {position} 'tags' must not contain duplicates")

    return JudgeEvalCase(
        case_id=case_id,
        question=question,
        note=Note(
            note_id=note_id,
            title=title,
            text=text,
            source=source,
            line_start=line_start,
        ),
        expected_relation=expected_relation,
        expected_evidence_line=expected_line,
        expected_evidence_quote=expected_quote,
        tags=tuple(tags_value),
    )


def load_judge_eval_dataset(path: Path) -> list[JudgeEvalCase]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("Judge Eval dataset must contain a JSON array")
    if not value:
        raise ValueError("Judge Eval dataset must contain at least one case")

    cases = [_load_case(item, position) for position, item in enumerate(value, start=1)]
    ids = [case.case_id for case in cases]
    if len(set(ids)) != len(ids):
        duplicate = next(case_id for case_id in ids if ids.count(case_id) > 1)
        raise ValueError(f"Judge Eval dataset contains duplicate id: {duplicate}")
    return cases


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _rounded(value: float | None) -> float | None:
    return round(value, 4) if value is not None else None


def _percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = min(len(ordered) - 1, int((len(ordered) - 1) * fraction))
    return round(ordered[index], 3)


def _citation_matches_source(
    case: JudgeEvalCase,
    judgment: Any,
) -> bool | None:
    """Measure quote fidelity independently of relation correctness.

    IRRELEVANT outputs have no citation, so they are outside this metric's
    denominator. Their null-field contract is covered by schema_valid_rate.
    """
    if judgment.relation == Relation.IRRELEVANT:
        return None
    valid, _ = validate_evidence_quote(
        case.note,
        judgment.evidence_line,
        judgment.evidence_quote,
    )
    return valid


def _gold_evidence_matches(
    case: JudgeEvalCase,
    judgment: Any,
) -> bool | None:
    """Check the expected evidence span without conflating source fidelity."""
    if case.expected_relation == Relation.IRRELEVANT:
        return None
    if judgment.relation == Relation.IRRELEVANT:
        return False
    if judgment.evidence_line != case.expected_evidence_line:
        return False
    if not isinstance(judgment.evidence_quote, str):
        return False
    if case.expected_evidence_quote not in judgment.evidence_quote:
        return False
    valid, _ = validate_evidence_quote(
        case.note,
        judgment.evidence_line,
        judgment.evidence_quote,
    )
    return valid



def run_judge_eval(dataset_path: Path, judge: RelationJudge) -> dict[str, Any]:
    cases = load_judge_eval_dataset(dataset_path)
    case_results: list[dict[str, Any]] = []
    counts = {
        relation: {"tp": 0, "fp": 0, "fn": 0}
        for relation in Relation
    }
    correct = 0
    schema_valid_count = 0
    citation_valid_count = 0
    citation_output_count = 0
    gold_evidence_match_count = 0
    gold_evidence_case_count = sum(
        case.expected_relation != Relation.IRRELEVANT for case in cases
    )
    errors = 0
    latencies: list[float] = []
    token_totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    token_observations = {key: 0 for key in token_totals}
    request_count = 0
    retry_count = 0

    for case in cases:
        candidate = RetrievalCandidate(
            note=case.note,
            rrf_score=0.0,
            best_lexical_score=0.0,
        )
        started = time.perf_counter()
        try:
            judgment = judge.judge(case.question, candidate)
            contract_error = judgment_contract_error(judgment)
            if contract_error is not None:
                trace = getattr(judgment, "trace", {})
                raise JudgeError(
                    "invalid_judgment_schema",
                    f"Judge returned an invalid judgment: {contract_error}",
                    trace=trace if isinstance(trace, dict) else {},
                )
        except JudgeError as error:
            error_trace = getattr(error, "trace", None)
            elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
            if isinstance(error_trace, dict):
                traced_latency = error_trace.get("latency_ms")
                if (
                    isinstance(traced_latency, (int, float))
                    and not isinstance(traced_latency, bool)
                ):
                    elapsed_ms = round(float(traced_latency), 3)
                tokens = error_trace.get("tokens")
                if isinstance(tokens, dict):
                    for key in token_totals:
                        value = tokens.get(key)
                        if (
                            isinstance(value, int)
                            and not isinstance(value, bool)
                            and value >= 0
                        ):
                            token_totals[key] += value
                            token_observations[key] += 1
                error_requests = error_trace.get("request_count")
                if (
                    isinstance(error_requests, int)
                    and not isinstance(error_requests, bool)
                    and error_requests >= 0
                ):
                    request_count += error_requests
                error_retries = error_trace.get("retry_count")
                if (
                    isinstance(error_retries, int)
                    and not isinstance(error_retries, bool)
                    and error_retries >= 0
                ):
                    retry_count += error_retries
            errors += 1
            latencies.append(elapsed_ms)
            counts[case.expected_relation]["fn"] += 1
            case_results.append(
                {
                    "id": case.case_id,
                    "tags": list(case.tags),
                    "status": "JUDGE_ERROR",
                    "expected_relation": case.expected_relation.value,
                    "predicted_relation": None,
                    "relation_correct": False,
                    "schema_valid": False,
                    "citation_integrity": None,
                    "gold_evidence_match": (
                        False
                        if case.expected_relation != Relation.IRRELEVANT
                        else None
                    ),
                    "expected_evidence_line": case.expected_evidence_line,
                    "predicted_evidence_line": None,
                    "expected_evidence_quote": case.expected_evidence_quote,
                    "predicted_evidence_quote": None,
                    "latency_ms": elapsed_ms,
                    "trace": error_trace,
                    "error": str(error),
                }
            )
            continue

        elapsed_ms = judgment.trace.get("latency_ms")
        if not isinstance(elapsed_ms, (int, float)) or isinstance(elapsed_ms, bool):
            elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
        latencies.append(float(elapsed_ms))

        trace = judgment.trace
        tokens = trace.get("tokens")
        if isinstance(tokens, dict):
            for key in token_totals:
                value = tokens.get(key)
                if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                    token_totals[key] += value
                    token_observations[key] += 1
        for key, accumulator in (("request_count", "request"), ("retry_count", "retry")):
            value = trace.get(key)
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                if accumulator == "request":
                    request_count += value
                else:
                    retry_count += value

        schema_valid = isinstance(judgment.relation, Relation)
        schema_valid_count += int(schema_valid)
        citation_valid = _citation_matches_source(case, judgment)
        if citation_valid is not None:
            citation_output_count += 1
            citation_valid_count += int(citation_valid)
        gold_evidence_match = _gold_evidence_matches(case, judgment)
        if gold_evidence_match:
            gold_evidence_match_count += 1
        relation_correct = judgment.relation == case.expected_relation
        correct += int(relation_correct)

        for relation in Relation:
            predicted = judgment.relation == relation
            expected = case.expected_relation == relation
            counts[relation]["tp"] += int(predicted and expected)
            counts[relation]["fp"] += int(predicted and not expected)
            counts[relation]["fn"] += int(not predicted and expected)

        case_results.append(
            {
                "id": case.case_id,
                "tags": list(case.tags),
                "status": "OK",
                "expected_relation": case.expected_relation.value,
                "predicted_relation": judgment.relation.value,
                "relation_correct": relation_correct,
                "schema_valid": schema_valid,
                "citation_integrity": citation_valid,
                "gold_evidence_match": gold_evidence_match,
                "expected_evidence_line": case.expected_evidence_line,
                "predicted_evidence_line": judgment.evidence_line,
                "expected_evidence_quote": case.expected_evidence_quote,
                "predicted_evidence_quote": judgment.evidence_quote,
                "confidence": judgment.confidence,
                "reason": judgment.reason,
                "latency_ms": round(float(elapsed_ms), 3),
                "trace": trace,
                "error": None,
            }
        )

    by_class: dict[str, dict[str, int | float | None]] = {}
    class_f1: list[float] = []
    for relation in Relation:
        relation_counts = counts[relation]
        precision = _ratio(relation_counts["tp"], relation_counts["tp"] + relation_counts["fp"])
        recall = _ratio(relation_counts["tp"], relation_counts["tp"] + relation_counts["fn"])
        f1_denominator = 2 * relation_counts["tp"] + relation_counts["fp"] + relation_counts["fn"]
        f1 = (
            2 * relation_counts["tp"] / f1_denominator
            if f1_denominator
            else None
        )
        if f1 is not None:
            class_f1.append(f1)
        by_class[relation.value] = {
            **relation_counts,
            "precision": _rounded(precision),
            "recall": _rounded(recall),
            "f1": _rounded(f1),
        }

    injection_cases = [
        result for result in case_results if "prompt_injection" in result["tags"]
    ]
    injection_correct = sum(result["relation_correct"] for result in injection_cases)
    counter = by_class[Relation.COUNTER_EVIDENCE.value]
    case_count = len(cases)
    latency_total = sum(latencies)
    return {
        "status": "JUDGE_ERROR" if errors else "OK",
        "dataset": dataset_path.name,
        "dataset_sha256": hashlib.sha256(dataset_path.read_bytes()).hexdigest(),
        "case_count": case_count,
        "error_count": errors,
        "relation_accuracy": _rounded(_ratio(correct, case_count)),
        "relation_macro_f1": _rounded(_ratio(sum(class_f1), len(class_f1))),
        "relation_by_class": by_class,
        "counter_recall": counter["recall"],
        "prompt_injection_case_count": len(injection_cases),
        "prompt_injection_accuracy": _rounded(
            _ratio(injection_correct, len(injection_cases))
        ),
        "schema_valid_rate": _rounded(_ratio(schema_valid_count, case_count)),
        "citation_integrity": _rounded(
            _ratio(citation_valid_count, citation_output_count)
        ),
        "citation_output_count": citation_output_count,
        "gold_evidence_match_rate": _rounded(
            _ratio(gold_evidence_match_count, gold_evidence_case_count)
        ),
        "gold_evidence_case_count": gold_evidence_case_count,
        "aggregate": {
            "latency_ms": {
                "count": len(latencies),
                "total": round(latency_total, 3),
                "mean": round(latency_total / len(latencies), 3) if latencies else None,
                "p50": _percentile(latencies, 0.5),
                "p95": _percentile(latencies, 0.95),
                "min": round(min(latencies), 3) if latencies else None,
                "max": round(max(latencies), 3) if latencies else None,
            },
            "tokens": {
                key: {
                    "total": token_totals[key],
                    "observed_case_count": token_observations[key],
                }
                for key in token_totals
            },
            "request_count": request_count,
            "retry_count": retry_count,
        },
        "cases": case_results,
    }
