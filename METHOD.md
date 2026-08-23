# Universal Verified Research Method (UVRM) v1

This is the default method for all research, engineering, mathematics, benchmarking, solver development, and scientific investigation in this repository unless a project explicitly freezes a stricter protocol.

It has two coupled loops:

1. **Object loop** — improve the thing being investigated.
2. **Method loop** — improve how the investigation itself is conducted when evidence shows the current method is inadequate.

The method is not a claim that every problem is finite or that every failure can be diagnosed perfectly. Its purpose is to prevent common epistemic errors: confusing search failure with impossibility, changing representations prematurely, optimizing invalid metrics, retaining noncausal improvements, and rewriting methodology after seeing protected outcomes.

---

## 0. Constitutional core

These rules are not ordinary heuristics. They may be changed only under an explicit constitutional-amendment protocol with independent justification.

1. **Reality decides.** External verifiers, measurements, proofs, counterexamples, tests, or protected outcomes outrank narrative preference.
2. **Evidence is monotone.** Later interpretation may change; historical observations, failures, nulls, rejected candidates, hashes, and provenance are not rewritten.
3. **Not found != unreachable != unselectable != inexpressible.** Distinguish search, capability, representation, and constructor failure.
4. **Apparatus validity is upstream.** Infrastructure/measurement failure is not scientific evidence.
5. **Objective validity is upstream.** Do not optimize a proxy whose alignment with the real target is unestablished.
6. **Closure before invention.** Before adding a representation/operator/object, inspect whether the needed distinction already exists or can be composed from existing structure.
7. **Absence requires a frozen boundary.** Failure to generate a move is evidence only relative to a declared and auditable search basis/budget.
8. **Success is provisional.** A positive result must survive causal attack, ablation or matched controls before retention.
9. **Transfer and reconstruction matter.** A retained structure is stronger evidence when it transfers and cannot be cheaply reconstructed from the same raw history under matched budget.
10. **Protected outcomes never flow backward.** No test definition, equivalence rule, generator boundary, expected interpretation, or attribution rule may be changed using protected outcome knowledge.
11. **Claims track controls.** The strongest claim is bounded by the weakest relevant rival/control defeated.
12. **The method is itself falsifiable.** Method changes are hypotheses and require prospective evidence.

---

## 1. Research state

Every active programme should be representable, at least approximately, as:

`S = (G, V, A, F, R, H, Q, X, K, B, E, M)`

where:

- `G` — real goal and operational metric;
- `V` — verifier / deciding authority;
- `A` — apparatus and measurement validity;
- `F` — current frame / representation;
- `R` — sharpest residual(s);
- `H` — live rival explanations;
- `Q` — current question / deciding experiment;
- `X` — supplied scaffolds and hidden assumptions;
- `K` — retained verified structures, laws, macros, representations;
- `B` — resource budget vector;
- `E` — immutable evidence ledger;
- `M` — current revisable method policy.

When asked "are you doing the process?", report the current state, current lifecycle/mode, why that mode is warranted, and the condition that would switch it.

---

## 2. Two-axis controller

### Lifecycle — what stage are we in?

- `REPAIR` — apparatus, data, measurement, runner, or objective must be repaired/audited.
- `DISCOVER` — generate/test candidate explanations or moves.
- `VERIFY` — run a frozen separator or causal gate.
- `TRANSFER` — test held-out regimes/domains/problems.
- `RETAIN` — admit a surviving mechanism into persistent state.

### Epistemic mode — how should we reason now?

- `EXPLOIT` — push the strongest current approach while it continues producing information.
- `INSPECT` — inspect current closure, existing objects, assumptions, or hidden structure before inventing anything new.
- `MAP` — collect broad cheap cartography when the residual is too fuzzy for a deciding experiment.
- `REFRAME` — change decomposition/representation when a frozen search basis is exhausted or repeated evidence warrants a higher-altitude model.
- `DISCRIMINATE` — execute the smallest experiment that makes live rivals predict different outcomes.

A research decision is a pair, e.g. `(DISCOVER, MAP)`, `(VERIFY, DISCRIMINATE)`, `(REPAIR, INSPECT)`.

---

## 3. Default operating cycle

Use the smallest necessary part of the cycle; do not ritualistically perform every stage on every attempt.

### PUSH
Exploit the strongest current route hard enough to learn something. Do not abandon a frame because the first attempts fail.

### READ
Treat both success and failure as evidence. State what changed and identify the sharpest unexplained residual.

### DIAGNOSE
Classify the failure using the weakest explanation consistent with evidence:

- search;
- capability;
- representation/selectability;
- constructor/meta-language;
- data/assumption;
- infrastructure/measurement;
- objective/metric;
- boundary/scope;
- displacement/total-cost.

### MAP
When the residual is not sharp enough, collect broad low-cost measurements: censuses, profiles, perturbations, effect atlases, inference maps, ablation sweeps, countermodel maps, rapid sniff tests.

### INSPECT CLOSURE
Before inventing a new representation or operator, ask whether the desired object already exists, is latent in current state, or is composable from existing objects.

### ZOOM / IMPORT
When local information gain collapses, generate alternative decompositions. Outside material may arrive at any time — papers, repos, comments, conversations, analogies, observations. An import becomes active only by supplying a structural mapping and a differential prediction; novelty itself receives no credit.

### RIVAL
Maintain the strongest simpler explanations: search-only, memory-only, surrogate, leakage, measurement artifact, infrastructure, known method, wrong metric, displacement.

### FREEZE
Before protected execution, freeze: question, hypotheses, generator/search boundary, intervention, baseline, ablation/control, metric, budget, corpus, verifier, and interpretation table.

### DECIDE
Choose the smallest budget-feasible experiment with strong robust discrimination among observationally distinct rivals.

