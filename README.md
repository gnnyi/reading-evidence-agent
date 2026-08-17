# Reading Evidence Agent

Your notes can retrieve what looks similar. Can they retrieve what challenges your current belief?

Reading Evidence Agent is a local-first retrieval agent that searches a reading corpus for supporting evidence, counter-evidence, related material, and explicit absence of evidence.

It is designed for relation-aware evidence retrieval—not as a generic personal RAG or “second brain.” V0 provides a reproducible synthetic demo, inspectable traces, citations back to source notes, and an evaluation runner. A separate private real-world evaluation is in progress; this repository makes no claim that it has passed.

## Try the public demo

Requirements: Python 3.10+; no runtime dependencies or external API keys.

```bash
python -m venv .venv
.venv/bin/pip install -e .

reading-evidence ingest demo/corpus
reading-evidence ask "Should I treat a failed experiment as wasted time?"
```

The answer is grouped into:

- `SUPPORT`: material aligned with the belief under test;
- `COUNTER_EVIDENCE`: material with overlapping claims and opposing polarity;
- `RELATED`: useful context without a directional claim;
- `NO_EVIDENCE / ABSTAIN`: an explicit refusal when directional evidence is too weak.

Each result includes a stable note ID, an excerpt, a source-relative citation, confidence, and a reason. The trace shows rewritten queries, retrieval volume, deduplication, and relation decisions.

Run the public evaluation:

```bash
reading-evidence eval \
  --questions demo/questions.json \
  --dataset demo/gold.json
```

Run tests:

```bash
python -m unittest discover -s tests -v
```

## How V0 works

1. Ingest `.md` and `.txt` notes into a deterministic local JSON index.
2. Decompose a question into original, support-seeking, and counter-seeking queries.
3. Retrieve each query with a small BM25 implementation and merge results using reciprocal-rank fusion.
4. Apply an inspectable relation-classification baseline based on claim overlap and explicit polarity.
5. Return citations and abstain unless sufficiently confident directional evidence exists.

The classifier is intentionally a baseline. It does not claim general natural-language inference. Its limitations are visible in the public Eval and documented in [design decisions](docs/design-decisions.md).

## Bring your own evaluation data

The public project never reads a private corpus by default. A local benchmark can use explicit paths:

```bash
reading-evidence ingest path/to/corpus --index path/to/local-index.json
reading-evidence eval \
  --index path/to/local-index.json \
  --questions path/to/questions.json \
  --dataset path/to/gold.json \
  --output path/to/untracked-results.json
```

Keep private corpora, indexes, gold labels, and outputs outside the repository. See [privacy](docs/privacy.md) and [evaluation methodology](docs/eval-methodology.md).

## Project status

- Public synthetic demo: included and reproducible.
- Local-first relation-aware baseline: implemented.
- Private real-world evaluation: in progress, with no public performance claim.
- Web UI, vector database, multi-agent orchestration, accounts, and cloud SaaS: intentionally out of scope.
