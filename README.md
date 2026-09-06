[English](README.md) | [简体中文](README.zh-CN.md)

# Reading Evidence Agent

Your notes can retrieve what looks similar. Can they retrieve what challenges your current belief?

Reading Evidence Agent explores a different retrieval question:

> Given a current question or belief, can a reading corpus surface evidence that supports it, challenges it, is merely related, or contains no useful evidence at all?

An offline, reproducible evidence-retrieval engineering project: BM25 + RRF retrieval, a replaceable relation judge, source-line citations, abstention, decision traces, and separate pipeline/candidate evaluations. The default judge is deterministic. An optional model adapter exists as experimental code, with simulated tests only; no live model result is claimed. There is no answer generation or dynamic Agent Loop.

## Beyond similarity search

| Ordinary retrieval | Reading Evidence framing |
|---|---|
| Question → similarity search → top-k related chunks | Question or belief → query variants → BM25 + RRF → relation judgment → `SUPPORT` / `COUNTER_EVIDENCE` / `RELATED` / `ABSTAIN` → citation + trace |

Relation judgment is the product and evaluation target. In V0.1 it is implemented with transparent lexical/polarity rules, not a reliable semantic classifier.

## See it work

After ingesting the public demo corpus (see Quick start below), ask:

```bash
.venv/bin/reading-evidence ask "Should I treat a failed experiment as wasted time?"
```

Example output, abbreviated from the current CLI:

```text
SUPPORT
  [failed-experiment-waste] When a failed experiment is wasted
  Citation: failed-experiment-waste.md#L1
  Confidence: 0.950 — Overlapping claim with matching explicit polarity

COUNTER_EVIDENCE
  [failed-experiment-learning] Failure can buy information
  Citation: failed-experiment-learning.md#L3
  Confidence: 0.950 — Overlapping claim with opposite explicit polarity

RELATED
  [experiment-preregistration] Pre-register the learning condition
  Citation: experiment-preregistration.md#L3
  Confidence: 0.490 — Shares a topic but not enough of the claim

NO_EVIDENCE / ABSTAIN: NO

Trace:
  - rewritten queries: {"original": "Should I treat a failed experiment as wasted time?", ...}
  - candidates retrieved: 11
  - candidates deduplicated: 5
  - relation decisions: 3
```

The full output also includes source excerpts and a deduplicated source list.

## Quick start

Requirements: Python 3.10+. The base installation has no third-party runtime dependencies or external API keys. All commands below run locally after installation.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .

.venv/bin/reading-evidence ingest demo/corpus
.venv/bin/reading-evidence ask "Should I treat a failed experiment as wasted time?"
```

Run the public evaluation:

```bash
.venv/bin/reading-evidence eval \
  --questions demo/questions.json \
  --dataset demo/gold.json
```

Run the four-class candidate demo (fixed question/note pairs; retrieval is bypassed):

```bash
.venv/bin/reading-evidence judge-eval \
  --dataset demo/judge-cases.json --judge lexical
```

Follow the [five-minute walkthrough](docs/walkthrough.md) to inspect a success, abstention, and a known failure.

Run tests:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## What V0.1 establishes

The verified path uses `LexicalJudge`. It establishes:

- relation-aware retrieval with explicit `SUPPORT`, `COUNTER_EVIDENCE`, and `RELATED` labels;
- abstention when directional evidence is too weak;
- source-relative, source-line-faithful citations and decision traces;
- reproducible public fixtures and evaluation contracts.

`RelationJudge` and `judge-eval` allow fixed-candidate comparisons without changing retrieval. The optional DeepSeek adapter validates structured output and exact source quotes; its error/retry handling is covered by simulated clients. Live SDK compatibility, semantic quality, prompt-injection resistance, latency, and costs remain unverified. The base install and CI do not activate it. This is not a completed RAG application or an autonomous agent.

## How V0.1 works

1. Ingest `.md` and `.txt` notes into a deterministic local JSON index.
2. Expand a question into original, support-seeking, and counter-seeking query variants.
3. Retrieve each variant with BM25 and combine rankings with reciprocal-rank fusion (RRF).
4. Classify retrieved notes with inspectable claim-overlap and polarity rules.
5. Return citations and abstain unless sufficiently confident directional evidence exists.

The pipeline is deliberately small. Its failures can be reproduced, inspected, and measured without hiding them behind an opaque model call. See [architecture](docs/architecture.md) and [design decisions](docs/design-decisions.md).

## Why Eval is part of the product

The original four-case presentation-level regression looked perfect. After separating classification evaluation from the one-per-relation presentation cap, the same fixture is only 2 / 4 classification-exact while the CLI presentation remains 4 / 4. The separately frozen 20-case adversarial benchmark continues to expose the harder failure modes.

| Dataset or metric | Corrected V0.1 result |
|---|---:|
| Four-case classification exact | 2 / 4 — regression only |
| Four-case presentation exact | 4 / 4 |
| Frozen adversarial exact cases | 8 / 20 |
| Relation precision | 0.4737 |
| Relation recall | 0.4286 |
| Relation F1 | 0.4500 |
| Relation macro F1 | 0.3621 |
| False counter rate | 0.5000 |
| Counter recall | 0.1250 |
| RELATED contamination | 0.7500 |
| RELATED recall | 0.2500 |
| Abstention accuracy | 0.6500 |
| Abstention balanced accuracy | 0.5000 |
| Citation span integrity | 1.0000 |

The corrected Eval scores all retrieved non-`IRRELEVANT` classifications before the presentation cap. This exposes false positives that the old top-one display policy could hide; `presentation_exact_case_rate` remains available as a UI regression metric. The frozen benchmark still shows weak counter-evidence recall, false directional labels, RELATED contamination, and poor balanced abstention.

These numbers are not a quality claim. Eval inputs, raw outputs, and failure analysis are first-class repository artifacts so that the next technical decision can be based on observed failures rather than a perfect demo score:

- frozen [adversarial Gold](reports/release-review/adversarial-gold.json);
- V0.1 [raw results](reports/release-review/adversarial-results.json);
- historical [release review and failure analysis](reports/release-review/public-release-candidate-review.md);
- [evaluation methodology](docs/eval-methodology.md).

## Known limitations

- Relation classification is lexical and heuristic. Implicit counter-evidence, mixed stances, irony, and complex negation often fail.
- Tokenization supports ASCII words and deterministic overlapping Han bigrams. It does not provide Chinese word segmentation, synonym matching, or Chinese semantic relation judgment.
- There is no dynamic second retrieval or Agent Loop.
- Performance on a large corpus has not been established.
- Real-user value and performance on private reading data have not been validated.

## Bring your own evaluation data

The public project never discovers or reads a private corpus by default. A local benchmark can use explicit paths:

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

Current V0.1:

- deterministic lexical/polarity baseline;
- reproducible public demo;
- frozen adversarial benchmark and failure analysis;
- citation, trace, and abstention behavior;
- a replaceable judge contract and a four-class offline candidate demo;
- an experimental model adapter tested with simulated responses only.

Possible next investigations, not commitments:

- semantic relation judgment;
- dynamic second retrieval based on evidence quality;
- multilingual retrieval;
- private real-world benchmark.

Web UI, vector-database infrastructure, multi-agent orchestration, user accounts, and cloud SaaS are intentionally out of scope.

## Contributing

Start with [CONTRIBUTING.md](CONTRIBUTING.md) and the [relation annotation guide](docs/relation-annotation-guide.md). The committed 20-case adversarial set is regression-only; a separate blind/holdout Eval must be frozen before it can be used for semantic-judge model selection.
