# Starter contributions

Choose a small task with a fixture and acceptance criteria. These maintainer-proposed tasks are now published as issues. They are not evidence of external demand or assigned work. Check the linked issue and describe your approach before starting so work is not duplicated.

| Task | Useful skills | Done when |
|---|---|---|
| [Readable malformed-index errors](01-malformed-index-cli-error.md) · [Issue #1](https://github.com/gnnyi/reading-evidence-agent/issues/1) | Python input validation and CLI tests | A malformed note exits 2 without a traceback; a valid index still works |
| [Reproducible freeze manifest](02-freeze-manifest-helper.md) · [Issue #2](https://github.com/gnnyi/reading-evidence-agent/issues/2) | File hashing and deterministic JSON | Stable inputs give identical manifests; tampering is detected; no model runs |
| [Trace schema contract](03-trace-schema-contract.md) · [Issue #3](https://github.com/gnnyi/reading-evidence-agent/issues/3) | JSON contracts and focused tests | C18 trace passes validation; missing or inconsistent decisions fail clearly |

Start with the malformed-index task for the narrowest code change. Follow [CONTRIBUTING](../../CONTRIBUTING.md) for setup and checks. For a contribution without code, [report one first-use experience](../feedback.md) or identify an unclear walkthrough step.
