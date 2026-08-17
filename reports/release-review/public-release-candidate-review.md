# Reading Evidence Agent — Public Release Candidate Adversarial Review

Review date: 2026-08-17
Reviewed commit: `b216c949356b96dcce27deb8fb7e92d69e0b0624`
Review mode: independent, report-only, no production edits

## 1. Executive Verdict

**Release decision: NOT_READY.**

The repository has a clean public/private boundary, a small installable package, real BM25/RRF code, explicit relation and abstention schemas, and an honest statement that the public Eval is synthetic. Those are sound engineering choices.

They are not enough for release. Three blockers independently trigger `NOT_READY`:

1. The README commands do not run as written in a clean shell. `python` and bare `reading-evidence` each exit `127`; explicit `.venv/bin/...` commands work.
2. The frozen 20-case adversarial Eval produced Relation F1 `0.4103`, only `8/20` exact cases, False Counter Rate `50%`, Counter Recall `12.5%`, RELATED precision/recall `0%`, and Abstention Accuracy `65%`.
3. A synthetic non-Latin corpus can be ingested but its question cannot be asked because tokenization only retains ASCII letters and digits.

The current project is best described as a transparent lexical retrieval and heuristic relation baseline. It is not yet a credible relation-aware Agent capability and is not ready to occupy a flagship resume position.

## 2. 30-second GitHub Review

**README_VALUE_PROPOSITION: MEDIUM**

The opening question and one-sentence definition explain the intended problem quickly. SUPPORT, COUNTER_EVIDENCE, RELATED, and ABSTAIN are visible above the fold. However, there is no sample output before installation, and the first runnable commands fail in a clean shell. The reader understands the aspiration faster than they can verify the product.

**GENERIC_RAG_DIFFERENTIATION: MEDIUM**

The relation taxonomy and explicit abstention distinguish the product framing from “retrieve similar chunks.” The implementation does not yet establish that distinction in behavior: adversarial counter recall is `1/8`, all three predicted RELATED results are contamination, and query “decomposition” is fixed token expansion rather than a question-dependent plan.

Hiring-review answers:

1. Problem understood in 30 seconds: **yes, at a conceptual level**.
2. Clearly different from Generic RAG: **partly; the taxonomy is different, the demonstrated capability is not yet**.
3. Why multi-query, classification, abstention, and Eval are needed: **classification and abstention are clear; multi-query value is not shown by an ablation; Eval is present but the visible fixture is too curated**.
4. “Built for GitHub” feeling: **material risk**. Four tailored public cases produce 1.0, while the first broader frozen set drops to F1 0.4103.
5. Engineering judgment beyond API assembly: **some**. Local-first design, no runtime dependencies, privacy rules, deterministic traces, and explicit abstention show judgment. The semantic core remains shallow.

## 3. Claim → Evidence Matrix

| Claim | Implementation Evidence | Runtime Verified | Verdict |
|---|---|---:|---|
| local-first | Standard-library imports only; index is local JSON; no network client in runtime source | Yes, corrected fresh-clone CLI works without runtime network calls | VERIFIED |
| multi-query retrieval | `query/decompose.py` returns original/support/counter strings; retrieval runs all three | Yes, trace contains three variants and rankings change | VERIFIED |
| reciprocal-rank fusion | `retrieval/lexical.py` accumulates `1 / (60 + rank)` across queries | Yes, candidates are deduplicated and carry fused scores | VERIFIED |
| SUPPORT | Relation enum and classifier branch exist | Yes, but adversarial precision `53.85%` and recall `77.78%` | PARTIAL |
| COUNTER_EVIDENCE | Opposite local polarity maps to counter | Yes, but precision `50%`, recall `12.5%`, and only two counters were emitted | PARTIAL |
| RELATED | Weak topical overlap maps to related | Yes, but adversarial precision and recall are both `0%` | PARTIAL |
| abstention | Fixed policy requires directional confidence ≥ `0.6` | Yes, but adversarial accuracy is `65%` with seven errors | PARTIAL |
| citation | Every note stores a relative source and emits `source#L<line>` | Yes, coverage `100%`; exact line integrity `94.44%` because evidence on line 5 is cited as line 1 | PARTIAL |
| trace | Query strings, aggregate retrieval counts, dedup count, and selected decisions are returned | Yes, but retrieved candidate identities and rejected classification decisions are absent | PARTIAL |
| Eval runner | Pair precision/recall/F1, exact case rate, abstention, and non-empty citation coverage | Yes; independent recomputation matched | VERIFIED |

