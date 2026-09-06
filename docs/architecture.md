# Architecture

V0 is a local pipeline with five bounded capabilities:

```text
notes -> ingest -> local JSON index
                       |
question -> query variants -> BM25 retrieval -> RRF deduplication
                                           -> relation baseline
                                           -> citation + abstention
                                           -> trace / Eval
```

## Modules

- `ingest`: reads public or user-supplied Markdown/text and stores only source-relative paths.
- `query`: creates deterministic original/support/counter query variants.
- `retrieval`: runs BM25 per query and reciprocal-rank fusion across candidates.
- `judge`: defines `RelationJudge` and wraps the unchanged lexical baseline in `LexicalJudge`. An optional DeepSeek adapter is experimental and not live-validated.
- `relation`: assigns `SUPPORT`, `COUNTER_EVIDENCE`, `RELATED`, or `IRRELEVANT` using an inspectable baseline.
- `abstention`: emits `NO_EVIDENCE / ABSTAIN` when no directional result clears the confidence threshold.
- `citation`: points results back to an ingested note and line.
- `trace`: records query rewrites, full candidate identities/ranks, every classification, selection/drop reasons, deterministic configuration, and the indexed corpus hash.
- `evaluation`: scores uncapped candidate classifications independently from the presentation cap, plus abstention and citation integrity, against an explicit dataset.

- `judge_evaluation`: scores fixed question/note pairs across all four relations, including `IRRELEVANT`; it bypasses retrieval and retains errors in the denominator.

No background service is required. The index is a local artifact and is ignored by Git at its default path.

## Extension seams

`RelationJudgment` in `models.py` and `RelationJudge` in `judge/base.py` define the candidate boundary. A judgment includes relation, confidence, reason, evidence line/quote, and a trace. Invalid structure or an ungrounded quote in `exact_quote` mode invalidates the answer with `JUDGE_ERROR`; it never falls back silently to lexical evidence. Candidate Eval reports errors separately. Normal abstention is not a judge failure. The CLI exits 2 for input errors and 3 for judge errors.

Retrieval, classification, presentation, and evaluation remain separate. A replacement judge does not establish that it improves semantics; use fixed candidates before changing retrieval. There is no generated answer or conditional retrieval loop.
