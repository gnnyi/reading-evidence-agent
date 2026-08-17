# Evaluation methodology

The public Eval is deliberately small and synthetic. It verifies behavior and reproducibility; it does not establish production quality.

## Evaluation unit

Each unit contains:

- a question ID and question;
- expected note-to-relation assignments;
- an expected abstention decision.

The runner reports relation precision, recall, F1, exact-case rate, abstention accuracy, and citation coverage. Exact-case rate requires both the full relation set and abstention decision to match.

## Public demo scope

The demo covers:

- a claim with both support and counter-evidence;
- related but non-directional material;
- a question with no corpus evidence, which must abstain.

Because the corpus and labels are synthetic, public scores are regression checks for this repository only. They must not be presented as evidence of performance on personal reading data.

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
