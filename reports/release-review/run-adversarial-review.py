from __future__ import annotations

import hashlib
import json
import tempfile
from pathlib import Path

from reading_evidence.agent import ask
from reading_evidence.ingest import ingest_corpus, load_index
from reading_evidence.query import decompose_query
from reading_evidence.relation import classify_candidate
from reading_evidence.retrieval import retrieve


ROOT = Path(__file__).resolve().parents[2]
REVIEW = ROOT / "reports" / "release-review"
CORPUS_ROOT = REVIEW / "adversarial"
GOLD_PATH = REVIEW / "adversarial-gold.json"
FREEZE_PATH = REVIEW / "adversarial-freeze.json"
OUTPUT_PATH = REVIEW / "adversarial-results.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def corpus_aggregate_hash() -> str:
    lines = []
    for path in sorted(value for value in CORPUS_ROOT.rglob("*") if value.is_file()):
        relative = path.relative_to(ROOT).as_posix()
        lines.append(f"{sha256(path)}  {relative}\n")
    return hashlib.sha256("".join(lines).encode()).hexdigest()


def citation_check(item, case: dict, corpus_dir: Path) -> tuple[bool, str]:
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
    if line < 1 or line > len(path.read_text().splitlines()):
        return False, "citation_line_out_of_range"
    expected = case.get("expected_citations", {}).get(item.note_id)
    if expected is not None and item.citation != expected:
        return False, f"expected_{expected}_got_{item.citation}"
    source_text = " ".join(path.read_text().split())
    excerpt_prefix = item.excerpt.removesuffix("…")
    if not source_text.startswith(excerpt_prefix):
        return False, "excerpt_does_not_match_source"
    return True, "ok"


def main() -> int:
    freeze = json.loads(FREEZE_PATH.read_text())
    if sha256(GOLD_PATH) != freeze["gold_sha256"]:
        raise RuntimeError("Adversarial Gold changed after freeze")
    if corpus_aggregate_hash() != freeze["corpus_hash_of_sorted_sha256_lines"]:
        raise RuntimeError("Adversarial corpus changed after freeze")

    gold = json.loads(GOLD_PATH.read_text())
    cases = []
    tp = fp = fn = 0
    predicted_counter = false_counter = 0
    predicted_support = false_support = 0
    predicted_related = related_contamination = 0
    abstention_correct = 0
    citation_total = citation_present = citation_valid = 0

    for case in gold:
        corpus_dir = CORPUS_ROOT / case["corpus_dir"]
        with tempfile.TemporaryDirectory() as temporary:
            index = Path(temporary) / "index.json"
            ingest_corpus(corpus_dir, index)
            answer = ask(case["question"], index)
            notes, _ = load_index(index)
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

            predicted = {item.note_id: item.relation.value for item in answer.evidence}
            expected = case["expected_relations"]
            predicted_pairs = set(predicted.items())
            expected_pairs = set(expected.items())
            tp += len(predicted_pairs & expected_pairs)
            fp += len(predicted_pairs - expected_pairs)
            fn += len(expected_pairs - predicted_pairs)
            abstain_ok = answer.abstained == case["expected_abstain"]
            abstention_correct += int(abstain_ok)

            for note_id, relation in predicted.items():
                if relation == "COUNTER_EVIDENCE":
                    predicted_counter += 1
                    false_counter += int(expected.get(note_id) != relation)
                elif relation == "SUPPORT":
                    predicted_support += 1
                    false_support += int(expected.get(note_id) != relation)
                elif relation == "RELATED":
                    predicted_related += 1
                    related_contamination += int(expected.get(note_id) != relation)

            citation_results = {}
            for item in answer.evidence:
                citation_total += 1
                citation_present += int(bool(item.citation))
                valid, reason = citation_check(item, case, corpus_dir)
                citation_valid += int(valid)
                citation_results[item.note_id] = {"citation": item.citation, "valid": valid, "reason": reason}

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
                    failures.append({"type": "ranking_or_selection_miss", "note_id": note_id, "expected": expected_relation})
            for note_id, predicted_relation in predicted.items():
                if note_id not in expected:
                    kind = {
                        "COUNTER_EVIDENCE": "false_counter",
                        "SUPPORT": "false_support",
                        "RELATED": "related_contamination",
                    }.get(predicted_relation, "unexpected_relation")
                    failures.append({"type": kind, "note_id": note_id, "predicted": predicted_relation})
            if not abstain_ok:
                failures.append({"type": "abstention_failure", "expected": case["expected_abstain"], "predicted": answer.abstained})
            for note_id, result in citation_results.items():
                if not result["valid"]:
                    failures.append({"type": "citation_mismatch", "note_id": note_id, "reason": result["reason"]})

            cases.append({
                "question_id": case["question_id"],
                "coverage": case["coverage"],
                "expected_relations": expected,
                "predicted_relations": predicted,
                "expected_abstain": case["expected_abstain"],
                "predicted_abstain": answer.abstained,
                "relations_exact": predicted_pairs == expected_pairs,
                "abstention_correct": abstain_ok,
                "exact_case": predicted_pairs == expected_pairs and abstain_ok,
                "raw_candidates": raw,
                "trace": answer.trace,
                "citations": citation_results,
                "failures": failures,
            })

    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    metrics = {
        "case_count": len(cases),
        "exact_cases": sum(case["exact_case"] for case in cases),
        "relation_precision": round(precision, 4),
        "relation_recall": round(recall, 4),
        "relation_f1": round(f1, 4),
        "false_counter_rate": round(false_counter / predicted_counter, 4) if predicted_counter else 0.0,
        "false_support_rate": round(false_support / predicted_support, 4) if predicted_support else 0.0,
        "related_contamination_rate": round(related_contamination / predicted_related, 4) if predicted_related else 0.0,
        "abstention_accuracy": round(abstention_correct / len(cases), 4),
        "citation_coverage": round(citation_present / citation_total, 4) if citation_total else 1.0,
        "citation_integrity": round(citation_valid / citation_total, 4) if citation_total else 1.0,
        "predicted_counter_count": predicted_counter,
        "false_counter_count": false_counter,
        "predicted_support_count": predicted_support,
        "false_support_count": false_support,
        "predicted_related_count": predicted_related,
        "related_contamination_count": related_contamination,
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
