from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reading_evidence.agent import ask
from reading_evidence.evaluation import run_eval
from reading_evidence.ingest import ingest_corpus, load_index
from reading_evidence.models import Relation


ROOT = Path(__file__).resolve().parents[1]
DEMO_CORPUS = ROOT / "demo" / "corpus"


class PublicV0Test(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.index = Path(self.temporary.name) / "index.json"
        self.manifest = ingest_corpus(DEMO_CORPUS, self.index)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_ingest_is_deterministic_and_sources_are_relative(self) -> None:
        notes, metadata = load_index(self.index)
        self.assertEqual(9, metadata["document_count"])
        self.assertEqual(self.manifest["corpus_sha256"], metadata["corpus_sha256"])
        self.assertTrue(all(not Path(note.source).is_absolute() for note in notes))

    def test_relation_aware_answer_has_citations_and_trace(self) -> None:
        answer = ask("Should I treat a failed experiment as wasted time?", self.index)
        relations = {item.relation for item in answer.evidence}
        self.assertIn(Relation.SUPPORT, relations)
        self.assertIn(Relation.COUNTER_EVIDENCE, relations)
        self.assertIn(Relation.RELATED, relations)
        self.assertFalse(answer.abstained)
        by_id = {item.note_id: item.relation for item in answer.evidence}
        self.assertEqual(Relation.SUPPORT, by_id["failed-experiment-waste"])
        self.assertEqual(Relation.COUNTER_EVIDENCE, by_id["failed-experiment-learning"])
        self.assertTrue(all(item.citation.endswith("#L1") for item in answer.evidence))
        self.assertEqual(3, len(answer.trace["rewritten_queries"]) - 1)
        self.assertGreaterEqual(answer.trace["candidates_retrieved"], answer.trace["candidates_deduplicated"])

    def test_no_evidence_abstains(self) -> None:
        answer = ask("Should an office chair be replaced every two years?", self.index)
        self.assertTrue(answer.abstained)
        self.assertEqual([], answer.evidence)

    def test_generic_predicate_does_not_create_related_contamination(self) -> None:
        answer = ask("Does reading faster always improve comprehension?", self.index)
        by_id = {item.note_id: item.relation for item in answer.evidence}
        self.assertNotIn("more-notes-help", by_id)
        self.assertEqual(Relation.RELATED, by_id["review-questions"])

    def test_index_rejects_absolute_source_path(self) -> None:
        payload = json.loads(self.index.read_text())
        payload["notes"][0]["source"] = str((ROOT / "demo" / "corpus" / "x.md").resolve())
        self.index.write_text(json.dumps(payload))
        with self.assertRaisesRegex(ValueError, "absolute source"):
            load_index(self.index)

    def test_public_eval_is_reproducible(self) -> None:
        result = run_eval(
            self.index,
            ROOT / "demo" / "questions.json",
            ROOT / "demo" / "gold.json",
        )
        self.assertEqual(4, result["case_count"])
        self.assertEqual(1.0, result["relation_f1"])
        self.assertEqual(1.0, result["abstention_accuracy"])
        self.assertEqual(1.0, result["citation_coverage"])
        self.assertEqual(1.0, result["exact_case_rate"])


if __name__ == "__main__":
    unittest.main()
