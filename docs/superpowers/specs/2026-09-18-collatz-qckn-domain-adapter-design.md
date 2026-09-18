# Collatz QCKN V1 Domain Adapter — Design

**Date:** 2026-09-18  
**Status:** Design specification  
**Repository:** `heathsanchez/test`  
**Branch:** `collatz-qckn-v1`  
**Reference QCKN:** `heathsanchez/realitygraph:qckn-v1-frozen`  
**Reference QCK:** `heathsanchez/Minimal-Sufficient-Interface:qck-v1-frozen`

## 1. Purpose

Turn the existing exact Collatz research programme into a thin, explicit QCKN V1 domain adapter and developmental runtime without changing the mathematical meaning of the existing Collatz engines.

The adapter must preserve the strongest discipline already present in the work:

> Never introduce a distinction without consequential evidence; never erase one while a protected future can expose it; never retain a developmental change without independent verification; never replay discovery once its verified consequence has been safely compiled.

The immediate objective is not to claim Collatz, nor to replace the exact arithmetic engines. It is to make verified mathematical lessons first-class causal capabilities so that later generations can reuse them from a canonical CompiledPresent and so that causal compounding can be measured with matched controls.

## 2. Scope and non-goals

This V1 adapter covers the existing exact lower-merge research domain:

[
operatorname{LM}(n,x)
iff
x<nlandexists a,b,;T^a(n)=T^b(x).
]

The protected consequence is:

[
orall n>1,quad exists x<n:operatorname{LM}(n,x).
]

The adapter may use existing verified constructors such as direct descent, immediate inverse-odd predecessor, Complete-O outcomes, reverse-episode certificates, transferable RIGID fragments, and forward q0 descent macros.

It does **not** claim that the current capability bank is complete, that the current residual grammar proves Collatz, that any bounded census generalizes universally, or that the adapter is the exact linear QCK theorem surface. This is a discrete/non-linear QCKN adapter profile.

## 3. Architectural boundary

The implementation has four layers.

### 3.1 Existing exact domain engines

Existing Collatz scripts remain authoritative for domain arithmetic. The QCKN layer must call or wrap them rather than duplicate their mathematics.

Examples include:

- `collatz_q0_coalescence_component_audit.py`;
- `collatz_q0_rigid_recharge_audit.py`;
- `collatz_universal_reverse_episode_bfs_v2.py`;
- `collatz_fragment_transfer_probe.py`;
- `collatz_forward_descent_macro_transfer.py`.

### 3.2 Collatz adapter

The adapter translates domain results into typed developmental judgments.

The minimum V1 outcome vocabulary is:

- `CERTIFIED_LOWER_MERGE`;
- `CERTIFIED_DESCENT`;
- `TAIL_CLOSED`;
- `RIGID_RESIDUAL`;
- `UNKNOWN_SEARCH`;
- `UNKNOWN_CHOICE`;
- `UNKNOWN_EXPRESSIVITY`;
- `CERTIFICATE_INVALID`;
- `IMPLEMENTATION_MISMATCH`;
- `OUT_OF_SCOPE`.

A timeout, depth limit, or exhausted local budget must remain `UNKNOWN_SEARCH` unless a declared complete regime proves a stronger obstruction.

### 3.3 Authority and causal ledger

Proposal is not promotion.

Every retained capability must pass an independent replay verifier under an explicit contract. Promotion creates an immutable causal event containing:

- typed capability identity;
- exact applicability guard;
- executable semantics or canonical payload;
- certificate;
- dependencies;
- authority snapshot;
- verifier identity/version;
- provenance/acquisition generation;
- declared cost;
- ablation handle.

Revocation is causal and must survive restart.

### 3.4 CompiledPresent

The active mathematical memory contains only promoted, non-revoked capabilities whose dependencies are active.

Raw acquisition history, search traces, rejected candidates, and RED diagnostics are not active execution state.

Compilation must be deterministic and canonical. Restart from the serialized CompiledPresent must reproduce WARM behavior without replaying discovery.

## 4. Domain state

For the Collatz adapter, instantiate the QCKN developmental state as

[
Sigma=(Gamma,mathcal L,mathcal P).
]

### (Gamma): protected contract

Contains:

- shortcut Collatz map definition;
- lower-merge consequence;
- exact arithmetic conventions;
- source-shell contract;
- authority/verifier versions;
- search completeness declarations;
- protected ordinary-positive-integer scope.

### (mathcal L): active executable language

Contains the currently promoted constructors/capabilities. Initial candidate families include:

- direct descent;
- immediate inverse-odd predecessor;
- selected exact reverse predecessor schemas;
- exact reverse episode fragments;
- q0 forward descent macros;
- composed capabilities only when composition is independently replay-verified.

### (mathcal P): causal developmental memory

Contains:

- immutable promotion/revocation events;
- dependency edges;
- provenance;
- evidence digests;
- generation;
- costs;
- ablation handles.

The compiled active projection of (mathcal P) is the Collatz CompiledPresent.

## 5. Capability schema

A V1 Collatz capability is a typed record with the following semantic fields:

