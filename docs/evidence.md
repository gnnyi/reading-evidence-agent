# Evidence and limits

The default path is a deterministic, offline retrieval baseline. The public fixtures are synthetic and already inspected. They support reproducibility claims, not generalization or user-value claims.

## What to trust

| Claim | Evidence | Limit |
|---|---|---|
| The base CLI can run locally without a model key | [CI workflow](../.github/workflows/ci.yml), [walkthrough](walkthrough.md) | Installation may download build dependencies; local onboarding checks are recorded in [release readiness](release-readiness.md) |
| Retrieval and judgments can be inspected separately | [Architecture](architecture.md), `trace.candidates`, `trace.candidate_decisions`, `judge-eval` | No ablation establishes that multi-query RRF beats a simpler query |
| Citations point to original source lines | [Candidate demo](../demo/judge-cases.json), [evaluation definitions](eval-methodology.md) | Source fidelity does not prove semantic support; a heading can be a valid but unhelpful citation |
| Failures are reproducible | [Frozen results](../reports/release-review/adversarial-results.json), [runner](../reports/release-review/run-adversarial-review.py) | This is a known regression set, not a blind holdout |
| External users benefit or return | No confirmed evidence recorded for this candidate | [Feedback process](feedback.md); do not infer adoption from stars, traffic, CI, or maintainer runs |

## Why Eval is part of the product

The original four-case presentation-level regression looked perfect. After separating classification evaluation from the one-per-relation presentation cap, the same fixture is only 2 / 4 classification-exact while the CLI presentation remains 4 / 4. The separately frozen 20-case adversarial benchmark continues to expose the harder failure modes.

| Dataset or metric | Corrected V0.1 result |
|---|---:|
| Four-case classification exact | 2 / 4 — regression only |
| Four-case presentation exact | 4 / 4 |
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

The corrected Eval scores all retrieved non-`IRRELEVANT` classifications before the presentation cap. This exposes false positives that the old top-one display policy could hide; `presentation_exact_case_rate` remains available as a UI regression metric. The frozen benchmark still shows weak counter-evidence recall, false directional labels, RELATED contamination, and poor balanced abstention.

These numbers are not a quality claim. Eval inputs, raw outputs, and failure analysis are first-class repository artifacts so that the next technical decision can be based on observed failures rather than a perfect demo score:

- frozen [adversarial Gold](../reports/release-review/adversarial-gold.json);
- V0.1 [raw results](../reports/release-review/adversarial-results.json);
- historical [release review and failure analysis](../reports/release-review/public-release-candidate-review.md);
- [evaluation methodology](eval-methodology.md).


## Reading the history

The August 17 [release review](../reports/release-review/public-release-candidate-review.md) assessed commit `b216c94`. Its original scores and missing-feature findings are historical, not a current status report. The table above reflects the corrected baseline; retain the original review as an audit trail.

## Unverified capabilities

The optional DeepSeek adapter has simulated-client tests only. Live SDK compatibility, semantic quality, prompt-injection resistance, latency, and cost are unverified. No generated answers or autonomous retrieval loop are implemented. Large-corpus performance and user value on personal notes remain unverified.

ASCII words and overlapping Han bigrams are supported for retrieval. Chinese semantic relation judgment, synonym matching, and Chinese word segmentation are not established. Confidence values are rule scores, not calibrated probabilities.

For private experiments, pass explicit paths and keep corpus, index, labels, and results outside the checkout. See [privacy](privacy.md) and [evaluation methodology](eval-methodology.md).
