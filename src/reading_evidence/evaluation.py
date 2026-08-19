from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reading_evidence.abstention import abstention_decision
from reading_evidence.agent import analyze
from reading_evidence.citation import validate_citation
from reading_evidence.ingest import load_index
from reading_evidence.models import Relation


EVALUATED_RELATIONS = (
    Relation.SUPPORT,
    Relation.COUNTER_EVIDENCE,
    Relation.RELATED,
)


def _load_questions(path: Path) -> dict[str, str]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("Questions file must contain a JSON array")
    questions: dict[str, str] = {}
    for position, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Questions item {position} must be an object")
        question_id = item.get("id")
        question = item.get("question")
        if not isinstance(question_id, str) or not question_id.strip():
            raise ValueError(f"Questions item {position} requires a non-empty string 'id'")
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"Questions item {position} requires a non-empty string 'question'")
        if question_id in questions:
            raise ValueError(f"Questions contains duplicate id: {question_id}")
        questions[question_id] = question
    return questions


def _load_gold(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError("Gold file must contain a JSON array")
    if not value:
        raise ValueError("Gold file must contain at least one case")

    allowed_relations = {relation.value for relation in EVALUATED_RELATIONS}
    seen_question_ids: set[str] = set()
    for position, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Gold item {position} must be an object")
        question_id = item.get("question_id")
        if not isinstance(question_id, str) or not question_id.strip():
            raise ValueError(f"Gold item {position} requires a non-empty string 'question_id'")
        if question_id in seen_question_ids:
            raise ValueError(f"Gold contains duplicate question_id: {question_id}")
        seen_question_ids.add(question_id)

        expected = item.get("expected_relations", {})
        if not isinstance(expected, dict):
            raise ValueError(f"Gold item {position} 'expected_relations' must be an object")
        for note_id, relation in expected.items():
            if not isinstance(note_id, str) or not note_id:
                raise ValueError(f"Gold item {position} contains an invalid note id")
            if relation not in allowed_relations:
                raise ValueError(
                    f"Gold item {position} relation for '{note_id}' must be one of "
                    f"{', '.join(sorted(allowed_relations))}"
                )
        if "expected_abstain" not in item or not isinstance(item["expected_abstain"], bool):
            raise ValueError(f"Gold item {position} 'expected_abstain' must be true or false")
    return value


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _rounded(value: float | None) -> float | None:
    return round(value, 4) if value is not None else None


def _f1(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None:
        return None
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def _class_metrics(tp: int, fp: int, fn: int) -> dict[str, int | float | None]:
    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "predicted_count": tp + fp,
        "gold_count": tp + fn,
        "precision": _rounded(precision),
        "recall": _rounded(recall),
        "f1": _rounded(_f1(precision, recall)),
    }


def _mean_defined(values: list[float | None]) -> float | None:
    defined = [value for value in values if value is not None]
    return sum(defined) / len(defined) if defined else None


def run_eval(index_path: Path, questions_path: Path, dataset_path: Path) -> dict[str, Any]:
    questions = _load_questions(questions_path)
    gold = _load_gold(dataset_path)
    notes, _ = load_index(index_path)
    notes_by_id = {note.note_id: note for note in notes}

    case_results: list[dict[str, Any]] = []
    relation_counts = {
        relation: {"tp": 0, "fp": 0, "fn": 0} for relation in EVALUATED_RELATIONS
    }
    true_positive = false_positive = false_negative = 0
    abstain_tp = abstain_fp = abstain_tn = abstain_fn = 0
    citation_items = cited_items = valid_citations = 0

    for case in gold:
        question_id = case["question_id"]
        if question_id not in questions:
            raise ValueError(f"Gold references unknown question: {question_id}")
        question = questions[question_id]
        answer, classified_evidence = analyze(question, index_path)

        predicted = {item.note_id: item.relation.value for item in classified_evidence}
        presented = {item.note_id: item.relation.value for item in answer.evidence}
        expected = case.get("expected_relations", {})
        expected_pairs = set(expected.items())
        predicted_pairs = set(predicted.items())
        presented_pairs = set(presented.items())

        true_positive += len(expected_pairs & predicted_pairs)
        false_positive += len(predicted_pairs - expected_pairs)
        false_negative += len(expected_pairs - predicted_pairs)

        for relation in EVALUATED_RELATIONS:
            relation_value = relation.value
            predicted_ids = {note_id for note_id, value in predicted.items() if value == relation_value}
            expected_ids = {note_id for note_id, value in expected.items() if value == relation_value}
            relation_counts[relation]["tp"] += len(predicted_ids & expected_ids)
            relation_counts[relation]["fp"] += len(predicted_ids - expected_ids)
            relation_counts[relation]["fn"] += len(expected_ids - predicted_ids)

        # Abstention is evaluated from uncapped classifications, independent of presentation policy.
        predicted_abstain, _ = abstention_decision(classified_evidence)
        expected_abstain = case["expected_abstain"]
        if expected_abstain and predicted_abstain:
            abstain_tp += 1
        elif expected_abstain and not predicted_abstain:
            abstain_fn += 1
        elif not expected_abstain and predicted_abstain:
            abstain_fp += 1
        else:
            abstain_tn += 1
        abstain_ok = predicted_abstain == expected_abstain

        case_citation_results: dict[str, dict[str, Any]] = {}
        for item in classified_evidence:
            citation_items += 1
            cited_items += int(bool(item.citation))
            note = notes_by_id.get(item.note_id)
            if note is None:
                valid, citation_reason = False, "citation_note_missing_from_index"
            else:
                valid, citation_reason = validate_citation(
                    note, question, item.relation, item.citation
                )
            valid_citations += int(valid)
            case_citation_results[item.note_id] = {
                "citation": item.citation,
                "valid": valid,
                "reason": citation_reason,
            }

        case_results.append(
            {
                "question_id": question_id,
                "relations_exact": predicted_pairs == expected_pairs,
                "presentation_relations_exact": presented_pairs == expected_pairs,
                "abstention_correct": abstain_ok,
                "predicted_relations": predicted,
                "presented_relations": presented,
                "expected_relations": expected,
                "citations": case_citation_results,
            }
        )

    precision = _ratio(true_positive, true_positive + false_positive)
    recall = _ratio(true_positive, true_positive + false_negative)
    f1 = _f1(precision, recall)
    by_class = {
        relation.value: _class_metrics(**relation_counts[relation])
        for relation in EVALUATED_RELATIONS
    }
    raw_class_precision = {
        relation: _ratio(
            relation_counts[relation]["tp"],
            relation_counts[relation]["tp"] + relation_counts[relation]["fp"],
        )
        for relation in EVALUATED_RELATIONS
    }
    raw_class_recall = {
        relation: _ratio(
            relation_counts[relation]["tp"],
            relation_counts[relation]["tp"] + relation_counts[relation]["fn"],
        )
        for relation in EVALUATED_RELATIONS
    }
    raw_class_f1 = {
        relation: _f1(raw_class_precision[relation], raw_class_recall[relation])
        for relation in EVALUATED_RELATIONS
    }
    macro_precision = _mean_defined(list(raw_class_precision.values()))
    macro_recall = _mean_defined(list(raw_class_recall.values()))
    macro_f1 = _mean_defined(list(raw_class_f1.values()))

    abstention_precision = _ratio(abstain_tp, abstain_tp + abstain_fp)
    abstention_recall = _ratio(abstain_tp, abstain_tp + abstain_fn)
    abstention_specificity = _ratio(abstain_tn, abstain_tn + abstain_fp)
    abstention_balanced_accuracy = (
        (abstention_recall + abstention_specificity) / 2
        if abstention_recall is not None and abstention_specificity is not None
        else None
    )

    counter = by_class[Relation.COUNTER_EVIDENCE.value]
    support = by_class[Relation.SUPPORT.value]
    related = by_class[Relation.RELATED.value]
    case_count = len(case_results)
    return {
        "case_count": case_count,
        "relation_precision": _rounded(precision),
        "relation_recall": _rounded(recall),
        "relation_f1": _rounded(f1),
        "relation_macro_precision": _rounded(macro_precision),
        "relation_macro_recall": _rounded(macro_recall),
        "relation_macro_f1": _rounded(macro_f1),
        "relation_by_class": by_class,
        "false_counter_rate": _rounded(
            None
            if raw_class_precision[Relation.COUNTER_EVIDENCE] is None
            else 1 - raw_class_precision[Relation.COUNTER_EVIDENCE]
        ),
        "counter_precision": counter["precision"],
        "counter_recall": counter["recall"],
        "false_support_rate": _rounded(
            None
            if raw_class_precision[Relation.SUPPORT] is None
            else 1 - raw_class_precision[Relation.SUPPORT]
        ),
        "support_precision": support["precision"],
        "support_recall": support["recall"],
        "related_contamination_rate": _rounded(
            None
            if raw_class_precision[Relation.RELATED] is None
            else 1 - raw_class_precision[Relation.RELATED]
        ),
        "related_precision": related["precision"],
        "related_recall": related["recall"],
        "abstention_accuracy": round((abstain_tp + abstain_tn) / case_count, 4),
        "abstention_precision": _rounded(abstention_precision),
        "abstention_recall": _rounded(abstention_recall),
        "abstention_specificity": _rounded(abstention_specificity),
        "abstention_balanced_accuracy": _rounded(abstention_balanced_accuracy),
        "expected_abstain_count": abstain_tp + abstain_fn,
        "predicted_abstain_count": abstain_tp + abstain_fp,
        "citation_coverage": _rounded(_ratio(cited_items, citation_items)),
        "citation_integrity": _rounded(_ratio(valid_citations, citation_items)),
        "exact_case_rate": round(
            sum(r["relations_exact"] and r["abstention_correct"] for r in case_results) / case_count,
            4,
        ),
        "presentation_exact_case_rate": round(
            sum(
                r["presentation_relations_exact"] and r["abstention_correct"]
                for r in case_results
            )
            / case_count,
            4,
        ),
        "cases": case_results,
    }
