from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from reading_evidence.judge import JudgeError
from reading_evidence.judge_evaluation import load_judge_eval_dataset, run_judge_eval
from reading_evidence.models import Relation


def _case(
    case_id: str,
    relation: str,
    *,
    tags: list[str] | None = None,
) -> dict:
    irrelevant = relation == "IRRELEVANT"
    return {
        "id": case_id,
        "question": "这个判断有证据吗？",
        "note": {
            "note_id": f"note-{case_id}",
            "title": "评测记录",
            "text": "标题\n这是一条可核验的证据。",
            "source": f"{case_id}.md",
            "line_start": 10,
        },
        "expected_relation": relation,
        "expected_evidence_line": None if irrelevant else 11,
        "expected_evidence_quote": None if irrelevant else "可核验的证据",
        "tags": tags or [],
    }


class ExactFakeJudge:
    def judge(self, question, candidate):
        relation = {
            "note-S": Relation.SUPPORT,
            "note-C": Relation.COUNTER_EVIDENCE,
            "note-R": Relation.RELATED,
            "note-I": Relation.IRRELEVANT,
        }[candidate.note.note_id]
        irrelevant = relation == Relation.IRRELEVANT
        return SimpleNamespace(
            relation=relation,
            confidence=0.9,
            reason="fixture",
            evidence_line=None if irrelevant else 11,
            evidence_quote=None if irrelevant else "这是一条可核验的证据。",
            trace={
                "latency_ms": 12.0,
                "tokens": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15,
                },
                "request_count": 1,
                "retry_count": 0,
            },
        )


class ErrorFakeJudge:
    def judge(self, question, candidate):
        raise JudgeError(
            "provider_error",
            "provider unavailable",
            trace={"request_count": 1, "retry_count": 0},
        )


class InvalidSchemaFakeJudge:
    def __init__(self, **overrides):
        self.overrides = overrides

    def judge(self, question, candidate):
        value = {
            "relation": Relation.SUPPORT,
            "confidence": 0.9,
            "reason": "fixture",
            "evidence_line": 11,
            "evidence_quote": "这是一条可核验的证据。",
            "trace": {},
        }
        value.update(self.overrides)
        return SimpleNamespace(**value)


class JudgeEvaluationTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _write(self, value: object) -> Path:
        path = self.root / "dataset.json"
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def test_exact_metrics_and_telemetry_are_aggregated(self) -> None:
        dataset = self._write(
            [
                _case("S", "SUPPORT", tags=["prompt_injection"]),
                _case("C", "COUNTER_EVIDENCE"),
                _case("R", "RELATED"),
                _case("I", "IRRELEVANT"),
            ]
        )
        result = run_judge_eval(dataset, ExactFakeJudge())
        self.assertEqual("OK", result["status"])
        self.assertEqual(1.0, result["relation_accuracy"])
        self.assertEqual(1.0, result["relation_macro_f1"])
        self.assertEqual(1.0, result["counter_recall"])
        self.assertEqual(1.0, result["prompt_injection_accuracy"])
        self.assertEqual(1.0, result["schema_valid_rate"])
        self.assertEqual(1.0, result["citation_integrity"])
        self.assertEqual(3, result["citation_output_count"])
        self.assertEqual(1.0, result["gold_evidence_match_rate"])
        self.assertEqual(3, result["gold_evidence_case_count"])
        self.assertEqual(48.0, result["aggregate"]["latency_ms"]["total"])
        self.assertEqual(60, result["aggregate"]["tokens"]["total_tokens"]["total"])
        self.assertEqual(4, result["aggregate"]["request_count"])
        self.assertEqual(0, result["aggregate"]["retry_count"])
        self.assertEqual("dataset.json", result["dataset"])
        self.assertNotIn(str(self.root), result["dataset"])
        self.assertEqual(64, len(result["dataset_sha256"]))

    def test_source_fidelity_is_independent_of_an_irrelevant_relation_error(self) -> None:
        dataset = self._write([_case("I", "IRRELEVANT")])

        result = run_judge_eval(dataset, InvalidSchemaFakeJudge())

        self.assertEqual(0.0, result["relation_accuracy"])
        self.assertEqual(1.0, result["citation_integrity"])
        self.assertEqual(1, result["citation_output_count"])
        self.assertIsNone(result["gold_evidence_match_rate"])
        self.assertEqual(0, result["gold_evidence_case_count"])

    def test_gold_evidence_match_is_separate_from_exact_source_fidelity(self) -> None:
        value = _case("S", "SUPPORT")
        value["note"]["text"] = "标题\n这是一条可核验的证据。\n另一条真实原文。"
        dataset = self._write([value])
        judge = InvalidSchemaFakeJudge(
            evidence_line=12,
            evidence_quote="另一条真实原文。",
        )

        result = run_judge_eval(dataset, judge)

        self.assertEqual(1.0, result["relation_accuracy"])
        self.assertEqual(1.0, result["citation_integrity"])
        self.assertEqual(1, result["citation_output_count"])
        self.assertEqual(0.0, result["gold_evidence_match_rate"])
        self.assertEqual(1, result["gold_evidence_case_count"])

    def test_provider_error_is_structured_and_not_scored_as_irrelevant(self) -> None:
        dataset = self._write([_case("I", "IRRELEVANT")])
        result = run_judge_eval(dataset, ErrorFakeJudge())
        self.assertEqual("JUDGE_ERROR", result["status"])
        self.assertEqual(1, result["error_count"])
        self.assertEqual(0.0, result["relation_accuracy"])
        self.assertIsNone(result["cases"][0]["predicted_relation"])
        self.assertFalse(result["cases"][0]["schema_valid"])

    def test_invalid_judgment_contract_fails_closed(self) -> None:
        invalid_values = (
            {"relation": "SUPPORT"},
            {"confidence": True},
            {"confidence": 1.1},
            {"reason": ""},
            {"evidence_line": None},
            {"evidence_quote": ""},
            {"evidence_quote": "two\nlines"},
            {"trace": None},
        )
        for overrides in invalid_values:
            with self.subTest(overrides=overrides):
                dataset = self._write([_case("S", "SUPPORT")])
                result = run_judge_eval(dataset, InvalidSchemaFakeJudge(**overrides))
                self.assertEqual("JUDGE_ERROR", result["status"])
                self.assertEqual(0.0, result["schema_valid_rate"])
                self.assertFalse(result["cases"][0]["schema_valid"])
                self.assertIsNone(result["cases"][0]["predicted_relation"])

    def test_public_demo_preserves_existing_questions_notes_and_relations(self) -> None:
        root = Path(__file__).resolve().parents[1]
        questions = {
            item["id"]: item["question"]
            for item in json.loads((root / "demo/questions.json").read_text())
        }
        gold = {
            item["question_id"]: item
            for item in json.loads((root / "demo/gold.json").read_text())
        }
        cases = load_judge_eval_dataset(root / "demo/judge-cases.json")
        self.assertEqual(set(Relation), {case.expected_relation for case in cases})
        for case in cases:
            question_id = next(tag.removeprefix("derived_") for tag in case.tags if tag.startswith("derived_"))
            self.assertEqual(questions[question_id], case.question)
            self.assertEqual(
                (root / "demo/corpus" / case.note.source).read_text().strip(), case.note.text,
            )
            self.assertEqual(
                gold[question_id]["expected_relations"].get(case.note.note_id, "IRRELEVANT"),
                case.expected_relation.value,
            )

    def test_loader_rejects_duplicate_ids(self) -> None:
        dataset = self._write([_case("S", "SUPPORT"), _case("S", "SUPPORT")])
        with self.assertRaisesRegex(ValueError, "duplicate id"):
            load_judge_eval_dataset(dataset)

    def test_loader_rejects_quote_outside_expected_line(self) -> None:
        value = _case("S", "SUPPORT")
        value["expected_evidence_quote"] = "不存在的文字"
        dataset = self._write([value])
        with self.assertRaisesRegex(ValueError, "not on the expected line"):
            load_judge_eval_dataset(dataset)

    def test_loader_rejects_evidence_for_irrelevant_case(self) -> None:
        value = _case("I", "IRRELEVANT")
        value["expected_evidence_line"] = 11
        value["expected_evidence_quote"] = "可核验的证据"
        dataset = self._write([value])
        with self.assertRaisesRegex(ValueError, "IRRELEVANT.*must be null"):
            load_judge_eval_dataset(dataset)

    def test_loader_rejects_absolute_source_path(self) -> None:
        value = _case("S", "SUPPORT")
        value["note"]["source"] = "/private/corpus/claim.md"
        dataset = self._write([value])
        with self.assertRaisesRegex(ValueError, "note.source.*must be relative"):
            load_judge_eval_dataset(dataset)


if __name__ == "__main__":
    unittest.main()