Important limitation: “multi-query” is technically true but consists of appending fixed English words to the same core tokens. No public ablation shows that this improves relation retrieval.

## 4. Fresh Clone Verification

Clone source: reachable Git history at the reviewed commit.

| Command / operation | Exit | Result |
|---|---:|---|
| local Git clone | 0 | PASS |
| `python -m venv .venv` from README | 127 | FAIL: `python` is unavailable in the clean shell |
| `python3 -m venv .venv` fallback | 0 | PASS |
| `.venv/bin/pip install -e .` | 0 | PASS |
| bare `reading-evidence ingest demo/corpus` from README | 127 | FAIL: venv executable is not on PATH |
| bare `reading-evidence ask ...` from README | 127 | FAIL |
| bare `reading-evidence eval ...` from README | 127 | FAIL |
| bare `python -m unittest ...` from README | 127 | FAIL |
| `.venv/bin/reading-evidence ingest demo/corpus` | 0 | PASS, nine notes indexed |
| `.venv/bin/reading-evidence ask ...` | 0 | PASS, three relation sections and citations returned |
| `.venv/bin/reading-evidence eval ...` | 0 | PASS, public regression fixtures pass |
| `.venv/bin/python -m unittest discover -s tests -v` | 0 | PASS, 6/6 |
| Python 3.12 wheel/install/tests | 0 | PASS, 6/6 |
| CLI missing-index behavior | 2 | PASS: concise error |
| CLI empty-corpus behavior | 2 | PASS: concise error |
| CLI invalid JSON behavior | 2 | PASS: concise error |
| CLI malformed Gold schema | 1 | FAIL: uncaught `KeyError` traceback |

The statement “synthetic regression fixtures currently pass” is accurate. The stronger README statement that the demo is reproducible is false for the commands as presented.

## 5. Adversarial Dataset

Gold was written before the first adversarial system run and then frozen.

- Cases: `20`
- Synthetic note files: `22`
- Gold SHA-256: `fa85979f9b9c84ddc365a0a2983fefbce814753d8c592770616dc2fea0c55c6f`
- Corpus aggregate hash: `5ab04591d6c48463cbb8e347e68774631b05ba4a094caafc254912e19d11b229`
- Freeze record: `adversarial-freeze.json`
- Raw results: `adversarial-results.json`

Coverage includes mixed stance, qualified statements, negation scope, implicit counter-evidence, same-topic unrelated conclusions, lexical traps, low lexical overlap, multiple claims, evidence absence, irony, quoted claims, three-way relation retrieval, and citation-line integrity.

Each case uses an isolated corpus. This avoids treating content from another test topic as an unlabeled false positive.

## 6. Adversarial Metrics

| Metric | Result |
|---|---:|
| Cases | 20 |
| Exact relation + abstention cases | 8 / 20 |
| Relation Precision | 0.4444 |
| Relation Recall | 0.3810 |
| Relation F1 | 0.4103 |
| False Counter Rate | 0.5000 (1 / 2 predicted counters) |
| Counter Precision | 0.5000 |
| Counter Recall | 0.1250 (1 / 8 expected counters) |
| False Support Rate | 0.4615 (6 / 13 predicted supports) |
| Support Precision | 0.5385 |
| Support Recall | 0.7778 |
| RELATED contamination | 1.0000 (3 / 3 predicted related) |
| RELATED Precision | 0.0000 |
| RELATED Recall | 0.0000 |
| Abstention Accuracy | 0.6500 (13 / 20) |
| Citation Coverage | 1.0000 (18 / 18 non-empty) |
| Citation Integrity | 0.9444 (17 / 18 exact/source-valid) |

Independent recomputation produced `TP=8`, `FP=10`, and `FN=13`, matching the saved metrics.

False Counter deserves extra weight. The system emitted only two counter-evidence results across eight counter cases. One was correct and one was a double-negation false counter. The larger failure is under-generation: implicit, qualified, mixed, and ironic counter-evidence is usually missed or mislabeled.

## 7. Failure Analysis

