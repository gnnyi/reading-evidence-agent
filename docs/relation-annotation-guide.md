# Relation annotation guide

This guide defines how public benchmark labels should be proposed and reviewed. It is an annotation contract, not a claim that the V0.1 lexical classifier can reliably make these distinctions.

## Unit of judgment

Annotate the relationship between a **question/claim** and a specific **evidence span** in a candidate note. The current V0.1 system emits one note-level relation, but Gold rationale should still name the span that justifies the label. This prevents a heading or nearby sentence from standing in for the evidence actually being judged.

Candidate relations used in Gold are `SUPPORT`, `COUNTER_EVIDENCE`, and `RELATED`. `IRRELEVANT` is an internal classifier outcome and is represented in Gold by omitting that note from `expected_relations`. `ABSTAIN` is a question-level decision, not a note relation.

## SUPPORT

Use `SUPPORT` when the evidence span gives directional evidence for the claim as written. The wording need not be identical, but the relevant subject, predicate, scope, and polarity must line up.

Do not label a note `SUPPORT` merely because it shares a topic or repeats a noun phrase from the claim.

## COUNTER_EVIDENCE

Use `COUNTER_EVIDENCE` when the evidence span contradicts the claim or materially weakens a scope/strength that the claim commits to.

A qualification is counter-evidence only when it matters to the proposition being evaluated. For example:

- Claim: “Method X always improves recall.” Evidence: “Method X did not improve recall under condition Y.” → `COUNTER_EVIDENCE` because the exception defeats “always”.
- Claim: “Method X can improve recall.” Evidence: “Method X is slower to administer.” → normally `RELATED`; the cost does not negate the stated possibility of improvement.

Annotators should write which predicate, quantifier, condition, or causal claim is being contradicted.

## RELATED vs IRRELEVANT

Use `RELATED` when a span is useful context for the same question but does not provide directional evidence for or against the claim.

Omit a note as `IRRELEVANT` when its overlap is merely topical, lexical, or incidental and would not help a careful reader evaluate the claim.

A practical test is: if the claim's truth changed, would this span become more or less plausible as a result? If not, ask whether the span still contributes concrete context needed to evaluate the claim. If neither is true, it is `IRRELEVANT`, not `RELATED`.

Do not use `RELATED` as a catch-all for every retrieved candidate.

## Mixed-stance notes

A single note may contain both support and counter-evidence. Record the exact supporting and counter spans before assigning a note-level Gold label.

For ordinary regression cases, prefer a note whose intended relation is unambiguous. If mixed stance is the behavior under test, the case rationale must state:

- both relevant spans;
- why one note-level label is expected under the current benchmark contract;
- what information is lost by reducing the note to one label.

If two reasonable annotators select different dominant relations, treat the case as ambiguous until adjudicated; do not resolve it by looking at system output.

## Quotation, attribution, and negation

Quoted text is not automatically the note author's position. Annotate the proposition asserted by the evidence span, including attribution when attribution changes the meaning.

Examples:

- “The paper claims X, but the replication found no effect.” The quoted `X` is not support from the note as a whole; the replication clause may be `COUNTER_EVIDENCE`.
- “No evidence shows X improves Y.” is negative evidence about the evidential claim; do not strip `no` and label it as support for “X improves Y”.
- Double negation, scoped negation, irony, and reported speech should be marked as potentially ambiguous when the intended polarity is not explicit.

For cases involving negation, the rationale must copy the exact span and name the negation target.

## Abstention labels

Set `expected_abstain: true` when the evaluated corpus contains no sufficiently justified directional evidence under the benchmark contract. A corpus can contain `RELATED` notes and still require abstention.

Do not set abstention from the system's confidence score. Gold abstention is a human judgment about available evidence, independent of the current implementation.

## Independent annotation and adjudication

For any benchmark intended to compare semantic judges or other capability variants:

1. Freeze the question and corpus before system evaluation.
2. Have at least two annotators label independently without seeing candidate-system outputs.
3. Record the evidence span and rationale for each directional/RELATED label.
4. Adjudicate disagreements before the first model-selection run.
5. Record unresolved ambiguity instead of forcing agreement.
6. Hash the final question, corpus, and Gold artifacts when they are frozen.

A label changed after inspecting system output invalidates that benchmark version as a blind model-selection holdout. Corrections should create a new version with a written reason rather than silently rewriting the frozen Gold.

## Current 20-case benchmark

`reports/release-review/adversarial-*` is a **frozen regression suite**, not a blind holdout. It is useful for detecting behavioral regressions and reproducing known failure modes. It must not be used to select a semantic judge or tune its thresholds because the cases and failures are already known to the project.

Until a separately assembled blind/holdout Eval exists, semantic-judge experiments are exploratory and cannot claim holdout improvement.
