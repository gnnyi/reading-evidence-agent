# Design decisions

## Deterministic baseline first

The base installation uses only the Python standard library at runtime. With the default lexical judge, it runs without model downloads, credentials, network calls, or hidden prompts. Packaging still depends on the declared build backend being available when `pip install` runs. Pipeline outputs are deterministic; candidate-evaluation timing fields naturally vary.

The existing model adapter is an optional extra, not part of the verified offline path. It is never selected implicitly. Remote mode requires explicit public-data confirmation. Its presence and simulated tests do not establish real provider compatibility or semantic improvement; no remote command is required for the public walkthrough.

Tradeoff: overlap and polarity heuristics cannot perform general entailment. Negation, irony, qualifications, and multi-sentence arguments can be misclassified. The trace exposes these decisions so later models can be evaluated against the baseline.

## Multi-query without an agent framework

The query planner produces three transparent variants. Reciprocal-rank fusion merges their candidates. This is enough to test whether query diversity helps; orchestration frameworks would add surface area without evidence of need.

## Explicit abstention

Related content is not evidence for a claim. V0 abstains unless at least one support or counter-evidence item clears a fixed confidence threshold, even when related notes exist.

## Source-relative citations

Ingest stores paths relative to the supplied corpus root, rejects files whose resolved path escapes that root, and records the original first-content-line offset so citations remain source-line faithful after text normalization. This keeps a cloned demo portable without letting relative symlinks silently widen the read boundary.

## Public and private evaluation stay separate

The public fixtures are newly authored synthetic material. The CLI exposes path-based integration for local benchmarks, but no private adapter, default path, or data sample belongs in this repository.
