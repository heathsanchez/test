# RGRS Experiment Ledger

This ledger is the authoritative residual/representation record for the Lean optimization programme. Entries preserve rejected and obstructed results as evidence; nothing is silently discarded.

## Current frontier evidence

### RGRS-L001 — Canonicalization placement

- State: ADMITTED LAW
- Source: E0018 / A3
- Residual before intervention: R3 Redundancy
- Location: nested-Lambda `apply_many` environment canonicalization
- Intervention: defer intermediate `key_env` pruning at transient composition boundary while preserving canonicalization at persistence/cache boundaries.
- Frozen semantic result: 161/161 on both arms, zero declines.
- Protected resource result: 12/12 wall wins, 12/12 CPU wins, 9/12 RSS wins; median paired wall -4.9082%, CPU -4.6513%, RSS -3.4164%.
- Decision: ADMITTED.
- Law: `CANONICALIZE_AT_PERSISTENCE_BOUNDARIES_NOT_TRANSIENT_COMPOSITION_BOUNDARIES`.
- Consequence: canonicalization itself is not the target; *where identity is materialized* is a first-class representation decision.

### RGRS-L002 — Repeated canonical-environment threading does not close the residual

- State: NEGATIVE LAW
- Sources: E0016, E0017
- Primary residual: R3 Redundancy
- E0016 infer canonical-env threading: +0.1246%, rejected.
- E0017 eval canonical-env threading: -0.0616%, too small/noisy, not admitted.
- Decision: repeated local threading is not a sufficient representation change.
- RGRS trigger: Rule A satisfied for the narrow "thread already-canonical env harder" family.

### RGRS-L003 — Canonicalization remains a major cost center after A3

- State: OBSERVATION
- Source: fresh A3 profile
- Primary residual: R2 Cost, secondary R3 Redundancy
- Evidence: `prune_env_cold` = 382,910,453 / 2,697,871,700 self instructions = 14.19% on the profiled workload.
- Scope: profile workload dominated by `grind-ring-5`.
- Confidence: high for local hotspot, not automatically global.

### RGRS-L004 — Cache value is structurally conditional

- State: OBSERVATION
- Source: A3 open-eval cache diagnostic
- Primary residual: R5 Applicability
- App: n=1489, hit 32.57%, same-env 14.71%, mean loose=5.564, mean mask-pop=2.764.
- Lambda: n=383, hit 29.50%, same-env 12.79%, mean loose=4.606, mean mask-pop=3.196.
- Pi: n=267, hit 58.05%, same-env 4.12%, mean loose=2.539, mean mask-pop=1.820.
- Proj: n=17, hit 70.59%, same-env 0%.
- Let: n=7, hit 0% in sample; bypass test E0022 was semantically safe but too small to matter.
- Interpretation: materializing a full canonical environment has different expected value by expression class.

### RGRS-L005 — Lambda raw-env capture is conditionally promising, not yet a representation admission

- State: MECHANISM SIGNAL
- Source: E0030 protected PGO gate
- Primary residual: R4 Observability / R3 Redundancy
- Intervention: from A5, Lambda closure captures existing env directly instead of `key_env`-pruned env.
- Semantics: 161/161 both arms, zero declines.
- Paired medians: wall -2.6519%, CPU -0.4950%, RSS -0.1929%.
- Decision: retain as evidence that eager environment projection can be avoided in some Lambda paths; do not infer universal applicability.

### RGRS-L006 — A6 is strong on the frozen Arena proxy but cannot by itself settle the cross-regime question

- State: CONDITIONAL SIGNAL
- Source: A6 vs Arena-pinned sokonanoda run 31873303994
- Primary residual: R5 Applicability
- Semantics on frozen proxy: 161/161 both arms, zero declines.
- Median: A6 0.827586 s vs Arena-pinned sokonanoda 1.089281 s.
- Reported speedup: 1.3162x; A6 wins 16 paired samples; paired median A6-minus-Arena -23.9586%.
- Boundary: this establishes a strong proxy regime result only. It does not license a universal eager/lazy choice across Cedar, CSLib, init-prelude, or full-Mathlib.

## Active representation hypothesis — H-DAG-001

### Name

Selective canonical identity / canonical-DAG environment representation

### Current residual

```text
rho = (
  class = R5 Applicability,
  location = environment projection + open-eval cache identity,
  evidence = E0018 admission + E0016/E0017 failures + A3 profile + class-conditional cache economics + E0030/A6 regime signal,
  scope = Lean checker evaluation workloads,
  confidence = medium-high
)
```

