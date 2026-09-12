# Release candidate — 2026-09-12

**Status: local release checks passed; not published.** Lee authorized preparation of this candidate. The current files are uncommitted changes on `0464cf1`; publication, remote CI and independent user acceptance remain separate steps.

The release is an inspectable offline evidence-retrieval baseline for developers checking a claim against short notes. It adds clearer bilingual onboarding, contributor and feedback entry points, and `ask --max-per-relation N` with a hidden-evidence hint. The default remains one item per relation. Retrieval, semantic judgments and abstention are unchanged.

## Verified candidate

The [machine-readable check record](../reports/release-candidate/2026-09-12.json) includes commands, tested-input SHA-256 hashes, observations and limits. Checks ran on an allowlisted temporary copy, excluding all pre-existing untracked Chinese benchmark files and private material.

| Check | Result |
| --- | --- |
| README editable installation | Passed in a fresh Python 3.14.3 environment on macOS |
| Built wheel and independent installation | Passed; installed with `--no-index` into a second fresh environment |
| CLI outside the source directory | Passed with `PYTHONPATH` unset; package imports from `site-packages` |
| Candidate unit suite | 57 tests passed |
| Three public walkthrough samples | Three relation classes and chair abstention reproduced; C04 still wrongly labels `pivot` as support |
| Synthetic display case | One to three displayed notes; same retrieved candidates and `ABSTAINED` status; hidden-evidence hint verified |
| Four-case public evaluation | 2/4 classification-exact; 4/4 presentation-exact |
| Four-case fixed-candidate evaluation | 4/4 labels; 3/3 source-faithful citations; 2/3 expected spans |
| Frozen 20-case regression | Two hash seeds produced byte-identical results, unchanged from the committed artifact |
| Model requests | Zero |

The [display case study](case-study-display.md) uses only synthetic garden notes and gives before/after commands. Its purpose is to let another developer inspect a concrete diagnosis and bounded change, including what remains wrong.

The initial September 7 install failed because build dependencies could not be downloaded; retain the [historical record](../reports/onboarding/2026-09-07.json). On September 12, the sandbox initially blocked the public package download; approved network access allowed installation without changing package requirements or disabling build isolation.

These are local results on macOS/Python 3.14.3. This candidate has not yet run in remote CI, on Python 3.10 locally, or on Windows. A fresh remote clone cannot contain these unpushed changes. GitHub template rendering and independent first use remain unverified. The existing CI matrix covers Python 3.10 and 3.14 when the candidate is pushed; historical green CI is not a pass for this candidate.

## Evidence status

| Evidence | Present state | Missing observation |
| --- | --- | --- |
| Technical | Installed package, known failures, regression and display change are locally reproducible | Remote CI on the exact published commit |
| Adoption | Maintainer feedback informed the display change; no confirmed independent trial recorded | An independent user's task, attempt and actual outcome |
| Public | The repository was accessible on September 7; this update is local | Candidate changes, templates and release visible remotely |

Neither successful tests nor a release announcement proves that another person benefits. The [feedback loop](feedback.md) remains a proposed manual process until a real report and follow-up occur.

## Exact publication scope

Include only:

- `README.md`, `README.zh-CN.md`, `CONTRIBUTING.md`;
- `src/reading_evidence/cli.py`, `tests/test_cli_display.py`;
- `docs/walkthrough.md`, `docs/starter-issues/README.md`, `docs/evidence.md`, `docs/feedback.md`, `docs/release-readiness.md`, `docs/case-study-display.md`;
- the three synthetic files in `demo/display/corpus/`;
- `.github/ISSUE_TEMPLATE/bug_report.md`, `.github/ISSUE_TEMPLATE/first_use.md`, `.github/pull_request_template.md`;
- `reports/onboarding/2026-09-07.json`, `reports/release-candidate/2026-09-12.json`.

Retain all other tracked baseline files. Exclude the pre-existing untracked `benchmarks/`, `tests/test_benchmark_contract.py`, private notes, private indexes, personal-question traces, local virtual environments and build output. Do not stage the whole working directory indiscriminately. This candidate retains package version `0.1.0`; it is not a newly published package version.

## Remaining publication steps

After Lee explicitly authorizes the concrete external writes:

1. Commit and push only the reviewed scope; verify remote CI for that exact commit. Keep release pending on failure.
2. Check both README entry points and template selection on GitHub. Publish the release using the draft below; create the three existing starter task specifications as actual issues and update their links.
3. Invite a first relevant developer only through recipients/channels Lee explicitly approves. Record the attempted task and result using the [feedback guide](feedback.md), then choose the next change from observed problems.

No new model, UI, broader benchmark or live WeRead integration is needed for this release. Publication does not authorize sending invitations to unspecified people. The next usefulness check is one independent trial, not further internal feature expansion.

## Proposed release copy — not published

Title: **An inspectable offline evidence-retrieval baseline**

Reading Evidence Agent lets you inspect whether short notes support a claim, challenge it, or are only related, with source-line citations and a decision trace. The default command-line workflow runs locally without a model key.

This update adds a clearer bilingual first-run path, a three-sample walkthrough, first-use and bug-report templates, and three scoped contributor tasks. The CLI also reports hidden evidence and accepts `--max-per-relation N` to show more passages from the same retrieval. The underlying relation classifier and abstention policy are unchanged. A synthetic three-note case study reproduces the display change and explains why abstention remains appropriate.

The known adversarial regression remains 8/20 exact cases with relation F1 0.45. Citations can point to real but unhelpful lines; implicit counter-evidence can be labeled as support. Public data is synthetic, model-adapter tests are simulated, and real-user usefulness remains unverified.

Start with the README, inspect the known failure, then try one real question against a few short notes if the use case fits. Tell us where you stopped and whether the result helped. A failed run or a result you would not use is welcome feedback.

## Proposed Chinese invitation — not sent

我做了一个小型开源实验：输入一个观点，从短笔记中找支持、反对和仅仅相关的材料，并显示原文引用和判断过程。默认离线运行，不需要模型密钥。

它目前的语义判断还很弱，公开对抗集只有 8/20 完全正确，F1 为 0.45；这次想验证的是：这种查看证据的方式对一个具体任务有没有用。

如果你正在做检索评测或核对阅读笔记，可以从 README 的三个例子开始。愿意继续的话，只试一个真实问题和几条短笔记即可。想知道你停在哪一步、哪里误判、是否帮助完成了任务；不必上传私人笔记，也不需要给好评。

项目：https://github.com/gnnyi/reading-evidence-agent
反馈：https://github.com/gnnyi/reading-evidence-agent/issues
