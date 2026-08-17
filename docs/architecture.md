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
- `relation`: assigns `SUPPORT`, `COUNTER_EVIDENCE`, `RELATED`, or `IRRELEVANT` using an inspectable baseline.
- `abstention`: emits `NO_EVIDENCE / ABSTAIN` when no directional result clears the confidence threshold.
- `citation`: points results back to an ingested note and line.
- `trace`: records query rewrites, candidate counts, deduplication, and decisions.
- `evaluation`: compares answer relations and abstention against an explicit dataset.

No background service is required. The index is a local artifact and is ignored by Git at its default path.

## Extension seams

The dataclasses in `models.py` are the public internal contract. A later implementation can replace lexical retrieval or the relation baseline without changing CLI output, citations, trace schema, or Eval format. Such changes should be justified by evaluation evidence rather than framework preference.
