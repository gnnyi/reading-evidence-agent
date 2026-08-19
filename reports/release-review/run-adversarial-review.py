from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from reading_evidence.abstention import abstention_decision
from reading_evidence.agent import analyze
from reading_evidence.citation import validate_citation
from reading_evidence.ingest import ingest_corpus, load_index
from reading_evidence.models import Relation
from reading_evidence.query import decompose_query
from reading_evidence.relation import classify_candidate
from reading_evidence.retrieval import retrieve


ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "reports" / "release-review"
CORPUS_ROOT = REVIEW / "adversarial"
GOLD_PATH = REVIEW / "adversarial-gold.json"
FREEZE_PATH = REVIEW / "adversarial-freeze.json"
OUTPUT_PATH = REVIEW / "adversarial-results.json"
EVALUATED_RELATIONS = (
    Relation.SUPPORT,
    Relation.COUNTER_EVIDENCE,
    Relation.RELATED,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def corpus_aggregate_hash() -> str:
    lines = []
    for path in sorted(value for value in CORPUS_ROOT.rglob("*") if value.is_file()):
        relative = path.relative_to(ROOT).as_posix()
        lines.append(f"{sha256(path)}  {relative}\n")
    return hashlib.sha256("".join(lines).encode()).hexdigest()


def citation_check(item, case: dict, corpus_dir: Path, note, question: str) -> tuple[bool, str]:
    if "#L" not in item.citation:
        return False, "citation_missing_line"
    source, line_text = item.citation.rsplit("#L", 1)
    path = corpus_dir / source
    if not path.is_file():
        return False, "citation_source_missing"
    try:
        line = int(line_text)
    except ValueError:
        return False, "citation_line_invalid"
    raw_lines = path.read_text(encoding="utf-8").splitlines()
    if line < 1 or line > len(raw_lines):
        return False, "citation_line_out_of_range"
    expected = case.get("expected_citations", {}).get(item.note_id)
    if expected is not None and item.citation != expected:
        return False, f"expected_{expected}_got_{item.citation}"
    valid, reason = validate_citation(note, question, item.relation, item.citation)
    if not valid:
        return False, reason
    internal_index = line - note.line_start
    indexed_lines = note.text.splitlines()
    if internal_index < 0 or internal_index >= len(indexed_lines):
        return False, "citation_line_not_in_indexed_note"
    if raw_lines[line - 1].strip() != indexed_lines[internal_index].strip():
        return False, "citation_line_does_not_match_source"
    return True, "ok"


def ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def rounded(value: float | None) -> float | None:
    return round(value, 4) if value is not None else None


def f1(precision: float | None, recall: float | None) -> float | None:
    if precision is None or recall is None:
        return None
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def class_metrics(tp: int, fp: int, fn: int) -> dict:
    precision = ratio(tp, tp + fp)
    recall = ratio(tp, tp + fn)
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "predicted_count": tp + fp,
        "gold_count": tp + fn,
        "precision": rounded(precision),
        "recall": rounded(recall),
        "f1": rounded(f1(precision, recall)),
    }


