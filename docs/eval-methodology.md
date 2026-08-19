# Evaluation methodology

The public Eval is deliberately small and synthetic. It verifies behavior and reproducibility; it does not establish production quality.

## Evaluation unit

Each unit contains:

- a question ID and question;
- expected note-to-relation assignments;
- an expected abstention decision.

The runner scores every retrieved non-`IRRELEVANT` classification before the CLI presentation cap is applied. It reports micro and macro relation precision/recall/F1, per-class counts and metrics, paired false-rate/recall metrics for `SUPPORT`, `COUNTER_EVIDENCE`, and `RELATED`, abstention accuracy plus precision/recall/specificity/balanced accuracy, citation coverage/integrity, and exact-case rate. Exact-case rate requires both the full uncapped relation set and abstention decision to match. `presentation_exact_case_rate` is reported separately as a CLI/output regression signal.

Gold must contain at least one case. A zero-prediction class reports undefined precision as `null` and still reports recall, so suppressing a relation cannot masquerade as a perfect false-positive rate. `IRRELEVANT` is an internal classifier outcome rather than a Gold evidence label.

`citation_integrity` is a deterministic contract check, not a human entailment score: the citation must resolve to the indexed source line and that line must be relation-consistent with the baseline's explicit overlap/polarity rules. A wrong-polarity span therefore fails even when its file and line address are valid.

## Public demo scope

The demo covers:

- a claim with both support and counter-evidence;
- related but non-directional material;
- a question with no corpus evidence, which must abstain.

Because the corpus and labels are synthetic, public scores are regression checks for this repository only. They must not be presented as evidence of performance on personal reading data.

## Regression set vs blind holdout

The committed 20-case adversarial benchmark is a regression suite, not a blind model-selection holdout. Its cases, failure modes, and current outputs are already known. It may be used to detect regressions and to reproduce known weaknesses, but not to choose a semantic judge, tune semantic thresholds, or claim blind generalization.

A future capability holdout must be assembled, independently annotated/adjudicated, and frozen before the first candidate system is run. See [relation annotation guide](relation-annotation-guide.md).

## Private benchmark interface

The same runner accepts explicit `--index`, `--questions`, and `--dataset` paths. Private inputs and outputs must stay outside the repository and remain untracked. Public and private results should be reported separately.

## Failure taxonomy

- retrieval miss;
- ranking miss;
- query abstraction mismatch;
- false support;
- false counter-evidence;
- related contamination;
- unjustified abstention;
- failure to abstain;
- corpus genuinely lacks evidence;
- ambiguous or unstable human label.
