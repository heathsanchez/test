# E0034 — Parent-tail projection splice

## Residual

`rho = (R8 Access + R3 Redundancy, prune_env_cold Cons tails, existing parent projection knowledge is rediscovered after head-local work, canonical-env projection paths, high)`

## Evidence frozen before intervention

E0031: 59.4% of cold projections terminate in an already-existing canonical frame while raw `(env,mask)` repeats are only ~1.4%.

E0032: Cons walking exists but mean scan depth is only ~2.39; a heavyweight random-access environment is not yet justified.

E0033: among 707,979 nonzero Cons tails, 137,548 parent nodes already hold an exact one-entry prune result for the remaining tail mask: 19.43%. Every exact match had a usable result.

## Hypothesis

The current representation already contains useful suffix knowledge. Before inventing a new quotient fingerprint, compose that knowledge inside `prune_env_cold`: after consuming the current Cons head, if the parent has an exact cached projection for the remaining tail mask, splice the cached projected tail into the current projection and terminate the walk.

No new semantic object is introduced. This is Rule F (composition-before-invention).

## Frozen arms

- A0: reconstructed A6.
- A1: A6 + parent-tail splice.
- A1-abl: identical E0034 source with the splice compile-time disabled.

Primary metric: paired CPU time.
Secondary: wall, RSS, cold prune calls, splice hits, Cons steps avoided estimate.

Semantic gate: complete frozen Arena good/bad corpus before resource interpretation.

## Interpretation

- A1 improves primary CPU, passes semantics, and A1-abl does not share the gain: promote composition candidate to protected resource gate.
- A1 ~= A0/A1-abl: reject suffix composition as insufficient; proceed to quotient-fingerprint separator.
- A1 hurts total CPU/RSS despite fewer scans: R12 displacement; reject.
- Any semantic mismatch: R9 immediate reject.
- Build/runner failure: R10 only.

## Information delta

- preserved: exact selected value pointers, mask positions, level-substitution identity;
- exposed: parent suffix projection already computed by existing machinery;
- hidden/lost: none intended;
- recoverable: full original raw environment remains unchanged.
