# RGRS canonical-environment identity audit

## Finding

The current sokonanoda representation already contains the essential object that the preliminary RGRS note called `ObservedEnvId`.

At base revision `9b4ea12f4cd437d00b6bcd0e34743065c58dea08`:

1. `key_env(env, e)` computes the free-variable mask and calls `prune_env`.
2. `prune_env_cold` projects the raw environment into `(out_mask, slots, lsub)`.
3. `intern_frame(hash, out_mask, slots, lsub)` hash-conses that projection.
4. Equal projected frames return the same `E` pointer.
5. Downstream caches use environment pointer identity in keys.

Therefore the missing object is **not** a canonical projected-environment identity. It already exists.

The live residual is more precise:

> We often pay most of the projection/materialization cost before discovering that the resulting canonical frame already exists.

This is primarily **R8 — Access residual**, with an R3 redundancy component, rather than an R6 missing-representation residual.

## Evidence already in the ledger

- `prune_env_cold`: 382,910,453 / 2,697,871,700 self instructions = 14.19% on the A3 profile.
- frame-interner diagnostic: 1,848,149 calls; 745,981 hits; 1,102,168 misses; ~40.36% existing-frame reuse.
- E0014 (more input prune-map associativity) did not pay.
- E0016/E0017 duplicate canonical-env threading did not pay.

This combination rules out the naive next move "add a canonical DAG". The projected environment is already hash-consed. The deciding question is now whether **cold projection work that terminates in an interner hit is large enough and structured enough to bypass before slot materialization**.

## RGRS residual

`rho = (R8 Access, prune_env_cold -> intern_frame, cold projection precedes canonical identity discovery, open-eval/canonical-env paths, high)`

Secondary residual: R3 Redundancy.

## Smallest deciding test: E0031

Instrument `prune_env_cold` without changing semantics. Count:

- cold prune calls;
- total selected slots traversed/materialized;
- `intern_frame` hit vs miss **for calls originating in cold prune**;
- selected slots on hit vs miss;
- mask population on hit vs miss;
- source environment shape (`Cons` / `Framed`) on entry;
- repeated `(raw-env-pointer, mask)` pairs reaching the cold path despite the existing one-entry/direct-map memo layers.

Run the frozen semantic corpus and the same dominant workload (`grind-ring-5`, plus Cedar/CSLib when available under the same runner contract).

No optimization is permitted in E0031.

## Precommitted interpretation

### Pattern A — materialization-heavy interner hits

If a substantial share of cold projection cost ends in `intern_frame` hits, especially with nontrivial selected-slot counts, then a representation/access candidate is justified.

Next candidate: expose a cheap pre-materialization identity/index that can recognize repeated observed projections before rebuilding slot vectors.

Residual remains R8/R3.

### Pattern B — hits are cheap; misses dominate work

If most slot traversal/materialization belongs to interner misses, then early identity lookup cannot remove enough work.

Reject the canonical-access hypothesis and profile the miss construction path instead (R2 Cost).

### Pattern C — repeated raw `(env,mask)` pairs dominate

Then the architecture already has the right canonical representation and the problem is merely insufficient access caching. Test the smallest access-index intervention before any ontology change.

### Pattern D — repeated raw pairs are rare but equivalent canonical outputs recur

This is the strongest evidence for a real representation/access barrier: different raw histories collapse to the same observed environment, but equivalence is discovered too late.

That is the case in which a persistent projection fingerprint / quotient-level access object is justified.

## Admission rule

E0031 is diagnostic only and cannot be admitted as a performance capability. Any subsequent intervention must independently clear semantic, causal, resource, and reproducibility gates.
