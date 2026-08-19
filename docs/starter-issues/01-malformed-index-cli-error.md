# Starter: reject malformed index entries without a traceback

## Why

`load_index()` constructs `Note(**value)` directly. Structurally malformed note objects can therefore raise `TypeError`, while the CLI currently normalizes `OSError`, `ValueError`, and `JSONDecodeError` into a readable `error:` message. A malformed local index should fail through the same explicit CLI boundary instead of exposing an implementation traceback.

## Fixture

Create a temporary JSON index with version `1`, `document_count: 1`, and `notes: [{}]`. The corpus hash may be any string because structural validation should fail before the hash can be trusted.

Then run:

```bash
reading-evidence ask "Does spaced retrieval improve recall?" --index /tmp/malformed-index.json
```

## Expected result

- process exit code: `2`;
- stderr starts with `error:` and identifies a malformed index/note entry;
- no Python traceback;
- valid indexes behave exactly as before.

## Acceptance test

Add a subprocess or `cli.main()` regression test that proves the malformed fixture returns `2` without `Traceback`, plus an existing-valid-index control. Do not broaden exception handling to swallow unrelated programmer errors from retrieval/classification.
