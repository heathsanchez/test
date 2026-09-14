# Andrews–Curtis Discovery Track — MDA Domain Contract

Status: **bootstrap contract v1**  
Source present before MDA integration: `7d729961a2292e8a77efba4287d18c227e543263`  
Repository: `heathsanchez/test`, branch `acc-competitive-residual-v1`  
Grounding authority pin: `SAIRcompetition/Andrews-Curtis@99a65377c5c4f412cd9af7b8d31c41464a855736`  
Retained ACSolverX pin: `6a12515fe1d95178a483b76d5553266e61122417`

This contract applies the domain-independent Minimal Developmental Algorithm to
the SAIR Andrews–Curtis Discovery Track.  It does **not** define a new solver.
It defines what the domain is allowed to decide about solver development.

## 1. Domain

Name: SAIR Andrews–Curtis Challenge — Discovery Track, AC and Stable AC.

Current project:
- competition authority: `SAIRcompetition/Andrews-Curtis`;
- developmental implementation: this repository;
- current operational family: exact official replay, GS-Sub quotient search,
  exact atomic compilation, Proof Atlas terminal compilation, local peephole
  superoptimization, live scoring/publication gate.

Toolchain/runtime:
- Python 3 on GitHub Actions;
- official verifier uses deterministic standard-library integer replay;
- retained ACSolverX code is pinned separately;
- public/live leaderboard and authenticated submission APIs are external
  time-varying authorities, not part of the solver.

The MDA integration workflow records its exact `GITHUB_SHA`; this document's
source-present SHA is provenance for the pre-integration present.

## 2. Encounter interface

### Primary construction encounter

One encounter is:

```text
challenge presentation
+ problem kind (AC or Stable AC)
+ currently authorized present
+ resource bounds
-> candidate move sequence or unresolved status
-> official verifier consequence
```

Serialization:
- challenge IDs and exact initial relators come from the pinned official
  manifest;
- candidate certificates are UTF-8 lines
  `challenge_id: [move_id,...]`.

Batch/stream semantics:
- official submissions may contain up to 500 solution lines;
- each path is independently replayed after structural validation;
- local developmental experiments must record each target separately before
  any aggregate claim.

Ordering assumptions:
- AC target is exactly `[[1],[2]]`, in order;
- Stable AC target is `[]`;
- path move order is semantic and cannot be permuted.

Hidden-state assumptions:
- official replay is deterministic and contains no hidden solver state;
- the live leaderboard is a time-varying external environment because other
  teams act after a freeze;
- competitors' certificates are not observable through the public frontier.

### Scoring encounter

A scoring encounter is a verifier-clean certificate evaluated against a
**timestamped live leaderboard snapshot**.  This is a separate consequence
from semantic correctness.

## 3. Grounding consequence / verifier

### V0 — semantic ground

Verifier:
`competition/tools/verifier` at official pin
`99a65377c5c4f412cd9af7b8d31c41464a855736`.

Input:
- official challenge from `manifest.json`;
- integer move sequence;
- challenge move-spec version;
- official limits.

Output:
- `ok`;
- verified length;
- cumulative work;
- certificate hash;
- exact error code on failure.

PASS means:
- all moves are valid and applicable;
- all path/work/relator limits hold;
- final state is exactly the required target.

FAIL means:
- the official verifier rejects the path.

UNKNOWN means:
- semantic UNKNOWN is not emitted by the deterministic path verifier; MDA
  UNKNOWN statuses arise from incomplete search, incomplete authority,
  non-identifiability, scope or stale evidence.

Version/pins:
- repository pin above;
- AC move spec `ac-r2-v1`;
- Stable AC move spec `sac-r8-v1`;
- manifest hashes and golden vectors are checked in the baseline workflow.

Can the implementation being developed modify V0? **NO.**

### V1 — competition consequence

The SAIR live frontier and platform-accepted submissions determine score.

Scoring consequence:
- on a challenge, if `k` teams share the shortest verified length, each
  receives `2^(1-k)` points;
- AC and Stable AC are scored separately;
- later shorter certificates replace prior records;
- the frontier is therefore non-stationary and OPEN.

V1 can rank verified certificates economically.  It cannot overrule V0.

Authority order:

```text
official verifier V0
> platform acceptance receipt
> frozen public leaderboard snapshot
> bounded matched experiment
> historical solver success
> heuristic metric
```

## 4. Protected consequences Q_t

Future retained development must preserve:

1. official verifier conformance and manifest/hash checks;
2. exact local replay of the six score-bearing certificates from platform
   submission `70`:
   - `ac-01635` length 8;
   - `sac-01635` length 10;
   - `ac-04246` length 14;
   - `sac-04246` length 16;
   - `ac-08491` length 8;
   - `sac-08491` length 10;
3. platform provenance that those six rows were accepted;
4. verifier-clean regression behavior on the V5 frozen matched probe pack,
   when its exact candidate artifacts are available;
5. submission format, quota safety, and fresh-live-recheck behavior;
6. no silent weakening of official path/work/length constraints.

Replayable score-bearing cases are stored at:

`mda/domains/andrews_curtis/replay/protected_cases/scoring_holds_submission70.txt`.

A live tied hold may later be stolen without invalidating its historical
certificate.  That changes the **economic state**, not the truth of the stored
verified consequence.  The next live freeze updates economic protection.

