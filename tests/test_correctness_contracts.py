from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from reading_evidence.agent import ask
from reading_evidence.citation import validate_citation
from reading_evidence.evaluation import run_eval
from reading_evidence.ingest import ingest_corpus, load_index
from reading_evidence.models import Relation


class CorrectnessContractTest(unittest.TestCase):
    def _write_eval_files(self, root: Path, questions: list[dict], gold: list[dict]) -> tuple[Path, Path]:
        questions_path = root / "questions.json"
        gold_path = root / "gold.json"
        questions_path.write_text(json.dumps(questions), encoding="utf-8")
        gold_path.write_text(json.dumps(gold), encoding="utf-8")
        return questions_path, gold_path

    def test_empty_gold_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "a.md").write_text("# A\n\nAlpha beta gamma.", encoding="utf-8")
            index = root / "index.json"
            ingest_corpus(corpus, index)
            questions, gold = self._write_eval_files(root, [], [])
            with self.assertRaisesRegex(ValueError, "at least one case"):
                run_eval(index, questions, gold)

    def test_relation_metrics_pair_false_rate_with_recall_when_class_is_suppressed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "claim.md").write_text(
                "# Spacing helps recall\n\nSpaced retrieval improves long-term recall.",
                encoding="utf-8",
            )
            index = root / "index.json"
            ingest_corpus(corpus, index)
            questions, gold = self._write_eval_files(
                root,
                [{"id": "Q", "question": "Spaced retrieval improves long-term recall."}],
                [{
                    "question_id": "Q",
                    "expected_relations": {"claim": "COUNTER_EVIDENCE"},
                    "expected_abstain": False,
                }],
            )
            result = run_eval(index, questions, gold)
            self.assertIsNone(result["false_counter_rate"])
            self.assertIsNone(result["counter_precision"])
            self.assertEqual(0.0, result["counter_recall"])
            self.assertEqual(0, result["relation_by_class"]["COUNTER_EVIDENCE"]["predicted_count"])
            self.assertEqual(1, result["relation_by_class"]["COUNTER_EVIDENCE"]["gold_count"])

    def test_abstention_balanced_accuracy_exposes_never_abstain_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "claim.md").write_text(
                "# Spacing helps recall\n\nSpaced retrieval improves long-term recall.",
                encoding="utf-8",
            )
            index = root / "index.json"
            ingest_corpus(corpus, index)
            questions, gold = self._write_eval_files(
                root,
                [
                    {"id": "Q1", "question": "Spaced retrieval improves long-term recall."},
                    {"id": "Q2", "question": "Spaced retrieval improves long-term recall."},
                ],
                [
                    {
                        "question_id": "Q1",
                        "expected_relations": {"claim": "SUPPORT"},
                        "expected_abstain": False,
                    },
                    {
                        "question_id": "Q2",
                        "expected_relations": {},
                        "expected_abstain": True,
                    },
                ],
            )
            result = run_eval(index, questions, gold)
            self.assertEqual(0.5, result["abstention_accuracy"])
            self.assertEqual(0.0, result["abstention_recall"])
            self.assertEqual(1.0, result["abstention_specificity"])
            self.assertEqual(0.5, result["abstention_balanced_accuracy"])

    def test_eval_scores_uncapped_classifications_not_presentation_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "a.md").write_text(
                "# Spacing improves recall\n\nSpaced retrieval improves long-term recall.",
                encoding="utf-8",
            )
            (corpus / "b.md").write_text(
                "# Repeated recall helps\n\nSpaced retrieval improves long-term recall through repeated recall.",
                encoding="utf-8",
            )
            index = root / "index.json"
            ingest_corpus(corpus, index)
            question = "Spaced retrieval improves long-term recall."
            self.assertEqual(1, len(ask(question, index).by_relation(Relation.SUPPORT)))
            questions, gold = self._write_eval_files(
                root,
                [{"id": "Q", "question": question}],
                [{
                    "question_id": "Q",
                    "expected_relations": {"a": "SUPPORT", "b": "SUPPORT"},
                    "expected_abstain": False,
                }],
            )
            result = run_eval(index, questions, gold)
            self.assertEqual(1.0, result["relation_recall"])
            self.assertEqual(1.0, result["exact_case_rate"])
            self.assertEqual(0.0, result["presentation_exact_case_rate"])

    def test_ingest_preserves_original_source_line_numbers(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "claim.md").write_text(
                "\n\n# Review protocol\n\nSpaced retrieval improves long-term recall.\n",
                encoding="utf-8",
            )
            index = root / "index.json"
            ingest_corpus(corpus, index)
            answer = ask("Spaced retrieval improves long-term recall.", index)
            by_id = {item.note_id: item for item in answer.evidence}
            self.assertEqual("claim.md#L5", by_id["claim"].citation)

    def test_counter_citation_points_to_counter_span(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "mixed.md").write_text(
                "# Reading claim\n\n"
                "Reading faster improves comprehension.\n\n"
                "Reading faster does not improve comprehension and does not improve understanding.\n",
                encoding="utf-8",
            )
            index = root / "index.json"
            ingest_corpus(corpus, index)
            answer = ask("Reading faster improves comprehension.", index)
            item = answer.evidence[0]
            self.assertEqual(Relation.COUNTER_EVIDENCE, item.relation)
            self.assertEqual("mixed.md#L5", item.citation)
            note = load_index(index)[0][0]
            self.assertEqual(
                (False, "citation_line_not_relation_consistent"),
                validate_citation(
                    note,
                    "Reading faster improves comprehension.",
                    Relation.COUNTER_EVIDENCE,
                    "mixed.md#L3",
                ),
            )
            self.assertEqual(
                (True, "ok"),
                validate_citation(
                    note,
                    "Reading faster improves comprehension.",
                    Relation.COUNTER_EVIDENCE,
                    item.citation,
                ),
            )
            self.assertEqual(True, answer.trace["candidate_decisions"][0]["selected"])

    @unittest.skipIf(os.name == "nt", "symlink creation is not reliably available on Windows CI")
    def test_ingest_rejects_file_resolving_outside_corpus_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            corpus = root / "corpus"
            corpus.mkdir()
            outside = root / "private.md"
            outside.write_text("# Private\n\nSECRET_OUTSIDE_CORPUS", encoding="utf-8")
            (corpus / "linked.md").symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "outside the corpus root"):
                ingest_corpus(corpus, root / "index.json")

    def test_trace_contains_all_candidates_selection_reasons_and_deterministic_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            corpus = root / "corpus"
            corpus.mkdir()
            (corpus / "a.md").write_text(
                "# Spacing improves recall\n\nSpaced retrieval improves long-term recall.",
                encoding="utf-8",
            )
            (corpus / "b.md").write_text(
                "# Repeated recall helps\n\nSpaced retrieval improves long-term recall through repeated recall.",
                encoding="utf-8",
            )
            index = root / "index.json"
            manifest = ingest_corpus(corpus, index)
            answer = ask("Spaced retrieval improves long-term recall.", index)
            trace = answer.trace
            self.assertEqual(2, trace["schema_version"])
            self.assertEqual(manifest["corpus_sha256"], trace["corpus_sha256"])
            self.assertEqual(2, len(trace["candidates"]))
            self.assertEqual(2, len(trace["candidate_decisions"]))
            self.assertEqual(1, len(trace["relation_decisions"]))
            dropped = [item for item in trace["candidate_decisions"] if not item["selected"]]
            self.assertEqual(["max_per_relation"], [item["drop_reason"] for item in dropped])
            self.assertEqual(8, trace["config"]["top_k_per_query"])
            self.assertEqual(60, trace["config"]["rrf_k"])
            self.assertEqual(1, trace["config"]["max_per_relation"])
            self.assertEqual(0.6, trace["config"]["abstention_confidence_threshold"])
            self.assertEqual("lexical-polarity-v0.1", trace["config"]["relation_classifier"])

    def test_bm25_scores_are_stable_across_python_hash_seeds(self) -> None:
        script = r'''
import json
from reading_evidence.models import Note, QueryPlan
from reading_evidence.retrieval import retrieve
notes = [
    Note("a", "Alpha beta gamma", "alpha beta gamma delta epsilon", "a.md"),
    Note("b", "Alpha delta", "alpha delta epsilon zeta", "b.md"),
]
plan = QueryPlan(
    original="alpha beta gamma delta epsilon zeta",
    core="alpha beta gamma delta epsilon zeta",
    support="alpha beta gamma delta epsilon zeta support reason true",
    counter="alpha beta gamma delta epsilon zeta risk false exception",
)
print(json.dumps([(item.note.note_id, item.best_lexical_score, item.rrf_score) for item in retrieve(notes, plan)]))
'''
        root = Path(__file__).resolve().parents[1]
        outputs = []
        for seed in ("1", "2"):
            env = os.environ.copy()
            env["PYTHONHASHSEED"] = seed
            env["PYTHONPATH"] = str(root / "src")
            outputs.append(
                subprocess.check_output([sys.executable, "-c", script], env=env, text=True)
            )
        self.assertEqual(outputs[0], outputs[1])


if __name__ == "__main__":
    unittest.main()
