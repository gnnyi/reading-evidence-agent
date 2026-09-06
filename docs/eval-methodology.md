# Evaluation methodology

The public Eval is deliberately small and synthetic. It verifies behavior and reproducibility; it does not establish production quality.

## Evaluation unit

Each unit contains:

- a question ID and question;
- expected note-to-relation assignments;
- an expected abstention decision.

The runner scores every retrieved non-`IRRELEVANT` classification before the CLI presentation cap is applied. It reports micro and macro relation precision/recall/F1, per-class counts and metrics, paired false-rate/recall metrics for `SUPPORT`, `COUNTER_EVIDENCE`, and `RELATED`, abstention accuracy plus precision/recall/specificity/balanced accuracy, citation coverage/integrity, and exact-case rate. Exact-case rate requires both the full uncapped relation set and abstention decision to match. `presentation_exact_case_rate` is reported separately as a CLI/output regression signal.

Gold must contain at least one case. A zero-prediction class reports undefined precision as `null` and still reports recall, so suppressing a relation cannot masquerade as a perfect false-positive rate. `IRRELEVANT` is an internal classifier outcome rather than a Gold evidence label.

For the default lexical pipeline, `citation_integrity` checks source-line location plus consistency with explicit overlap/polarity rules. With a non-lexical judge, pipeline Eval checks source-line location; exact quotes are checked by the answer path when the judge declares `exact_quote`. Neither metric is a human entailment score. Do not compare the same metric name across judges as if it measured the same semantic property.

## Candidate-level evaluation

`judge-eval` fixes each question/note pair and bypasses query rewriting, retrieval, and display trimming. Its unit is a four-class classification, including `IRRELEVANT`. Errors have no predicted label, remain in the accuracy denominator, and count as a false negative for the expected class. Invalid JSON/dataset contracts stop before judging.

The [four-pair CLI demo](../demo/judge-cases.json) projects Q01's three existing public note labels and one irrelevant Q04/note pair from `demo/questions.json`, `demo/gold.json`, and `demo/corpus`. Expected spans point to substantive line 3. This is an inspectable tutorial fixture, not an independently annotated benchmark, a holdout, or the pending human-approved semantic experiment.

Candidate metrics separate:

- relation accuracy and per-class precision/recall/F1;
- `schema_valid_rate`: judgment structure, including null evidence for `IRRELEVANT`;
- `citation_integrity`: complete single-line quote equals the supplied source line, over non-`IRRELEVANT` outputs only;
- `gold_evidence_match_rate`: expected line and expected quote occur in an exact source quote, over non-`IRRELEVANT` gold cases;
- latency, observed token usage, request/retry counts, and errors. Missing usage observations are not verified zero-cost provider calls.

The offline demo matches 4/4 relation labels, quotes 3/3 real source lines, but matches only 2/3 expected evidence spans: the support quote selects a heading. This demonstrates why classification, source fidelity, and semantic support must be assessed separately. None of these mechanical citation metrics independently proves that an excerpt supports the relation. Model self-grading is not independent correctness evidence. The model adapter has only simulated tests; their fabricated usage is test data, never real provider measurements.

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