| Case | Expected | Observed | Failure classification |
|---|---|---|---|
| C01 mixed stance | COUNTER | COUNTER | PASS; explicit negation made this easy |
| C02 qualified persistence | COUNTER | RELATED + abstain | qualified-statement failure, implicit-relation failure, abstention failure |
| C03 negation elsewhere | SUPPORT | SUPPORT | PASS |
| C04 implicit pivot evidence | COUNTER | SUPPORT | false support, implicit counter failure |
| C05 same topic/procedure | RELATED + abstain | SUPPORT + no abstain | false support, same-topic conclusion failure, abstention failure |
| C06 quoted lexical trap | RELATED + abstain | SUPPORT + no abstain | quoted-claim failure, lexical overlap trap, false support |
| C07 low-overlap support | SUPPORT | no result + abstain | retrieval miss, low-overlap failure |
| C08 low-overlap implicit counter | COUNTER | no result + abstain | retrieval miss, implicit relation failure |
| C09 multi-claim speed limit | COUNTER | RELATED + abstain | multiple-claim failure, qualified counter failure |
| C10 absent evidence | abstain | abstain | PASS |
| C11 direct support/citation | SUPPORT | SUPPORT | PASS |
| C12 negation elsewhere | SUPPORT | SUPPORT | PASS |
| C13 mixed positive/negative clauses | COUNTER | SUPPORT | mixed-stance failure, false support |
| C14 double negation | SUPPORT | COUNTER | negation-scope failure, false counter |
| C15 conditional support | SUPPORT | SUPPORT | PASS |
| C16 irony | COUNTER | SUPPORT | irony failure, false support |
| C17 rejected quoted negation | SUPPORT | SUPPORT | PASS; outcome depends on dominant-token counts |
| C18 support/counter/related pool | all three | SUPPORT + counter note as RELATED | implicit counter failure; true RELATED displaced by one-per-relation selection |
| C19 same subject, wrong outcome | RELATED + abstain | SUPPORT + no abstain | lexical overlap trap, false support, abstention failure |
| C20 evidence begins at line 5 | SUPPORT at line 5 | SUPPORT cited at line 1 | citation mismatch |

Failure counts in raw output:

- false support: 6
- related contamination: 3
- retrieval miss: 2
- false counter: 1
- ranking/selection miss: 1
- citation mismatch: 1
- abstention failure: 7

New failure types not adequately represented in the original taxonomy are quoted-claim handling, irony, dominant-clause ambiguity, and citation granularity.

## 8. Agent Worthiness

**AGENT_WORTHINESS: WEAK**

Current execution is:

```text
question
-> fixed token expansions
-> one BM25/RRF retrieval pass
-> one heuristic classification pass
-> fixed one-per-relation selection
-> fixed abstention threshold
```

There is no observation-action loop, no evidence-quality judgment that changes the next tool call, and no second retrieval. The current artifact is a deterministic pipeline, not an Agent in the engineering sense.

A future dynamic loop could be justified at two points:

1. detect that support or counter coverage is missing/ambiguous, then choose a second retrieval strategy;
2. inspect contradictions and evidence quality, then decide whether to retrieve again, abstain, or answer.

Initial query normalization, lexical retrieval, deduplication, citation formatting, and most metric computation are better kept deterministic. Relation classification may need a stronger semantic component, but a model call alone would still not create an Agent loop.

## 9. Generic RAG Differentiation

The product thesis is differentiated; the current capability is not yet.

Positive evidence:

- relations are first-class output fields rather than prose decoration;
- counter-evidence and abstention are explicit;
- the Eval schema scores relation pairs and abstention separately;
- trace and citation contracts are visible.

Contrary evidence:

- retrieval is ordinary lexical BM25/RRF;
- support/counter query variants append fixed words to identical core tokens;
- classification is token overlap plus a three-token negation window;
- adversarial RELATED behavior is unusable and counter recall is `12.5%`;
- no ablation shows that multi-query beats original-query retrieval;
- no public failure report currently appears in the README.

The current repository demonstrates a useful Eval framing around a conventional retrieval baseline. It does not yet demonstrate a reliable Reading Evidence Agent.

## 10. Privacy / Secrets Review

**PRIVACY: PASS**

Reviewed surfaces:

- tracked working tree and review artifacts;
- reachable Git history and unreachable-object check;
- commit author and email;
- repository-local Git configuration;
- filenames, README, docs, demo, tests, and package metadata;
- common credential, token, private-key, email, phone, absolute-path, database, embedding, and private-project marker patterns.

Results:

- no private corpus, real personal question, account identifier, local absolute path, personal email, phone number, or credential value found;
- commit identity is the generic project identity `Reading Evidence Agent <noreply@reading-evidence.local>`;
- repository-local identity overrides a global identity that exists outside the repository;
- no unreachable Git objects were reported;
- database and embedding terms occur only in denylist/documentation context;
- ignored local environments contain normal generated absolute paths but are not tracked and are covered by `.gitignore`.

`gitleaks` and `detect-secrets` are not installed. They were not installed for this review. Secrets status is therefore **regex scan only, with TOOLING_LIMITATION**, not a complete secrets audit.

