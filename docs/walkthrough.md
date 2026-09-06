# Five-minute offline walkthrough

Install the base package using the [README](../README.md). All commands below use public synthetic material and the default lexical judge. No model API, credentials, or optional dependencies are needed.

## 1. Inspect evidence and abstention

From the repository root:

```bash
.venv/bin/reading-evidence ingest demo/corpus
.venv/bin/reading-evidence ask "Should I treat a failed experiment as wasted time?" --json
.venv/bin/reading-evidence ask "Should an office chair be replaced every two years?" --json
```

The first answer shows support, counter-evidence, and related context; the second abstains. Inspect `trace.candidates` and `trace.candidate_decisions` to distinguish retrieval, classification, and display trimming. An `IRRELEVANT` candidate label and an answer-level `ABSTAINED` status describe different decisions. Confidence is a rule score, not a calibrated probability.

## 2. Separate classification from citation quality

```bash
.venv/bin/reading-evidence judge-eval --dataset demo/judge-cases.json --judge lexical
```

These four pairs reuse Q01 and Q04 from the public demo. They demonstrate the candidate input format, not generalization. Current output matches 4/4 relation labels and quotes 3/3 real source lines, but matches only 2/3 expected evidence spans. DQ01-1 cites the heading at line 1 instead of the substantive paragraph at line 3. Read the paragraph yourself: a valid source address does not prove that an excerpt supports a conclusion.

## 3. Reproduce a known semantic failure

```bash
.venv/bin/reading-evidence ingest \
  reports/release-review/adversarial/c04-implicit-counter \
  --index .reading-evidence/c04.json
.venv/bin/reading-evidence ask \
  "Teams should persist with an idea despite repeated weak demand." \
  --index .reading-evidence/c04.json --json
```

C04 retrieves `pivot` but classifies it as `SUPPORT`; the frozen label is `COUNTER_EVIDENCE`. The passage describes the benefit of changing direction after weak demand. The lexical baseline misses that implication. This is a judgment failure after retrieval, so adding a vector database alone would not resolve this case.

## 4. Read the two evaluation levels correctly

```bash
.venv/bin/reading-evidence eval --questions demo/questions.json --dataset demo/gold.json
.venv/bin/python -m unittest discover -s tests -v
```

The public pipeline demo is 2/4 classification-exact and 4/4 presentation-exact. The frozen adversarial result is 8/20 exact, with relation F1 0.45. The [raw frozen results](../reports/release-review/adversarial-results.json), [runner](../reports/release-review/run-adversarial-review.py), and [metric definitions](eval-methodology.md) make these limitations inspectable. Running the frozen runner rewrites its deterministic public result file; CI checks it remains byte-identical.

## What this project demonstrates

The verified work is local retrieval, replaceable judgment contracts, evidence grounding checks, explicit failure/abstention handling, and reproducible evaluation. The optional model adapter has simulated-client tests only. No live-model quality, complete RAG generation, LangGraph workflow, large-corpus performance, or real-user value is established.

Before presenting this project, be able to explain: why use BM25 + RRF here; why C04 is a judgment failure; how source fidelity differs from entailment; why presentation exact can hide false positives; and how a fixed-candidate experiment would isolate a future semantic judge's contribution. Running commands is the start; explaining the outputs is the portfolio evidence.
