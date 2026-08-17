[English](README.md) | [简体中文](README.zh-CN.md)

# Reading Evidence Agent

Your notes can retrieve what looks similar. Can they retrieve what challenges your current belief?

Reading Evidence Agent explores a different retrieval question:

> Given a current question or belief, can a reading corpus surface evidence that supports it, challenges it, is merely related, or contains no useful evidence at all?

The project direction is an evidence-seeking Agent. V0.1 is its deterministic baseline: a small, local-first system for testing the retrieval flow, relation schema, abstention behavior, citations, traces, and Eval contract before adding a semantic judge or dynamic Agent Loop.

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

Requirements: Python 3.10+; no runtime dependencies or external API keys.

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

Run tests:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## What V0.1 establishes

V0.1 is the deterministic baseline for the broader Reading Evidence Agent project. It establishes the inspectable parts of the system before a semantic judge or dynamic retrieval loop is introduced:

- relation-aware retrieval with explicit `SUPPORT`, `COUNTER_EVIDENCE`, and `RELATED` labels;
- abstention when directional evidence is too weak;
- source-relative citations and decision traces;
- reproducible public fixtures and evaluation contracts.

It is not a completed Agent Loop. There is no model-based evidence judge, autonomous tool use, or question-dependent decision to retrieve again.

## How V0.1 works

1. Ingest `.md` and `.txt` notes into a deterministic local JSON index.
2. Expand a question into original, support-seeking, and counter-seeking query variants.
3. Retrieve each variant with BM25 and combine rankings with reciprocal-rank fusion (RRF).
4. Classify retrieved notes with inspectable claim-overlap and polarity rules.
5. Return citations and abstain unless sufficiently confident directional evidence exists.

The pipeline is deliberately small. Its failures can be reproduced, inspected, and measured without hiding them behind an opaque model call. See [architecture](docs/architecture.md) and [design decisions](docs/design-decisions.md).

## Why Eval is part of the product

A four-case demo fixture looked perfect. A separately frozen 20-case adversarial benchmark exposed the actual failure modes.

| Dataset or metric | V0.1 result |
|---|---:|
| Four-case demo fixture | 4 / 4 exact — regression only |
| Frozen adversarial exact cases | 8 / 20 |
| Relation precision | 0.4444 |
| Relation recall | 0.3810 |
| Relation F1 | 0.4103 |
| False counter rate | 0.5000 |
| Counter recall | 0.1250 |
| RELATED contamination | 1.0000 |
| Abstention accuracy | 0.6500 |
| Citation integrity after the V0.1 line-selection fix | 1.0000 |

That gap shows why both evaluations are kept: tiny synthetic fixtures are useful for regression, but they do not validate retrieval quality. The frozen benchmark found weak counter-evidence recall, false directional labels, and contamination in `RELATED` results that the four-case fixture missed.

These numbers are not a quality claim. Eval inputs, raw outputs, and failure analysis are first-class repository artifacts so that the next technical decision can be based on observed failures rather than a perfect demo score:

- frozen [adversarial Gold](reports/release-review/adversarial-gold.json);
- V0.1 [raw results](reports/release-review/adversarial-results.json);
- independent [release review and failure analysis](reports/release-review/public-release-candidate-review.md);
- [evaluation methodology](docs/eval-methodology.md).

## Known limitations

- Relation classification is lexical and heuristic. Implicit counter-evidence, mixed stances, irony, and complex negation often fail.
- Tokenization is English/ASCII-only.
- There is no dynamic second retrieval or Agent Loop.
- Performance on a large corpus has not been established.
- Private real-world evaluation is still in progress and has not passed a public gate.

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
- citation, trace, and abstention behavior.

Possible next investigations, not commitments:

- semantic relation judgment;
- dynamic second retrieval based on evidence quality;
- multilingual retrieval;
- private real-world benchmark.

Web UI, vector-database infrastructure, multi-agent orchestration, user accounts, and cloud SaaS are intentionally out of scope.
