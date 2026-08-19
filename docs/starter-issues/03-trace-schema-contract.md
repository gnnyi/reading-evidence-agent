# Starter: document and mechanically validate trace schema v2

## Why

Trace v2 now records retrieved candidates, candidate decisions, selection/drop reasons, deterministic config, and corpus hash. The contract is exercised in unit tests but is not yet documented as an inspectable public schema. A small validator would let contributors change trace-producing code without accidentally dropping the information needed to reproduce a decision.

## Fixture

Use the existing C18 adversarial corpus (`reports/release-review/adversarial/c18-three-way`) and its question. It yields three retrieved candidates while presentation keeps only two relation decisions because one `RELATED` candidate is dropped by `max_per_relation`.

## Expected result

For a valid trace:

- every entry in `candidates` has exactly one corresponding `candidate_decisions` entry by `note_id`;
- every selected candidate decision appears in `relation_decisions`;
- every unselected non-`IRRELEVANT` decision has a non-empty `drop_reason`;
- `schema_version`, `corpus_sha256`, and deterministic config fields are present;
- candidate order remains deterministic;
- validation must not call a model or require third-party packages.

## Acceptance test

Add a dependency-free validator plus tests using C18. The valid trace must pass. Mutated fixtures that remove a candidate decision, mark a dropped item selected without adding it to `relation_decisions`, or remove `drop_reason` must fail with readable reasons. Existing `Answer.to_dict()` output remains backward compatible apart from explicitly documented trace-schema validation.
