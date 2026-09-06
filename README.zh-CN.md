[English](README.md) | [简体中文](README.zh-CN.md)

# Reading Evidence Agent

你的笔记可以找回相似内容。但它能找出挑战你当前判断的证据吗？

Reading Evidence Agent 关注的是另一类检索问题：

> 面对一个当前问题或观点，阅读语料库能否找出支持它的证据、挑战它的反证、仅仅相关的材料，或者明确判断其中没有可用证据？

这是一个可离线复现的证据检索工程项目：BM25 + RRF 检索、可替换的关系判断器、原文行级引用、拒答、决策追踪，以及分开的流程评测与候选级评测。默认判断器使用确定性规则。仓库保留了实验性模型适配器，目前只有模拟测试，没有真实模型运行结论；尚无回答生成或动态 Agent Loop。

## 不止是相似度检索

| 普通检索 | Reading Evidence 的问题框架 |
|---|---|
| 问题 → 相似度搜索 → Top-K 相关片段 | 问题或观点 → 查询变体 → BM25 + RRF → 关系判断 → `SUPPORT` / `COUNTER_EVIDENCE` / `RELATED` / `ABSTAIN` → citation + trace |

关系判断是这个产品要解决、也要评测的核心问题。V0.1 使用透明的词法与极性规则实现这一步，不能视为可靠的语义分类器。

## 直接看效果

完成下方“快速开始”中的公开 Demo 语料导入后，运行：

```bash
.venv/bin/reading-evidence ask "Should I treat a failed experiment as wasted time?"
```

以下是当前 CLI 的真实输出节选：

```text
SUPPORT
  [failed-experiment-waste] When a failed experiment is wasted
  Citation: failed-experiment-waste.md#L1
  Confidence: 0.950 — Overlapping claim with matching explicit polarity

COUNTER_EVIDENCE
  [failed-experiment-learning] Failure can buy information
  Citation: failed-experiment-learning.md#L3
  Confidence: 0.950 — Overlapping claim with opposite explicit polarity

RELATED
  [experiment-preregistration] Pre-register the learning condition
  Citation: experiment-preregistration.md#L3
  Confidence: 0.490 — Shares a topic but not enough of the claim

NO_EVIDENCE / ABSTAIN: NO

Trace:
  - rewritten queries: {"original": "Should I treat a failed experiment as wasted time?", ...}
  - candidates retrieved: 11
  - candidates deduplicated: 5
  - relation decisions: 3
```

完整输出还包括来源摘录和去重后的来源列表。

## 快速开始

环境要求：Python 3.10+。基础安装没有第三方运行依赖，不需要外部 API key；以下命令安装完成后均在本地运行。

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .

.venv/bin/reading-evidence ingest demo/corpus
.venv/bin/reading-evidence ask "Should I treat a failed experiment as wasted time?"
```

运行公开 Eval：

```bash
.venv/bin/reading-evidence eval \
  --questions demo/questions.json \
  --dataset demo/gold.json
```

运行四分类候选演示（固定命题与原文，不经过检索）：

```bash
.venv/bin/reading-evidence judge-eval \
  --dataset demo/judge-cases.json --judge lexical