## 11. Repository Hygiene

| Check | Verdict | Evidence |
|---|---|---|
| LICENSE | PASS | MIT file present |
| package metadata | PASS | wheel and editable install succeed |
| Python version claim | PARTIAL | 3.12 and 3.14 pass; 3.10/3.11/3.13 unavailable for verification |
| `.gitignore` | PASS | venv, index, caches, package metadata, databases, vectors, and env files ignored |
| tests | PARTIAL | 6 focused tests pass; fixtures are highly tailored and no adversarial suite is part of production |
| docs | PASS_WITH_CONCERNS | architecture/privacy/Eval decisions are clear; runnable commands are wrong for a clean shell |
| dead code | FAIL_LOW | `has_negation()` remains defined with no caller |
| generated files | PASS | caches, editable metadata, venv, and local index are ignored, not tracked |
| large binaries | PASS | no tracked file exceeds 1 MB; no binary artifact found |
| dependencies | PASS | no runtime dependency; build requires setuptools |
| README links | PASS | all three relative links resolve |
| CLI help | PASS | commands and help render |
| common CLI errors | PARTIAL | missing files/empty corpus/invalid JSON are clean; malformed Gold schema leaks a traceback |
| CI | ABSENT | no automated workflow verifies clean install or supported versions |

Additional technical risk: tokenization uses `[a-z0-9]+`. A synthetic non-Latin note ingests, but a non-Latin question exits `2` with “Question must contain at least one meaningful token.” The README does not declare an English-only constraint.

Performance is also unproven. Each question reloads the JSON index, tokenizes every document for each query, and recomputes document frequencies. This is acceptable for nine demo notes but not evidence of readiness for a large reading corpus.

## 12. GitHub Value

Current GitHub value is mostly in the framing and auditability:

- clear relation taxonomy;
- explicit abstention and citations;
- small codebase that can be read end to end;
- no framework inflation;
- synthetic Eval contract and failure vocabulary.

The presentation weakness is that the repository currently invites the reviewer to trust a four-case 1.0 regression set. The README is honest about its limits, but it does not show the broader failure baseline, an ablation, or a real-world result. A hiring reviewer will likely summarize it as “BM25/RRF plus polarity rules and tailored synthetic fixtures.”

## 13. Resume Value

**PUBLIC_ONLY_RESUME_VALUE: WEAK**

As a public-only project, it is too small and too weak on its central semantic claim for a flagship position. It can support a bullet about evaluation-first prototyping, privacy boundaries, and transparent baselines, but it should not lead the project section.

**WITH_PRIVATE_BENCHMARK_RESUME_VALUE: STRONG**

A large real-world corpus, human-labeled current questions, a frozen before/after comparison, honest counter-evidence failures, and measurable improvements would change the signal. The value would come from product problem selection, Eval design, privacy-safe public extraction, failure-driven iteration, and evidence that semantic relation retrieval works beyond fixtures. Corpus size alone would not create that value.

## 14. Release Blockers

1. **README commands are not reproducible as written.** This independently blocks release under the supplied criteria.
2. **Core relation quality fails the frozen adversarial baseline.** F1 `0.4103`, False Counter `50%`, Counter Recall `12.5%`, and RELATED precision/recall `0%` do not support the central claim.
3. **Abstention is not trustworthy.** Seven of twenty decisions are wrong, including failures to abstain on same-topic unrelated content and unjustified abstention on implicit evidence.
4. **The public/private benchmark interface is language-incomplete.** Non-Latin questions cannot be tokenized, and no language limitation is declared.
5. **“Agent” overstates current behavior.** No dynamic second retrieval or evidence-quality loop exists.
6. **Citation line precision is false.** Every note starts at line 1 even when the cited claim begins later.

Secondary issues:

- trace omits retrieved candidate identities and rejected relation decisions;
- malformed Eval schema produces an uncaught traceback;
- no CI verifies the install path or Python support claim;
- dead negation helper remains;
- no multi-query ablation demonstrates value.

## 15. Recommended Next Action

Return the project to the Developer track. Do not add an Agent framework yet.

The next release candidate should be judged against three gates:

1. exact README commands pass in a clean shell on declared Python versions;
2. a newly frozen adversarial Eval demonstrates materially better counter precision/recall, RELATED behavior, and abstention without editing this Gold after seeing results;
3. the public scope explicitly matches supported languages and the repository name/README accurately distinguish a deterministic baseline from any later dynamic Agent loop.

Private benchmark evidence should be added only after the public pipeline can represent its input language and the human-label contract is complete.
