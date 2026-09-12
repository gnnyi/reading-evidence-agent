from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from reading_evidence.cli import main
from reading_evidence.ingest import ingest_corpus


class CliDisplayTest(unittest.TestCase):
    def test_more_related_evidence_is_visible_without_changing_retrieval_or_abstention(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            corpus = root / "corpus"
            corpus.mkdir()
            for name, text in {
                "tools": "Garden volunteers share spare tools.",
                "storage": "Garden volunteers label shared storage boxes.",
                "watering": "Garden volunteers coordinate watering shifts.",
            }.items():
                (corpus / f"{name}.md").write_text(f"# {name}\n\n{text}\n")
            index = root / "index.json"
            ingest_corpus(corpus, index)
            args = [
                "ask", "Should garden volunteers always grow tomatoes during summer?",
                "--index", str(index),
            ]

            def invoke(extra):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(0, main(args + extra))
                return output.getvalue()

            compact = json.loads(invoke(["--json"]))
            expanded = json.loads(invoke(["--json", "--max-per-relation", "3"]))
            self.assertEqual(1, len(compact["evidence"]))
            self.assertEqual(3, len(expanded["evidence"]))
            self.assertTrue(all(item["relation"] == "RELATED" for item in expanded["evidence"]))
            self.assertEqual("ABSTAINED", compact["status"])
            self.assertEqual(compact["status"], expanded["status"])
            self.assertEqual(compact["abstention_reason"], expanded["abstention_reason"])
            self.assertEqual(compact["trace"]["candidates"], expanded["trace"]["candidates"])
            self.assertEqual(3, expanded["trace"]["config"]["max_per_relation"])
            self.assertTrue(all(item["selected"] for item in expanded["trace"]["candidate_decisions"]))
            for item in expanded["evidence"]:
                source, line = item["citation"].rsplit("#L", 1)
                self.assertTrue((corpus / source).read_text().splitlines()[int(line) - 1])

            default_text = invoke([])
            self.assertIn("additional evidence hidden: 2", default_text)
            expanded_text = invoke(["--max-per-relation", "3"])
            for name in ("tools", "storage", "watering"):
                self.assertIn(f"[{name}]", expanded_text)
            self.assertNotIn("additional evidence hidden", expanded_text)

    def test_invalid_display_limit_stops_before_judge_construction(self):
        for value in ("0", "-1", "1.5", "many"):
            with self.subTest(value=value):
                error = io.StringIO()
                with patch("reading_evidence.cli._build_judge") as build_judge:
                    with contextlib.redirect_stderr(error):
                        with self.assertRaises(SystemExit) as raised:
                            main(["ask", "question", "--max-per-relation", value])
                self.assertEqual(2, raised.exception.code)
                self.assertIn("--max-per-relation", error.getvalue())
                self.assertIn("must be a positive integer", error.getvalue())
                self.assertNotIn("Traceback", error.getvalue())
                build_judge.assert_not_called()


if __name__ == "__main__":
    unittest.main()
