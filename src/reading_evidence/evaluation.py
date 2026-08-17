from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reading_evidence.agent import ask
from reading_evidence.models import Relation


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
    allowed_relations = {relation.value for relation in Relation}
    for position, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Gold item {position} must be an object")
        question_id = item.get("question_id")
        if not isinstance(question_id, str) or not question_id.strip():
            raise ValueError(f"Gold item {position} requires a non-empty string 'question_id'")
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
        if "expected_abstain" in item and not isinstance(item["expected_abstain"], bool):
            raise ValueError(f"Gold item {position} 'expected_abstain' must be true or false")
    return value


def run_eval(index_path: Path, questions_path: Path, dataset_path: Path) -> dict[str, Any]:
    questions = _load_questions(questions_path)
    gold = _load_gold(dataset_path)
    case_results: list[dict[str, Any]] = []
    true_positive = false_positive = false_negative = 0
    abstention_correct = 0
    citation_items = 0
    cited_items = 0

    for case in gold:
        question_id = case["question_id"]
        if question_id not in questions:
            raise ValueError(f"Gold references unknown question: {question_id}")
        answer = ask(questions[question_id], index_path)
        predicted = {item.note_id: item.relation.value for item in answer.evidence}
        expected = case.get("expected_relations", {})
        expected_pairs = set(expected.items())
        predicted_pairs = set(predicted.items())
        true_positive += len(expected_pairs & predicted_pairs)
        false_positive += len(predicted_pairs - expected_pairs)
        false_negative += len(expected_pairs - predicted_pairs)
        abstain_ok = answer.abstained == bool(case.get("expected_abstain", False))
        abstention_correct += int(abstain_ok)
        citation_items += len(answer.evidence)
        cited_items += sum(bool(item.citation) for item in answer.evidence)
        case_results.append(
            {
                "question_id": question_id,
                "relations_exact": predicted_pairs == expected_pairs,
                "abstention_correct": abstain_ok,
                "predicted_relations": predicted,
                "expected_relations": expected,
            }
        )

    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 1.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    case_count = len(case_results)
    return {
        "case_count": case_count,
        "relation_precision": round(precision, 4),
        "relation_recall": round(recall, 4),
        "relation_f1": round(f1, 4),
        "abstention_accuracy": round(abstention_correct / case_count, 4) if case_count else 0.0,
        "citation_coverage": round(cited_items / citation_items, 4) if citation_items else 1.0,
        "exact_case_rate": round(sum(r["relations_exact"] and r["abstention_correct"] for r in case_results) / case_count, 4) if case_count else 0.0,
        "cases": case_results,
    }
