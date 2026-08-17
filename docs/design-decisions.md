# Design decisions

## Deterministic baseline first

V0 uses only the Python standard library. This keeps a fresh clone installable without model downloads, credentials, network calls, or hidden prompts. It also makes every public Eval run deterministic.

Tradeoff: overlap and polarity heuristics cannot perform general entailment. Negation, irony, qualifications, and multi-sentence arguments can be misclassified. The trace exposes these decisions so later models can be evaluated against the baseline.

## Multi-query without an agent framework

The query planner produces three transparent variants. Reciprocal-rank fusion merges their candidates. This is enough to test whether query diversity helps; orchestration frameworks would add surface area without evidence of need.

## Explicit abstention

Related content is not evidence for a claim. V0 abstains unless at least one support or counter-evidence item clears a fixed confidence threshold, even when related notes exist.

## Source-relative citations

Ingest stores paths relative to the supplied corpus root. This makes a cloned demo portable and prevents local absolute paths from entering its index format.

## Public and private evaluation stay separate

The public fixtures are newly authored synthetic material. The CLI exposes path-based integration for local benchmarks, but no private adapter, default path, or data sample belongs in this repository.