[
oxed{
C=(id,;kind,;guard,;effect,;certificate,;deps,;authority,;provenance,;cost).
}
]

### Required kinds

**DIRECT_DESCENT**

Guard proves a forward path applies; effect supplies (T^t(n)<n).

**INVERSE_ODD**

Guard proves endpoint (yequiv2mod3) and predecessor positivity; effect supplies (p=(2y-1)/3<n) with (T(p)=y).

**REVERSE_SCHEMA**

Guard is an exact congruence/episode condition; effect supplies a replayable lower coalescing predecessor/path.

**RIGID_FRAGMENT**

A verified exact episode fragment transferable under its anchor/guard.

**FORWARD_DESCENT_MACRO**

A verified q0 episode word whose replay under its exact guard visits a value below the represented source.

Additional kinds require an explicit adapter version change or compatible extension.

## 6. Canonical identity and deduplication

Capability identity must be semantic enough to avoid retaining presentation duplicates.

For affine/episode capabilities, canonical identity should be derived from:

- kind;
- start/end anchor;
- exact affine map parameters;
- canonical episode word where required by the guard;
- guard digest;
- contract digest.

Two payloads with the same identity but different semantics are a conflict and compilation must refuse them.

Syntactically different candidates that are extensionally identical under the protected contract should compile to one active capability when equivalence is independently established.

## 7. Typed residual routing

The adapter must preserve classification separately from intervention choice.

### `CERTIFIED_LOWER_MERGE` / `CERTIFIED_DESCENT`

Licensed action: `COMPILE` if the certificate is proposed as reusable; otherwise terminal for the current obligation.

### `RIGID_RESIDUAL`

Licensed actions may include `CONSTRUCT`, `VERIFY`, `RESTRUCTURE`, or a representation split when a concrete separator proves an active abstraction too coarse.

### `UNKNOWN_SEARCH`

Licensed actions: extend search or verify a candidate. It must not directly trigger grammar expansion.

### `UNKNOWN_EXPRESSIVITY`

May license `EXPAND` only with a matching completeness/no-resolution certificate for the declared current language.

### Invalid/mismatch outcomes

Route to `VERIFY`, `REVOKE`, or `RESTRUCTURE` as appropriate. They must never silently enter active memory.

## 8. MDA policy for Collatz V1

The policy minimizes prospective cost subject to licensed interventions.

The primary score is not raw source coverage. Prefer, in order:

1. verified closure of a previously unresolved protected obligation;
2. prospective transfer to untouched sources;
3. residual-class elimination;
4. future search/acquisition cost reduction;
5. capability complexity and verification cost.

A RED is retained only as the smallest reusable falsifier/constraint it proves.

Examples already established by the programme include:

- finite acyclic abstraction is impossible for the unchanged Complete-O/direct-descent machine;
- local scalar and simple adelic ranks are insufficient;
- deeper q7/q12 residue banks have low marginal consequence in the tested regime;
- long transferred fragments add little beyond short fragments in the tested held-out regime;
- blind reverse-depth escalation has severe diminishing returns.

These are developmental constraints, not mathematical claims beyond their verified boundaries.

## 9. Generation protocol

### G0 — cold baseline

Run the declared target shell with no learned Collatz capabilities beyond constitutional primitives. Record:

- obligations;
- terminal certificates;
- unresolved residuals;
- acquisition/search cost;
- verification cost.

### G1 — acquire

Use a frozen training shell to discover candidate capabilities.

For the first adapter qualification, the existing forward q0 descent macro result is the seed acquisition:

[
252	ext{ training sources}
	o481	ext{ candidate macros}.
]

Every candidate must be independently replay-verified before promotion.

### G1 — promote and compile

Minimize/deduplicate verified candidates, append promotion events, compile active memory, serialize it canonically, and record a content digest.

### G1 — restart

Start a fresh process from only:

- frozen domain code;
- protected contract;
- CompiledPresent.

Do not restore raw discovery episodes.

### G2 — prospective use

Attack an untouched source shell. Record zero-search capability hits separately from new search.

Any genuinely new verified capability is promoted as G2 with explicit dependencies.

### G3 and later

Repeat. The developmental claim strengthens only if verified reach grows while new acquisition/search cost falls.

## 10. Mandatory matched controls

Any claim that compiled capabilities causally improve later mathematical work must run matched controls.

**COLD**

No learned capabilities.

**WARM**

Canonical CompiledPresent from prior generations.

**RAW_HISTORY**

Raw prior discovery/evidence is available but not compiled into active capabilities.

**SHAM**

Same memory shape/count/cost envelope as WARM, but payloads are stale, wrong, inapplicable, or otherwise non-authoritative and must not produce valid hits.

**ANCESTOR_ABLATION**

Remove the promoted capability family or a required ancestor, recompile, and verify that the claimed advantage disappears or the cold search cost returns.

The first qualification must not claim causal compounding without a successful relevant ablation.

## 11. Cost accounting

The adapter must report at least:

- domain search expansions;
- candidate constructions;
- independent replay verifications;
- promoted capabilities;
- active capabilities after minimization;
- zero-search WARM hits;
- new acquisition count;
- unresolved obligations;
- wall time as secondary operational evidence.

