# Contributing

Reading Evidence Agent is currently a small deterministic baseline. Contributions should preserve that property: a reviewer should be able to reproduce a change from a clean checkout without private data, hosted models, API keys, or hidden prompts.

## Start from a clean checkout

The package supports Python 3.10+. CI exercises the minimum supported version (3.10) and the current project lane (3.14).

```bash
git clone https://github.com/gnnyi/reading-evidence-agent.git
cd reading-evidence-agent
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

The project has no runtime dependencies. Package installation may still need access to the build backend declared in `pyproject.toml`.
CI deliberately runs from the source tree with `PYTHONPATH=src`, so CI itself does not install third-party test/runtime packages. If package installation is unavailable, contributors can run the same checks with `PYTHONPATH=src python ...`.

Run the unit suite:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Run the public four-case regression with explicit temporary paths:

```bash
tmpdir="$(mktemp -d)"
.venv/bin/reading-evidence ingest demo/corpus --index "$tmpdir/index.json"
.venv/bin/reading-evidence eval \
  --index "$tmpdir/index.json" \
  --questions demo/questions.json \
  --dataset demo/gold.json \
  --output "$tmpdir/public-results.json"
```

Run the frozen adversarial regression twice under different hash seeds:

```bash
PYTHONHASHSEED=1 .venv/bin/python reports/release-review/run-adversarial-review.py
cp reports/release-review/adversarial-results.json /tmp/adversarial-seed-1.json
PYTHONHASHSEED=2 .venv/bin/python reports/release-review/run-adversarial-review.py
cmp /tmp/adversarial-seed-1.json reports/release-review/adversarial-results.json
git diff --exit-code -- reports/release-review/adversarial-results.json
```

A change that intentionally updates a frozen artifact must explain why the benchmark contract changed; do not update expected output merely to make CI green.

## Scope of the current benchmark

The committed 20-case adversarial set is **regression-only**. It has already been inspected repeatedly during V0.1 development and review, so it is not a blind holdout and must not be used to choose between semantic judges, prompts, embeddings, rerankers, or other model variants.

A future model-selection holdout must be assembled, adjudicated, and frozen before the first candidate system is run on it. See [evaluation methodology](docs/eval-methodology.md) and the [relation annotation guide](docs/relation-annotation-guide.md).

## Submitting a benchmark case

Do not add a proposed case directly to the frozen 20-case corpus. Use `reports/benchmark-candidates/<case-id>/` as a review staging area. A candidate directory should contain:

- `corpus/`: the smallest public `.md`/`.txt` fixture that reproduces the intended distinction;
- `question.json`: the question ID and text;
- `proposed-gold.json`: proposed note-to-relation labels plus `expected_abstain`;
- `rationale.md`: the claim, exact evidence span(s), label rationale, known ambiguity, and whether the case came from a real failure or was synthetically constructed.

A candidate is not Gold merely because it appears in the repository. Before promotion into a future frozen benchmark it must follow the annotation/adjudication process in `docs/relation-annotation-guide.md`. For an ordinary code bug, prefer a focused unit-test fixture instead of expanding a benchmark.

## Privacy boundary

Only submit data you are allowed to publish. Never commit personal reading notes, private indexes, private Gold labels, credentials, local paths, or evaluation outputs derived from private corpora.

Ingest is intentionally bounded by the corpus root. A corpus file resolving outside that root is rejected. Do not weaken this boundary to make a fixture convenient. See [privacy boundary](docs/privacy.md).

## Pull request expectations

A focused contribution should include:

1. the smallest fixture that demonstrates the current behavior;
2. the expected behavior and why it follows from an existing contract or an explicitly proposed contract change;
3. a regression test that fails before the fix and passes after it;
4. the exact commands used to run unit tests and relevant Eval checks;
5. no unrelated architecture rewrite.

For relation-label changes, include the annotated evidence span and explain the `SUPPORT` / `COUNTER_EVIDENCE` / `RELATED` distinction rather than reporting only an aggregate score.

Three intentionally unclaimed starter tasks are tracked under [`docs/starter-issues/`](docs/starter-issues/). They are repository task specifications, not evidence that an external user has opened an issue or adopted the project.
