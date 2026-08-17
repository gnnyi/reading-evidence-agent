# Reading Evidence Agent

Your notes can retrieve what looks similar. Can they retrieve what challenges your current belief?

Reading Evidence Agent V0.1 is a local-first, deterministic evidence-retrieval baseline. It searches an English reading corpus for supporting evidence, counter-evidence, related material, and explicit absence of evidence.

It is designed to test relation-aware retrieval—not to present the current pipeline as a completed Agent loop, generic personal RAG, or “second brain.” V0.1 has no dynamic second retrieval, model-based evidence judge, or autonomous tool loop. It provides a reproducible synthetic demo, inspectable traces, citations back to source notes, and an evaluation runner.

## Try the public demo

Requirements: Python 3.10+; no runtime dependencies or external API keys.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .

.venv/bin/reading-evidence ingest demo/corpus
.venv/bin/reading-evidence ask "Should I treat a failed experiment as wasted time?"
```

The answer is grouped into:

- `SUPPORT`: material aligned with the belief under test;
- `COUNTER_EVIDENCE`: material with overlapping claims and opposing polarity;
- `RELATED`: useful context without a directional claim;
- `NO_EVIDENCE / ABSTAIN`: an explicit refusal when directional evidence is too weak.

Each result includes a stable note ID, an excerpt, a source-relative citation, confidence, and a reason. The trace shows rewritten queries, retrieval volume, deduplication, and relation decisions.

Run the public evaluation:

```bash
.venv/bin/reading-evidence eval \
  --questions demo/questions.json \
  --dataset demo/gold.json
```

Run tests:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## How the deterministic V0.1 baseline works

1. Ingest `.md` and `.txt` notes into a deterministic local JSON index.
2. Decompose a question into original, support-seeking, and counter-seeking queries.
3. Retrieve each query with a small BM25 implementation and merge results using reciprocal-rank fusion.
4. Apply an inspectable relation-classification baseline based on claim overlap and explicit polarity.
5. Return citations and abstain unless sufficiently confident directional evidence exists.

The classifier is intentionally a lexical/polarity baseline. It does not claim general natural-language inference or Agent behavior.

## Frozen adversarial benchmark

The four-case demo Eval currently passes, but it is a regression fixture—not a quality claim. A separate 20-case synthetic adversarial benchmark was frozen before execution and produced:

| Metric | V0.1 result |
|---|---:|
| Exact relation + abstention cases | 8 / 20 |
| Relation precision | 0.4444 |
| Relation recall | 0.3810 |
| Relation F1 | 0.4103 |
| False counter rate | 0.5000 |
| Counter recall | 0.1250 |
| RELATED contamination | 1.0000 |
| Abstention accuracy | 0.6500 |
| Citation integrity after the V0.1 line-selection fix | 1.0000 |

The benchmark exposes real weaknesses rather than supporting a performance claim. See the frozen [Gold](reports/release-review/adversarial-gold.json), the V0.1 [raw results](reports/release-review/adversarial-results.json), and the original pre-fix [release review](reports/release-review/public-release-candidate-review.md).

Current limitations:

- relation classification is lexical and heuristic; implicit counter-evidence, mixed claims, irony, and double negation often fail;
- counter-evidence recall and RELATED classification are not production-ready;
- tokenization is English/ASCII-only;
- no dynamic Agent loop or second retrieval exists;
- performance on a large corpus has not been established;
- private real-world evaluation remains in progress and has not passed a public gate.

More detail is documented in [design decisions](docs/design-decisions.md) and [evaluation methodology](docs/eval-methodology.md).

## Bring your own evaluation data

The public project never reads a private corpus by default. A local benchmark can use explicit paths:

```bash
.venv/bin/reading-evidence ingest path/to/corpus --index path/to/local-index.json
.venv/bin/reading-evidence eval \
  --index path/to/local-index.json \
  --questions path/to/questions.json \
  --dataset path/to/gold.json \
  --output path/to/untracked-results.json
```

Keep private corpora, indexes, gold labels, and outputs outside the repository. See [privacy](docs/privacy.md) and [evaluation methodology](docs/eval-methodology.md).

## Project status

- Public synthetic demo: included as a regression fixture.
- Local-first deterministic relation-aware baseline: implemented.
- Private real-world evaluation: in progress, with no public performance claim.
- Dynamic Agent loop: not implemented.
- Web UI, vector database, multi-agent orchestration, accounts, and cloud SaaS: intentionally out of scope.
