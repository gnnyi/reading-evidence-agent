from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reading_evidence.cli import build_parser, main
from reading_evidence.ingest import ingest_corpus
from reading_evidence.judge import JudgeError


def _dataset() -> list[dict]:
    return [
        {
            "id": "CLI-01",
            "question": "这个判断有证据吗？",
            "note": {
                "note_id": "cli-note",
                "title": "记录",
                "text": "标题\n这是一条证据。",
                "source": "cli-note.md",
                "line_start": 1,
            },
            "expected_relation": "SUPPORT",
            "expected_evidence_line": 2,
            "expected_evidence_quote": "一条证据",
            "tags": [],
        }
    ]


class ErrorFakeJudge:
    judge_id = "error-fixture"
    citation_mode = "exact_quote"

    def judge(self, question, candidate):
        raise JudgeError(
            "provider_error",
            "provider unavailable",
            trace={"request_count": 1, "retry_count": 0},
        )


class CliJudgeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.dataset = self.root / "dataset.json"
        self.dataset.write_text(
            json.dumps(_dataset(), ensure_ascii=False),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_existing_ask_and_eval_default_to_lexical(self) -> None:
        parser = build_parser()
        ask_args = parser.parse_args(["ask", "question"])
        eval_args = parser.parse_args(
            ["eval", "--questions", "questions.json", "--dataset", "gold.json"]
        )
        self.assertEqual("lexical", ask_args.judge)
        self.assertEqual("lexical", eval_args.judge)
        self.assertFalse(ask_args.confirm_public_data)
        self.assertFalse(eval_args.confirm_public_data)

    def test_deepseek_confirmation_fails_before_provider_construction(self) -> None:
        stderr = io.StringIO()
        with patch("reading_evidence.cli.DeepSeekJudge") as constructor:
            with contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "judge-eval",
                        "--dataset",
                        str(self.dataset),
                        "--judge",
                        "deepseek",
                    ]
                )
        self.assertEqual(2, exit_code)
        constructor.assert_not_called()
        self.assertIn("--confirm-public-data is required", stderr.getvalue())

    def test_judge_eval_provider_error_is_json_and_nonzero(self) -> None:
        stdout = io.StringIO()
        with patch("reading_evidence.cli._build_judge", return_value=ErrorFakeJudge()):
            with contextlib.redirect_stdout(stdout):
                exit_code = main(
                    ["judge-eval", "--dataset", str(self.dataset)]
                )
        result = json.loads(stdout.getvalue())
        self.assertEqual(3, exit_code)
        self.assertEqual("JUDGE_ERROR", result["status"])
        self.assertEqual(1, result["error_count"])
        self.assertIsNone(result["cases"][0]["predicted_relation"])

    def test_retrieval_eval_provider_error_is_nonzero_not_abstention(self) -> None:
        corpus = self.root / "corpus"
        corpus.mkdir()
        (corpus / "claim.md").write_text(
            "# Claim\n\nEvidence supports the claim.\n",
            encoding="utf-8",
        )
        index = self.root / "index.json"
        ingest_corpus(corpus, index)
        questions = self.root / "questions.json"
        gold = self.root / "gold.json"
        questions.write_text(
            json.dumps([{"id": "Q", "question": "Evidence supports the claim."}]),
            encoding="utf-8",
        )
        gold.write_text(
            json.dumps(
                [
                    {
                        "question_id": "Q",
                        "expected_relations": {"claim": "SUPPORT"},
                        "expected_abstain": False,
                    }
                ]
            ),
            encoding="utf-8",
        )
        stderr = io.StringIO()
        with patch("reading_evidence.cli._build_judge", return_value=ErrorFakeJudge()):
            with contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "eval",
                        "--index",
                        str(index),
                        "--questions",
                        str(questions),
                        "--dataset",
                        str(gold),
                    ]
                )
        self.assertEqual(3, exit_code)
        self.assertIn("Judge failed for Q", stderr.getvalue())
        self.assertNotIn("abstain", stderr.getvalue().lower())


if __name__ == "__main__":
    unittest.main()