Secondary residuals: R3 Redundancy, R4 Observability, R8 Access.

### Why representation change is now allowed

- Rule A: repeated local canonical-env threading interventions did not remove the residual.
- Rule B: available results indicate materially different evaluation regimes can prefer different eagerness/selectivity choices.
- Rule C: verifier-equivalent environment distinctions are repeatedly reconstructed/projected.
- Rule D: some environment components are not observed by a given expression/path.
- Rule E: the present representation conflates "environment as execution sequence" with "environment as cache identity"; the needed object is identity of the *observed dependency projection*.
- Rule F: first candidate must compose already-supported mechanisms (selectivity + canonical persistence identity) rather than introduce a new semantic primitive.

### Representation proposal

Do **not** replace Lean terms with a global DAG wholesale.

Introduce the smallest distinction-changing object first:

```text
ObservedEnvId(expr, env) = intern(canonical projection of env required by expr)
```

Properties:

1. Raw environment remains available for evaluation.
2. Canonical identity is materialized only when a persistent/cache identity is actually needed.
3. Projection result is interned/content-addressed so equivalent observed environments share identity.
4. The identity node stores/reuses dependency information needed to avoid rescanning/reconstructing the same projection.
5. Pi/Proj can retain eager identity materialization where cache economics justify it; App/Lambda can defer it until a cache operation is predicted/required.

This is intentionally narrower than "convert everything to a DAG". A global DAG is permitted only if this smaller representation cannot separate the regimes.

### Strongest old-representation explanation

The wins may come entirely from avoiding a few `prune_env_cold` calls. If so, a selective lazy path using the existing list/tree environment should match the proposed representation; interning/persistent identity adds no causal value.

### Separator question

> After controlling for laziness/selectivity, does persistent observed-environment identity remove repeated projection/reconstruction enough to improve the reuse-heavy discriminator without imposing cost on the low-reuse discriminator?

### Smallest deciding arms

- A0 — pinned strongest lawful baseline.
- A1 — selective/lazy projection using current representation; no persistent observed-env identity.
- A2 — same selectivity as A1 + `ObservedEnvId` interning/persistent dependency identity.
- A2-ablation — compile the same A2 path but disable identity reuse (fresh identity per request); preserves control flow while removing the representation-level causal mechanism.

A2 versus A1 isolates representation identity from laziness. A2 versus A2-ablation is the causal representation ablation.

### Opposing discriminators

Predeclare at minimum:

- reuse-heavy / canonicalization-heavy: Cedar or the strongest measured equivalent workload exhibiting repeated environment projection;
- regime where broad eagerness/selectivity previously behaves differently: CSLib;
- semantic/control discriminator: `init-prelude` plus the complete frozen Arena good/bad semantic corpus.

No workload may be removed after results are visible.

### Metrics

Primary resource metric: paired CPU time.

Secondary, predeclared diagnostics: wall time, peak RSS, `prune_env_cold` call count, observed-env projections constructed, identity hits/misses, canonical bytes/nodes materialized.

Admission may not switch to a secondary metric after seeing results.

### Decision table

- A2 beats A1 on primary metric in the reuse-heavy regime, preserves the opposing regime, passes semantics, and A2-ablation loses the gain -> escalate to protected Arena/full gate.
- A1 ~= A2 -> representation identity adds no causal value; reject H-DAG-001 and retain selectivity only.
- A2 helps reuse-heavy but hurts CSLib -> R5 remains; do not globally install. Search for a cheap activation predicate using pre-result structural features only.
- A2 and A2-ablation both win equally -> gain is not caused by persistent identity; reject representation claim.
- Any semantic failure -> R9 immediate reject.
- Local call-count win with worse paired CPU/RSS total -> R12 displacement.
- Runner/build failure -> R10 only; repair with no scientific update.

### Boundary robustness test

If H-DAG-001 passes, repeat the causal comparison under one alternate reasonable identity granularity:

- expression-specific observed projection identity versus frame-level observed projection identity.

A capability claim survives only if the causal gain is not an artifact of exactly one arbitrary node boundary.

## Next action

Implement only instrumentation and the A1/A2/A2-ablation separator first. Do not build a whole-kernel canonical DAG before this test decides whether persistent observed-environment identity has value beyond laziness.