### ATTACK
If a result is positive, try to kill it: ablation, sham, wrong-direction control, matched-size surrogate, hostile cases, budget control, leakage audit, measurement replication.

### DESCAFFOLD
Remove labels, handcrafted features, supplied roles, target-specific operators, privileged ordering, hidden history, or other scaffolds one at a time.

### TRANSFER
Move to held-out examples, harder distributions, natural cases, new domains, or future episodes.

### RECONSTRUCT
Give a strong matched baseline the same raw historical evidence and resources and allow it to reconstruct a behaviorally equivalent object. Record full reconstruction cost.

### RATCHET
Retain only the smallest mechanism supported by the evidence, together with scope, provenance, dependencies, counterexamples, revocation conditions, and negative laws.

### RECURSE
Push again from the stronger state.

---

## 4. Candidate generation

Candidate-generation failure is not frame failure.

Each generator must predeclare a finite auditable search basis where feasible. Use named search slots rather than attempt counts. Repeating the same move does not count as broader coverage.

Default generator families:

- `LOCAL` — deeper/current-frame continuation;
- `RESIDUAL` — moves derived directly from the sharp residual/obstruction;
- `STRUCTURAL` — analogies/correspondences from other domains;
- `RETAINED` — laws/macros/constructors from prior episodes;
- `IMPORT` — external material;
- `HUMAN` — separately logged human injection.

Every candidate records generator, slot, provenance, budget cost, predicted outcome sets under every live rival, and whether it touched protected information.

Independent critics may widen predicted outcome sets but may not sharpen them. Overconfidence can therefore reduce estimated discrimination, never increase it.

---

## 5. Residual and escalation law

Do not infer representation failure merely because generated candidates failed.

Escalation to `REFRAME` requires, relative to the declared boundary:

1. valid objective and apparatus;
2. sufficiently sharp residual;
3. frozen generator families and search slots;
4. required slots actually attempted;
5. no pending slot;
6. no protected leakage;
7. no unresolved surprise that requires model expansion;
8. no current admissible action that robustly separates the live observational rival classes.

Otherwise the correct directive is usually `EXPAND_CANDIDATES`, `MAP`, `INSPECT`, `REPAIR`, or `AUDIT_GOAL_METRIC`.

---

## 6. Success and retention ladder

A successful task result is not automatically a retained capability.

Use this rough evidence ladder:

- `K0` — raw verified fact/result;
- `K1` — reusable derived object;
- `K2` — verified abstraction/operator with causal support;
- `K3` — retained structure changes later reachable capability under matched budget;
- `K4` — retained structure causally enables construction/acquisition of another new retained structure.

For `K2+`, require appropriate ablation/control evidence. For `K3+`, require strong raw-history reconstruction comparison. For `K4`, require a recursive causal chain.

---

## 7. Method-on-method loop

The constitutional core is stable; the policy `M_t` is revisable.

A methodological residual may include:

- repeated bad experiment choices;
- missed separators;
- premature/late reframing;
- wasted search budget;
- wrong generator coverage;
- bad equivalence/probe definitions;
- failure to transfer;
- incorrect retention;
- systematic human interventions that the automated policy cannot reproduce.

A proposed method revision `Delta M` is treated like any other scientific hypothesis:

1. state the methodological residual;
2. name rival explanations (random variance, better memory, extra search, metric artifact, etc.);
3. predict what the revision should change;
4. freeze a prospective comparison before protected future episodes;
5. compare `FIXED`, `SELF_REVISING`, `RAW_HISTORY`, and `SHAM_REVISION` where feasible;
6. admit the method revision only if future research yield improves under relevant controls.

Never use retrospective fit alone to promote a method revision.

---

## 8. Research yield

Do not optimize positive-result rate alone. Record a vector rather than hiding tradeoffs in one arbitrary scalar:

- verified target progress;
- live rivals eliminated;
- residual sharpening;
- bad branches avoided;
- new verified capability;
- future search reduction;
- model calls/tokens;
- verifier/solver calls;
- CPU/wall/RSS where relevant;
- scaffold additions;
- transfer survival;
- reconstruction cost;
- surprise/model-miss rate.

A null result can be a good research decision when it sharply changes what should be tried next.

---

## 9. Required ledger entries

For every consequential experiment retain:

- date/run/commit/environment;
- state before experiment;
- lifecycle + epistemic mode;
- residual and rival explanations;
- generator + search slot;
- frozen prediction table;
- baseline/intervention/control;
- budget vector;
- verifier/metric;
- result including null/infra failure;
- interpretation;
- causal attack;
- transfer/reconstruction status;
- retained law or negative law;
- unresolved residual;
- next mode-switch condition.

Negative results and infrastructure failures remain first-class ledger objects.

---

## 10. Compact invocation

When starting or resuming any project, use:

> **Apply UVRM. Reconstruct the actual current state from evidence. Define the real goal and verifier. Push the strongest existing route until it yields a sharp result. Read the result as evidence; classify the residual using the weakest adequate failure class. If unclear, MAP. Before invention, INSPECT CLOSURE. Maintain strong rivals and audit objective/apparatus validity. Generate candidates from frozen auditable search slots across LOCAL, RESIDUAL, STRUCTURAL, RETAINED, IMPORT and HUMAN provenance as available. Candidate-generation failure is not frame failure. Freeze the smallest discriminating experiment before protected execution. Attack successes, descaﬀold, transfer, test raw-history reconstruction, then retain only causal mechanisms with scope and revocation conditions. Track immutable evidence and negative laws. Periodically inspect methodological residuals; revise the method only through prospective controlled evidence. Optimize research yield and future capability, not narrative confirmation.**

This file is the canonical portable version. Project-specific protocols may add constraints but should explicitly record any deviation from the constitutional core.
