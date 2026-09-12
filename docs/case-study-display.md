# Case study: retrieved evidence hidden by the display limit

This is a small engineering reproduction using three **synthetic English notes** about garden volunteers. It contains no personal reading material and is not a benchmark or evidence of external adoption.

## Problem and decision

When several retrieved notes have the same relation, the default output shows only one. A reader may therefore mistake a display limit for missing retrieval. The existing trace already records the omitted candidates and their drop reasons.

The change exposes the existing display limit as `--max-per-relation N` and adds a hidden-evidence count to text output. It keeps the default at one, with the same retrieval, classifications and abstention decision. It does not introduce query rewriting or a new judge.

## Reproduce from the installed checkout

After the [README installation](../README.md), run from the repository root:

```bash
.venv/bin/reading-evidence ingest demo/display/corpus --index .reading-evidence/display.json
.venv/bin/reading-evidence ask "Should garden volunteers always grow tomatoes during summer?" --index .reading-evidence/display.json
.venv/bin/reading-evidence ask "Should garden volunteers always grow tomatoes during summer?" --index .reading-evidence/display.json --max-per-relation 3
```

Add `--json` to either question command to inspect the complete trace.

| Observation | Default | `--max-per-relation 3` |
| --- | --- | --- |
| Retrieved candidates | 3 | Same 3 |
| Displayed evidence | 1 | 3 |
| Relations of the displayed notes | `RELATED` | All `RELATED` |
| Answer status | `ABSTAINED` | `ABSTAINED` |
| Hidden-evidence hint | `additional evidence hidden: 2` | No hint |

The three source files concern [tools](../demo/display/corpus/tools.md), [storage](../demo/display/corpus/storage.md), and [watering](../demo/display/corpus/watering.md). They do not establish whether volunteers should always grow tomatoes. Showing more background should therefore not turn abstention into a supported answer.

## Evidence and remaining failure

The [focused CLI test](../tests/test_cli_display.py) checks the one-to-three change, unchanged candidates and abstention, source-line availability, and invalid limits rejected before judge construction. The release check also runs these commands through an installed package outside the source directory.

This demonstrates a presentation fix, not improved semantic retrieval. The [known C04 failure](walkthrough.md#3-reproduce-a-known-semantic-failure) still labels an implicit counterexample as support. A larger display limit cannot correct that label or recover a note that retrieval never found.

**Engineering takeaway:** inspect retrieval, classification and presentation separately before choosing a fix. This example supports that diagnosis; whether exposing more evidence helps another person's task requires their feedback.

## 中文说明

这三条笔记完全是合成材料。默认只显示一条，原因是每种关系只展示一条；增加展示上限后能看见三条，但它们仍只是相关背景，无法回答“夏天是否应该总种番茄”，所以继续拒答。

这个案例证明了一个具体工程改动：让用户看见更多已经找到的材料，并保留原有拒答判断。它不证明自动理解用户问题、中文语义判断或跨书综合能力。公开的错误样本仍然保留，可与本案例一起复核。
