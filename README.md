[English](README.md) | [简体中文](README.zh-CN.md)

# Reading Evidence Agent

Explore whether your notes **support a claim, challenge it, or are only related**—with source-line citations and an inspectable decision trace.

A small, offline command-line baseline for developers exploring evidence retrieval and evaluation. It uses BM25 + RRF retrieval and deterministic relation rules; no API key or runtime dependencies are needed. Despite the name, it does not generate answers or run an autonomous agent loop.

**Current limit:** relation judgment is unreliable on harder language: the public adversarial regression has **8/20 exact cases and F1 0.45**. Use this to inspect and improve evidence retrieval, with human review of each conclusion. [Evidence and limits →](docs/evidence.md)

## When to try it

- **Inspect a claim against short notes:** for example, “Should I treat a failed experiment as wasted time?” Read the supporting passage, the counterpoint, and the related context side by side.
- **Debug a retrieval experiment:** use the trace to see whether a passage was missed, mislabeled, or removed from the display.
- **Contribute a reproducible failure:** turn a wrong relation or poor citation into a small public fixture before changing a judge.

Reliable automatic research synthesis and large personal knowledge libraries are not validated use cases. Start with the public English examples; Chinese retrieval exists, but Chinese semantic judgment is unverified.

## Run your first example

Requires Git and Python 3.10+. These commands use a macOS/Linux shell. Installation may download build dependencies; the default runtime is local.

```bash
git clone https://github.com/gnnyi/reading-evidence-agent.git
cd reading-evidence-agent
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/reading-evidence ingest demo/corpus
.venv/bin/reading-evidence ask "Should I treat a failed experiment as wasted time?"
```

On Windows PowerShell, create the environment with `py -3 -m venv .venv`, then use `.venv\Scripts\python.exe` and `.venv\Scripts\reading-evidence.exe` in place of the Unix executable paths. This candidate's Windows path has not been runtime-verified.

Expected output, abbreviated; the CLI also prints excerpts, confidence scores, sources, and a trace:

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

Read the quoted lines yourself. The support citation above selects a heading; a valid source line is not necessarily the best evidence.

To compare more passages, add `--max-per-relation 3`. The default shows one item per relation; increasing the limit reveals more existing evidence without changing retrieval or abstention.

**Next:** follow the [three-sample walkthrough](docs/walkthrough.md) to see a success, an abstention, and a known wrong judgment. If installation fails, [report the failing step](https://github.com/gnnyi/reading-evidence-agent/issues/new?template=bug_report.md); a failed first run is useful feedback too.

For a small, reproducible engineering example, see [how a display limit hid retrieved evidence](docs/case-study-display.md). It includes the before/after commands and the failures this change does not fix.

<details>
<summary>If installation cannot download build dependencies</summary>

From the cloned repository, Python alone can run the source version:

```bash
PYTHONPATH=src python3 -m reading_evidence.cli ingest demo/corpus
PYTHONPATH=src python3 -m reading_evidence.cli ask "Should I treat a failed experiment as wasted time?"
```

For later commands, replace `.venv/bin/reading-evidence` with `PYTHONPATH=src python3 -m reading_evidence.cli`. This verifies the source runtime, not package installation. [Walkthrough](docs/walkthrough.md)

</details>

## Check the technical evidence

After ingesting the demo:

```bash
.venv/bin/reading-evidence eval --questions demo/questions.json --dataset demo/gold.json
.venv/bin/reading-evidence judge-eval --dataset demo/judge-cases.json --judge lexical
```

| Check | Observed baseline | What it means |
|---|---|---|
| Public pipeline fixture | 2/4 classification-exact; 4/4 presentation-exact | Display trimming can hide false positives |
| Frozen adversarial regression | 8/20 exact; relation F1 0.45 | Harder relation judgments often fail |
| Fixed-candidate tutorial | 4/4 labels; 2/3 expected evidence spans | Correct labels and real quotes do not ensure good evidence selection |

All three datasets are synthetic, known examples. [Full results and limitations](docs/evidence.md) · [Metric definitions](docs/eval-methodology.md) · [CI](https://github.com/gnnyi/reading-evidence-agent/actions)

## Try your notes, or contribute without coding

Try one actual question against 3–5 short notes stored **outside this repository**, inspect the result, and record whether it helped. The [feedback guide](docs/feedback.md) includes local commands and a short report format. Do not upload private notes, indexes, or raw traces to an issue.

- [Share a first-use result](https://github.com/gnnyi/reading-evidence-agent/issues/new?template=first_use.md), including failures or a result that was not useful. English and Chinese are welcome.
- [Report a reproducible bug](https://github.com/gnnyi/reading-evidence-agent/issues/new?template=bug_report.md).
- Pick a [starter task with acceptance criteria](docs/starter-issues/README.md), or propose a public failure case using the [contribution guide](CONTRIBUTING.md).

## Project map

[Architecture](docs/architecture.md) · [Design decisions](docs/design-decisions.md) · [Privacy](docs/privacy.md) · [Contributing](CONTRIBUTING.md) · [MIT license](LICENSE)

The next decision is which failures real users encounter and whether this workflow helps them. External adoption remains unverified. See the [feedback process](docs/feedback.md) and [release readiness record](docs/release-readiness.md).