def main() -> int:
    freeze = json.loads(FREEZE_PATH.read_text())
    if sha256(GOLD_PATH) != freeze["gold_sha256"]:
        raise RuntimeError("Adversarial Gold changed after freeze")
    if corpus_aggregate_hash() != freeze["corpus_hash_of_sorted_sha256_lines"]:
        raise RuntimeError("Adversarial corpus changed after freeze")

    gold = json.loads(GOLD_PATH.read_text())
    if not gold:
        raise RuntimeError("Adversarial Gold must not be empty")

    cases = []
    tp = fp = fn = 0
    relation_counts = {
        relation: {"tp": 0, "fp": 0, "fn": 0} for relation in EVALUATED_RELATIONS
    }
    abstain_tp = abstain_fp = abstain_tn = abstain_fn = 0
    citation_total = citation_present = citation_valid = 0

    for case in gold:
        corpus_dir = CORPUS_ROOT / case["corpus_dir"]
        with tempfile.TemporaryDirectory() as temporary:
            index = Path(temporary) / "index.json"
            ingest_corpus(corpus_dir, index)
            answer, classified_evidence = analyze(case["question"], index)
            notes, _ = load_index(index)
            notes_by_id = {note.note_id: note for note in notes}
            plan = decompose_query(case["question"])
            candidates = retrieve(notes, plan)
            raw = {}
            for candidate in candidates:
                relation, confidence, reason = classify_candidate(case["question"], candidate)
                raw[candidate.note.note_id] = {
                    "relation": relation.value,
                    "confidence": round(confidence, 3),
                    "reason": reason,
                    "rrf_score": candidate.rrf_score,
                    "best_lexical_score": candidate.best_lexical_score,
                }

            predicted = {item.note_id: item.relation.value for item in classified_evidence}
            presented = {item.note_id: item.relation.value for item in answer.evidence}
            expected = case["expected_relations"]
            predicted_pairs = set(predicted.items())
            presented_pairs = set(presented.items())
            expected_pairs = set(expected.items())
            tp += len(predicted_pairs & expected_pairs)
            fp += len(predicted_pairs - expected_pairs)
            fn += len(expected_pairs - predicted_pairs)

            for relation in EVALUATED_RELATIONS:
                value = relation.value
                predicted_ids = {note_id for note_id, label in predicted.items() if label == value}
                expected_ids = {note_id for note_id, label in expected.items() if label == value}
                relation_counts[relation]["tp"] += len(predicted_ids & expected_ids)
                relation_counts[relation]["fp"] += len(predicted_ids - expected_ids)
                relation_counts[relation]["fn"] += len(expected_ids - predicted_ids)

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

            citation_results = {}
            for item in classified_evidence:
                citation_total += 1
                citation_present += int(bool(item.citation))
                note = notes_by_id[item.note_id]
                valid, reason = citation_check(item, case, corpus_dir, note, case["question"])
                citation_valid += int(valid)
                citation_results[item.note_id] = {
                    "citation": item.citation,
                    "valid": valid,
                    "reason": reason,
                }

            failures = []
            for note_id, expected_relation in expected.items():
                predicted_relation = predicted.get(note_id)
                if predicted_relation == expected_relation:
                    continue
                if note_id not in raw:
                    failures.append({"type": "retrieval_miss", "note_id": note_id, "expected": expected_relation})
                elif raw[note_id]["relation"] != expected_relation:
                    subtype = "relation_misclassification"
                    if raw[note_id]["relation"] == "COUNTER_EVIDENCE":
                        subtype = "false_counter"
                    elif raw[note_id]["relation"] == "SUPPORT":
                        subtype = "false_support"
                    elif raw[note_id]["relation"] == "RELATED":
                        subtype = "related_contamination"
                    failures.append({
                        "type": subtype,
                        "note_id": note_id,
                        "expected": expected_relation,
                        "raw_predicted": raw[note_id]["relation"],
                    })
                else:
                    failures.append({"type": "classification_output_miss", "note_id": note_id, "expected": expected_relation})
            for note_id, predicted_relation in predicted.items():
                if note_id not in expected:
                    kind = {
                        "COUNTER_EVIDENCE": "false_counter",
                        "SUPPORT": "false_support",
                        "RELATED": "related_contamination",
                    }.get(predicted_relation, "unexpected_relation")
                    failures.append({"type": kind, "note_id": note_id, "predicted": predicted_relation})
            if not abstain_ok:
                failures.append({"type": "abstention_failure", "expected": expected_abstain, "predicted": predicted_abstain})
            for note_id, result in citation_results.items():
                if not result["valid"]:
                    failures.append({"type": "citation_mismatch", "note_id": note_id, "reason": result["reason"]})

            cases.append({
                "question_id": case["question_id"],
                "coverage": case["coverage"],
                "expected_relations": expected,
                "predicted_relations": predicted,
                "presented_relations": presented,
                "expected_abstain": expected_abstain,
                "predicted_abstain": predicted_abstain,
                "relations_exact": predicted_pairs == expected_pairs,
                "presentation_relations_exact": presented_pairs == expected_pairs,
                "abstention_correct": abstain_ok,
                "exact_case": predicted_pairs == expected_pairs and abstain_ok,
                "presentation_exact_case": presented_pairs == expected_pairs and abstain_ok,
                "raw_candidates": raw,
                "trace": answer.trace,
                "citations": citation_results,
                "failures": failures,
            })

    precision = ratio(tp, tp + fp)
    recall = ratio(tp, tp + fn)
    by_class = {
        relation.value: class_metrics(**relation_counts[relation])
        for relation in EVALUATED_RELATIONS
    }
    raw_class_precision = {
        relation: ratio(
            relation_counts[relation]["tp"],
            relation_counts[relation]["tp"] + relation_counts[relation]["fp"],
        )
        for relation in EVALUATED_RELATIONS
    }
    raw_class_recall = {
        relation: ratio(
            relation_counts[relation]["tp"],
            relation_counts[relation]["tp"] + relation_counts[relation]["fn"],
        )
        for relation in EVALUATED_RELATIONS
    }
    raw_class_f1 = {
        relation: f1(raw_class_precision[relation], raw_class_recall[relation])
        for relation in EVALUATED_RELATIONS
    }
    defined_precision = [value for value in raw_class_precision.values() if value is not None]
    defined_recall = [value for value in raw_class_recall.values() if value is not None]
    defined_f1 = [value for value in raw_class_f1.values() if value is not None]

    abstention_precision = ratio(abstain_tp, abstain_tp + abstain_fp)
    abstention_recall = ratio(abstain_tp, abstain_tp + abstain_fn)
    abstention_specificity = ratio(abstain_tn, abstain_tn + abstain_fp)
    balanced = (
        (abstention_recall + abstention_specificity) / 2
        if abstention_recall is not None and abstention_specificity is not None
        else None
    )
    support = by_class[Relation.SUPPORT.value]
    counter = by_class[Relation.COUNTER_EVIDENCE.value]
    related = by_class[Relation.RELATED.value]

    metrics = {
        "case_count": len(cases),
        "exact_cases": sum(case["exact_case"] for case in cases),
        "presentation_exact_cases": sum(case["presentation_exact_case"] for case in cases),
        "relation_precision": rounded(precision),
        "relation_recall": rounded(recall),
        "relation_f1": rounded(f1(precision, recall)),
        "relation_macro_precision": rounded(sum(defined_precision) / len(defined_precision)) if defined_precision else None,
        "relation_macro_recall": rounded(sum(defined_recall) / len(defined_recall)) if defined_recall else None,
        "relation_macro_f1": rounded(sum(defined_f1) / len(defined_f1)) if defined_f1 else None,
        "relation_by_class": by_class,
        "false_counter_rate": rounded(
            None
            if raw_class_precision[Relation.COUNTER_EVIDENCE] is None
            else 1 - raw_class_precision[Relation.COUNTER_EVIDENCE]
        ),
        "counter_precision": counter["precision"],
        "counter_recall": counter["recall"],
        "false_support_rate": rounded(
            None
            if raw_class_precision[Relation.SUPPORT] is None
            else 1 - raw_class_precision[Relation.SUPPORT]
        ),
        "support_precision": support["precision"],
        "support_recall": support["recall"],
        "related_contamination_rate": rounded(
            None
            if raw_class_precision[Relation.RELATED] is None
            else 1 - raw_class_precision[Relation.RELATED]
        ),
        "related_precision": related["precision"],
        "related_recall": related["recall"],
        "abstention_accuracy": round((abstain_tp + abstain_tn) / len(cases), 4),
        "abstention_precision": rounded(abstention_precision),
        "abstention_recall": rounded(abstention_recall),
        "abstention_specificity": rounded(abstention_specificity),
        "abstention_balanced_accuracy": rounded(balanced),
        "expected_abstain_count": abstain_tp + abstain_fn,
        "predicted_abstain_count": abstain_tp + abstain_fp,
        "citation_coverage": rounded(ratio(citation_present, citation_total)),
        "citation_integrity": rounded(ratio(citation_valid, citation_total)),
        "predicted_counter_count": counter["predicted_count"],
        "false_counter_count": counter["fp"],
        "predicted_support_count": support["predicted_count"],
        "false_support_count": support["fp"],
        "predicted_related_count": related["predicted_count"],
        "related_contamination_count": related["fp"],
    }
    output = {
        "freeze": freeze,
        "metrics": metrics,
        "cases": cases,
    }
    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(metrics, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
