from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from reading_evidence.agent import ask


def run_eval(index_path: Path, questions_path: Path, dataset_path: Path) -> dict[str, Any]:
    questions = {item["id"]: item["question"] for item in json.loads(questions_path.read_text())}
    gold = json.loads(dataset_path.read_text())
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
