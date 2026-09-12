[English](README.md) | [简体中文](README.zh-CN.md)

# Reading Evidence Agent

检查笔记中的材料是在**支持一个观点、挑战它，还是仅仅相关**，并查看原文行级引用与判断过程。

这是面向证据检索与评测实验的小型离线命令行基线。它使用 BM25 + RRF 检索和确定性的关系规则，无需 API key 或第三方运行依赖。虽然名称中有 Agent，目前没有回答生成或自主智能体循环。

**当前限制：**复杂表达下的关系判断不可靠，公开对抗回归集仅 **8/20 完全正确，F1 为 0.45**。适合用来检查和改进检索，每个结论仍需人工复核。[查看证据与限制 →](docs/evidence.md)

## 什么时候值得试

- **用短笔记核对一个观点：**例如“失败的实验是否就是浪费时间？”并排阅读支持、反对和相关背景材料。
- **排查检索实验：**查看原文是没被检索到、被分错关系，还是在展示时被裁掉。
- **贡献可复现的失败：**把错误关系或不合适的引用整理成小型公开样例，再考虑修改判断器。

自动可靠地综合研究结论、处理大型个人知识库，仍是未验证的场景。请先运行公开英文样例；支持中文检索分词，不代表中文语义判断已验证。

## 跑通第一个例子

需要 Git 与 Python 3.10+。以下命令适用于 macOS/Linux 终端。安装可能下载构建依赖，默认运行过程在本地完成。

```bash
git clone https://github.com/gnnyi/reading-evidence-agent.git
cd reading-evidence-agent
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/reading-evidence ingest demo/corpus
.venv/bin/reading-evidence ask "Should I treat a failed experiment as wasted time?"
```

Windows PowerShell 用 `py -3 -m venv .venv` 创建环境，再将命令中的可执行路径换成 `.venv\Scripts\python.exe` 和 `.venv\Scripts\reading-evidence.exe`。本候选版本尚未实测 Windows 路径。

预期输出节选；完整输出还包含摘录、规则分数、来源和判断追踪：

```text
SUPPORT
  [failed-experiment-waste] When a failed experiment is wasted
  Citation: failed-experiment-waste.md#L1
COUNTER_EVIDENCE
  [failed-experiment-learning] Failure can buy information
  Citation: failed-experiment-learning.md#L3
RELATED
  [experiment-preregistration] Pre-register the learning condition
  Citation: experiment-preregistration.md#L3
NO_EVIDENCE / ABSTAIN: NO
```

请打开引用行阅读原文。上面的支持引用选中了标题；地址有效，不代表选到了最合适的证据。

需要比较多条材料时，可在提问命令后加 `--max-per-relation 3`。默认每类展示一条；提高上限只显示更多已有证据，不改变检索结果或拒答判断。

**下一步：**按[三个样本的演示](docs/walkthrough.md)查看一次成功、一次拒答和一次已知错误。安装遇到问题时，[报告失败步骤](https://github.com/gnnyi/reading-evidence-agent/issues/new?template=bug_report.md)即可；首次运行失败也是有价值的反馈。

想核验一个具体工程改动，可看[展示上限如何隐藏已检索证据](docs/case-study-display.md)：包含改动前后的复现命令，以及这次改动无法解决的错误。

<details>
<summary>安装时无法下载构建依赖</summary>

在克隆后的仓库中，只用 Python 也能直接运行源码：

```bash
PYTHONPATH=src python3 -m reading_evidence.cli ingest demo/corpus
PYTHONPATH=src python3 -m reading_evidence.cli ask "Should I treat a failed experiment as wasted time?"
```

后续命令可将 `.venv/bin/reading-evidence` 替换成 `PYTHONPATH=src python3 -m reading_evidence.cli`。这只能验证源码运行，不代表安装验证通过。[继续演示](docs/walkthrough.md)

</details>

## 核对技术证据

导入示例语料后运行：

```bash
.venv/bin/reading-evidence eval --questions demo/questions.json --dataset demo/gold.json
.venv/bin/reading-evidence judge-eval --dataset demo/judge-cases.json --judge lexical
```

| 检查 | 当前基线结果 | 能说明什么 |
|---|---|---|
| 公开流程样例 | 分类完全正确 2/4；展示完全正确 4/4 | 展示裁剪可能隐藏误报 |
| 冻结对抗回归集 | 完全正确 8/20；关系 F1 为 0.45 | 复杂关系判断经常失败 |
| 固定候选教学样例 | 标签正确 4/4；预期证据片段命中 2/3 | 标签正确、引用真实，也可能没有选好证据 |

三套数据都是已知的合成样例。[完整结果与边界](docs/evidence.md) · [指标定义](docs/eval-methodology.md) · [持续集成检查](https://github.com/gnnyi/reading-evidence-agent/actions)

## 试自己的笔记，或不写代码也能贡献

将 3～5 条短笔记放在**仓库外**，提出一个真实问题，读完结果后记录是否有帮助。[反馈指南](docs/feedback.md)提供本地命令和简短报告格式。请勿把私人笔记、索引或原始追踪结果上传到 Issue。

- [提交首次使用反馈](https://github.com/gnnyi/reading-evidence-agent/issues/new?template=first_use.md)：失败或“不值得继续用”同样欢迎，支持中英文。
- [报告可复现的问题](https://github.com/gnnyi/reading-evidence-agent/issues/new?template=bug_report.md)。
- 选择一个[带验收条件的入门任务](docs/starter-issues/README.md)，或按[贡献指南](CONTRIBUTING.md)提供公开失败样例。

## 继续了解

[架构](docs/architecture.md) · [设计决策](docs/design-decisions.md) · [隐私边界](docs/privacy.md) · [贡献指南](CONTRIBUTING.md) · [MIT 许可证](LICENSE)

下一步取决于真实用户遇到哪些失败，以及这套流程是否有用。外部采用仍未验证，见[反馈流程](docs/feedback.md)与[发布就绪记录](docs/release-readiness.md)。