```

按[五分钟演示](docs/walkthrough.md)检查一个成功案例、一次拒答和一个已知失败。

运行测试：

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## V0.1 建立了什么

已验证的路径使用 `LexicalJudge`（规则判断器），包括：

- 使用 `SUPPORT`、`COUNTER_EVIDENCE` 和 `RELATED` 明确标注证据关系；
- 当定向证据不足时 abstain；
- 提供相对来源路径、忠实于原始源行号的 citation 和决策 trace；
- 提供可复现的公开 fixtures 与 Eval 契约。

`RelationJudge` 接口与 `judge-eval` 支持固定候选对照，不必改动检索。可选的 DeepSeek 适配器会检查结构化输出和原文引文；其错误与重试处理目前只用模拟客户端验证。真实 SDK 兼容性、语义效果、抵抗提示注入的能力、耗时和费用均未验证。基础安装和 CI 不启用它，项目尚不能称为完整 RAG 应用或自主 Agent。

## V0.1 如何工作

1. 将 `.md` 和 `.txt` 笔记写入确定性的本地 JSON 索引。
2. 将一个问题扩展为原始、寻找支持和寻找反证三类查询变体。
3. 使用 BM25 分别检索，再通过 reciprocal-rank fusion（RRF，倒数排名融合）合并结果。
4. 根据可检查的 claim overlap（主张重合度）和 polarity（极性）规则判断关系。
5. 返回 citation；如果缺少置信度足够的定向证据，则 abstain。

这条 pipeline 有意保持简单。失败可以复现、检查和度量，不会被藏在不可见的模型调用后面。详见[架构说明](docs/architecture.md)和[设计决策](docs/design-decisions.md)。

## 为什么 Eval 是产品的一部分

原先的 4-case 展示层 regression 看起来是满分。把 classification Eval 与每类只展示一条结果的 presentation cap 分离之后，同一套 fixture 的 classification exact 只有 2 / 4，但 CLI presentation 仍是 4 / 4。另一套预先冻结的 20-case adversarial benchmark（对抗性基准）继续暴露更难的失败模式。

| 数据集或指标 | 修正后的 V0.1 结果 |
|---|---:|
| 4-case classification exact | 2 / 4 — 仅用于 regression |
| 4-case presentation exact | 4 / 4 |
| Frozen adversarial exact cases | 8 / 20 |
| Relation precision | 0.4737 |
| Relation recall | 0.4286 |
| Relation F1 | 0.4500 |
| Relation macro F1 | 0.3621 |
| False counter rate | 0.5000 |
| Counter recall | 0.1250 |
| RELATED contamination | 0.7500 |
| RELATED recall | 0.2500 |
| Abstention accuracy | 0.6500 |
| Abstention balanced accuracy | 0.5000 |
| Citation span integrity | 1.0000 |

修正后的 Eval 会在 presentation cap 之前评分所有 retrieved 且非 `IRRELEVANT` 的分类结果，因此原本会被 top-one 展示策略隐藏的 false positives 现在会进入指标；`presentation_exact_case_rate` 仍单独保留，作为 UI regression 信号。冻结 benchmark 仍然显示反证召回率低、方向标签误判、RELATED 污染和较差的 balanced abstention。

这些数字不是质量成功声明。项目把 Eval 输入、原始输出和 failure analysis 当作一等工程产物，让下一步技术决策基于已经观察到的失败，而不是基于一个完美的 Demo 分数：

- 冻结的 [adversarial Gold](reports/release-review/adversarial-gold.json)；
- V0.1 [原始结果](reports/release-review/adversarial-results.json)；
- 历史[发布审查与失败分析](reports/release-review/public-release-candidate-review.md)；
- [Eval 方法](docs/eval-methodology.md)。

## 已知限制

- 关系分类仍是词法和启发式规则；implicit counter-evidence（隐含反证）、mixed stance（混合立场）、反讽和复杂否定经常判断失败。
- 分词支持 ASCII 单词和确定性的汉字重叠双字切分；不提供中文词典分词、同义词匹配或中文语义关系判断。
- 没有动态二次检索或 Agent Loop。
- 尚未验证大规模语料上的性能。
- 真实用户价值、私人阅读数据上的效果尚未验证。

## 使用自己的评测数据

公开项目默认不会发现或读取 private corpus。需要运行本地 benchmark 时，必须显式传入路径：

```bash
.venv/bin/reading-evidence ingest path/to/corpus --index path/to/local-index.json
.venv/bin/reading-evidence eval \
  --index path/to/local-index.json \
  --questions path/to/questions.json \
  --dataset path/to/gold.json \
  --output path/to/untracked-results.json
```

Private corpus、索引、Gold labels 和输出都必须放在仓库之外。详见[隐私边界](docs/privacy.md)和[Eval 方法](docs/eval-methodology.md)。

## 项目状态

当前 V0.1：

- deterministic lexical/polarity baseline；
- 可复现的公开 Demo；
- 冻结的 adversarial benchmark 与 failure analysis；
- citation、trace 和 abstention 行为；
- 可替换的判断器契约和离线四分类候选演示；
- 仅有模拟响应测试的实验性模型适配器。

后续可能验证的方向，不代表承诺：

- semantic relation judgment（语义关系判断）；
- 根据证据质量决定是否进行动态二次检索；
- 多语言检索；
- private real-world benchmark。

Web UI、vector database 基础设施、multi-agent orchestration、用户账号和 cloud SaaS 仍不在当前范围内。

## 参与贡献

请先阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 和 [relation annotation guide](docs/relation-annotation-guide.md)。当前提交的 20-case adversarial set 只用于 regression；在单独的 blind/holdout Eval 于首次系统运行前完成冻结之前，不应把它用于 semantic-judge model selection。
