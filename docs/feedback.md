# First-use feedback / 首次使用反馈

The first use case to validate is narrow: **a developer checks one real claim against a few short notes and decides whether the retrieved evidence helps**. This is a hypothesis, not demonstrated demand. A result that wastes your time or misses the point is useful feedback.

先用一个真实问题与 3～5 条短笔记判断是否值得继续。无需先整理整个知识库，也无需提供私人原文。

## Try one real question locally

First complete the [public walkthrough](walkthrough.md). The default judge is local. Keep your own files and outputs outside the checkout. After replacing the example corpus path and question below, run from the repository root:

```bash
trial_dir="$(mktemp -d)"
.venv/bin/reading-evidence ingest /path/to/your/short-notes --index "$trial_dir/index.json"
.venv/bin/reading-evidence ask "Replace this with your actual question" --index "$trial_dir/index.json"
```

The temporary index contains note text. Keep it private and delete it when your trial is finished. Each file is one retrieval unit: use short `.md` or `.txt` notes rather than an entire book. Read the original cited lines and surrounding context; confidence is a heuristic score. Chinese tokenization works, but relation semantics are unverified.

## Tell us what happened

[Open a first-use report](https://github.com/gnnyi/reading-evidence-agent/issues/new?template=first_use.md) in English or Chinese. The useful minimum is:

1. What were you trying to do, and what would you normally use?
2. Where did you stop: install, demo, own notes, or reviewing evidence?
3. What happened: helpful passage, wrong relation, poor quote, nothing retrieved, or no practical benefit?
4. Did you actually use the result in a task? Would you use it again, and why?

Include OS, Python version, and commit when reporting a failure. Remove private paths and content. A public or synthetic minimal example is optional; say explicitly if it only approximates a private failure. Do not attach a whole corpus, index, or raw trace. Anyone can read public issues.

中文简报也可以：**原本要做什么 → 停在哪一步 → 实际结果 → 是否帮助完成任务 → 是否已经再次使用**。没跑通、不需要这个工具、不准备继续用，都请如实记录。

## Maintainer response loop

For the first three independent trials, keep the process manual. Do not add telemetry, a dashboard, a mailing list, or a new service before the usefulness question is answered.

When a report arrives, the maintainer should:

1. Record the stage and reported outcome in the issue; identify what is self-reported versus reproduced. Ask only for the missing detail needed to understand it.
2. Reproduce a public minimal example if available. Classify the problem as installation, retrieval, relation, citation, expectation mismatch, or no useful task.
3. Link one scoped fix or record why no change is warranted. A merged fix is technical progress, not proof that the reporter benefited.
4. Invite a retest in the same issue when a fix is available; record the actual follow-up, including silence as unknown. Do not close a usefulness question as solved solely because tests passed.

No response-time commitment is made. Aggregate only publicly shareable reports, and separate maintainer/agent runs from external trials. Count unique reporters, not comments; do not count duplicate reports or stars as adoption.

| Evidence stage | Minimum evidence | Does not establish |
|---|---|---|
| Public visibility | An accessible release, post, or repository link | Someone tried it |
| First run | An external user's report of attempting or completing the steps | It helped their work |
| Useful outcome | A specific task and how the result helped, reported by the user | Repeated use |
| Return use | A later, separate real task completed with the tool | Broad demand or commercial value |

## Decision after three trials

Three trials are a qualitative checkpoint, not a statistical estimate. If installation blocks use, fix that step first. If people run the tool but find no useful task, revisit the use case before adding semantic models or infrastructure. If a specific evidence failure blocks an otherwise useful task, use its smallest permitted reproduction to choose the next technical change.

Do not fill missing outcomes with inferred success. There is currently no confirmed external-use evidence recorded in this candidate; that is not proof that nobody has used the repository.