## 5. Warrant model

This domain contains several different warrant regimes.

### Exact path semantics

- finite deterministic replay;
- theorem-like authority for a specific certificate under the pinned verifier;
- certificate validity is closed once dependencies are pinned.

### Search / shortest-path claims

- enormous search spaces;
- current searches are incomplete unless a finite declared class has actually
  been exhausted;
- failure, timeout, node cap, or absence of a shorter path is
  `UNKNOWN_SEARCH`, not impossibility.

### Live competition consequence

- non-IID, time-varying, adversarial/multi-agent;
- public frontier is a timestamped observation, not closure;
- competitor future behavior is OPEN;
- non-observation is not impossibility;
- a finite frozen pack supports only a scoped empirical/bounded claim.

### Identifiability

If multiple retained mechanisms remain verifier-clean and economically
incomparable, the result is `UNKNOWN_CHOICE` until an authorized
discriminating encounter separates them.

### Staleness

Any changed official verifier pin, manifest, move spec, challenge data,
resource limit, leaderboard snapshot, or retained dependency invalidates the
affected scope and requires replay.

## 6. Developmental preorder / economy

Admission constraints dominate all performance objectives:

```text
1. official verifier violations == 0
2. protected replay violations == 0
3. scope / authority valid
4. then compare lawful continuations by a Pareto relation
```

Pareto coordinates include:

```text
maximize:
    current scoring consequence
    protected scoring retention
    verified prospective reach

minimize:
    final official atomic moves
    live record gap
    official work
    search nodes
    wall time
    peak memory
    submission/API cost
    implementation complexity
    maintenance/dependency burden
    future acquisition/reconstruction cost
```

No single scalar objective is canonical.  A scalarization is allowed only
inside a frozen experiment and must be recorded as part of that experiment.

A mechanism that produces a shorter certificate but requires substantially
more search can remain incomparable with a faster mechanism.  Do not erase one
without evidence that the relevant future economy makes it dominated.

## 7. Starting continuation language

The bootstrap continuation language may only:

- enable/disable already-existing ACC mechanisms;
- select among retained search policies `current` and V2 replay-clean
  `mask3 = short+long`;
- select compiler beam widths already qualified in V5;
- enable/disable Proof Atlas;
- enable/disable local peephole superoptimization;
- change caches, attempt-memory scope, batching and scheduling where semantic
  replay is unchanged;
- generate matched probes from official challenges;
- alter publication selection while remaining answerable to V0 and V1.

The following are **not active inherited structure merely because they were
implemented**:

- V3 guard variants;
- atomic-cost-first search;
- V6 window-7 near-miss experiment;
- any target-specific motif or feature heuristic.

They remain provenance-bearing proposals/evidence until inheritance is earned.

This continuation language is a boot substrate, not a permanent ontology.
Expansion beyond it requires a scoped `CERTIFIED_OBSTRUCTION`.

## 8. Probe / intervention interface

Authorized probes include:

### Official replay probe
Cost: low.  
Authority: V0.  
Separates: valid vs invalid certificate.

### Matched search-policy probe
Run the same target, verifier pin, resource cap and compiler family under
different retained search policies.  
Separates: reachability, quotient route, node cost and final atomic cost.

### Compiler-beam probe
Hold target and quotient route fixed; vary compiler beam.  
Separates: compiler choice/certificate cost from search-route effects.

### Atlas ablation
Compare the same verifier-clean path before/after retained terminal
compilation.  
Separates: future compilation value.

### Peephole ablation
Compare the same verifier-clean certificate before/after local exact
superoptimization.  
Separates: local compilation value.

### Live scoring probe
Fresh public frontier immediately before publication.  
Separates: currently scoring vs non-scoring certificate.  
This probe does **not** prove future score retention.

Probe selection should ask:

> What is the cheapest authorized encounter that makes the surviving lawful
> alternatives behave differently?

## 9. Forbidden changes

The developmental system may not alter:

- official verifier semantics;
- move tables or applicability conditions;
- official challenge data or target endpoints;
- official path/work/relator limits;
- competition scoring rule;
- submission quota definition;
- externally imposed deadline or team policy;
- stored protected certificates when replaying them as historical evidence.

It may not use a solver-created evaluator as independent proof of correctness.

## 10. Freeze boundary

Before a decisive MDA cycle, freeze:

- domain-independent kernel files;
- this domain contract;
- boot adapter / bootstrap code;
- official verifier pin;
- ACSolverX pin when used;
- protected replay suite;
- developmental preorder;
- probe definitions;
- current live snapshots;
- source `GITHUB_SHA`;
- hashes of recovered prior artifacts.

No scientific kernel or domain-contract change is allowed after the frozen
evidence is exposed within that cycle.

Harness-only repairs must be documented separately and must not be interpreted
as scientific improvement.

## Current bootstrap question

The immediate purpose of the first MDA cycle is **not** to invent another ACC
solver.  It is to establish the lawful present from existing evidence:

- run baseline ground + protected replay;
- run solvent on inherited/provisional machinery;
- regrow from a deliberately small valid seed using only the boot continuation
  language;
- compare genesis and solvent endpoints;
- preserve unresolved alternatives;
- return UNKNOWN rather than manufacture a new mechanism when the evidence
  does not authorize growth.