A cost claim must name its accounting unit.

The primary developmental quantity is:

[
oxed{
rac{	ext{new verified protected consequences}}
{	ext{new acquisition/search cost}}.
}
]

Coverage alone is insufficient.

## 12. Restart contract

A restart qualification must prove:

[
operatorname{Active}(operatorname{parse}(operatorname{text}(M)))=
operatorname{Active}(M).
]

The restarted WARM run must reproduce the same active capability decisions and certificate outputs as the pre-restart WARM run for the qualification obligations.

Raw training history must not be required.

## 13. Revocation and ablation

Every promoted capability has an ablation handle.

Revoking a capability:

- preserves its causal record;
- removes it from active memory;
- disables dependent capabilities;
- survives serialization/restart;
- must not be undone by stale merge/reload.

The qualification suite must include targeted revocation of the seed forward-descent capability family and demonstrate loss of its prospective advantage.

## 14. Verification architecture

Verification is independent of proposal.

For each capability, the authority must check:

1. payload parses and is within declared scope;
2. guard is satisfied on every claimed qualification instance;
3. exact replay reaches the claimed common endpoint or descent;
4. lower predecessor/minimum path value is genuinely below the protected source where required;
5. dependencies are active and compatible;
6. authority/contract/verifier digests match;
7. no bounded observation is promoted as a universal theorem unless its guard itself is finite and exact.

Qualification tests must deliberately include invalid, stale, sham, and mismatched capabilities.

## 15. Initial implementation units

The V1 adapter should be implemented as small independent modules.

`collatz_qckn/types.py`

Typed outcomes, obligation, capability, evidence, ledger event, cost record.

`collatz_qckn/authority.py`

Independent exact replay verifier and authority snapshot.

`collatz_qckn/ledger.py`

Immutable causal promotion/revocation events and deterministic active projection.

`collatz_qckn/compiled_present.py`

Canonical serialization, parse, digest, dependency validation, restart.

`collatz_qckn/adapter.py`

Maps existing Collatz engine results to typed QCKN judgments and capability proposals.

`collatz_qckn/mda.py`

Licensed-intervention routing and prospective cost selection.

`collatz_qckn/runner.py`

COLD/WARM/RAW_HISTORY/SHAM/ANCESTOR_ABLATION generation harness.

Existing `experiments/` files remain research engines and evidence sources; they are not silently rewritten into the runtime.

## 16. Test strategy

Implementation follows test-first development.

The qualification surface must include tests for:

- proposal cannot become active without authority verification;
- valid forward-descent macro promotion;
- invalid replay rejection;
- stale contract rejection;
- canonical serialization and exact restart;
- semantic deduplication;
- same-ID conflict refusal;
- dependency invalidation;
- causal revocation;
- WARM zero-search reuse;
- RAW_HISTORY not equivalent to WARM;
- SHAM rejection;
- ancestor ablation restoring cold behavior;
- UNKNOWN_SEARCH preservation;
- UNKNOWN_EXPRESSIVITY requiring a matching completeness certificate;
- deterministic evidence digest.

The end-to-end test must run a small sealed training/future split fast enough for CI while preserving the same causal structure as the larger research run.

## 17. First qualification experiment

Use the forward q0 descent macro family because it already demonstrated prospective transfer.

The qualification is deliberately bounded.

1. Freeze a training shell and future shell.
2. Run COLD on the future shell.
3. Discover candidate macros only from the training shell.
4. Independently verify and promote the valid subset.
5. Compile and restart from CompiledPresent.
6. Run WARM on the future shell.
7. Run RAW_HISTORY and SHAM controls.
8. Revoke/ablate the promoted macro family and rerun.
9. Emit one machine-readable evidence record containing all arm metrics and digests.

The release verdict may state only what the experiment proves, for example:

> Bounded causal reuse of independently verified Collatz descent capabilities was demonstrated on the declared sealed future shell.

It must not state or imply a proof of Collatz.

## 18. Success criteria

The Collatz QCKN V1 adapter is qualified when all of the following hold:

- typed adapter outcomes preserve the epistemic boundaries above;
- proposals require independent verification;
- promoted capabilities compile canonically;
- exact restart works without raw history;
- WARM reuses at least one prior verified capability on a sealed future obligation with zero rediscovery;
- RAW_HISTORY and SHAM do not reproduce that authoritative hit merely by containing prior material;
- targeted ablation removes the hit or restores the cold acquisition path;
- all invalid/stale/conflicting cases are rejected;
- evidence and cost accounting are deterministic;
- the existing Collatz arithmetic engines remain unchanged in meaning.

## 19. Claim boundary

A green Collatz QCKN V1 release would establish a developmental result:

[
oxed{
	ext{verified mathematical consequences can be promoted, compiled, restarted,
and causally reused on later Collatz obligations.}
}
]

It would **not** establish:

[
oxed{	ext{Collatz is proved}.}
]

The mathematical research continues from the compiled residual state. The purpose of the adapter is to ensure that verified lessons accumulate as executable mathematical capability while falsified developmental paths remain explicit constraints rather than being rediscovered.
