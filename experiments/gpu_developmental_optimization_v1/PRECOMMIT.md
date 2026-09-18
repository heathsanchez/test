# GPU Developmental Optimization V1 — Frozen Precommit Contract

This file freezes the Phase-A/B finite gate before the first authoritative target run.

## Question

Can exact optimization capabilities acquired on source kernel families reduce
developmental search on run-seeded untouched target kernels while preserving
exact reference semantics?

## Authority

The finite reference evaluator is the correctness authority. A transformation
may be promoted only when exhaustive input-domain replay proves semantic
equivalence and the frozen structural execution-cost metric strictly improves.

No finite result is described as a CUDA/Triton hardware speedup.

## Frozen IR

A kernel is a finite sequence of elementwise operations over integer vectors:

- `identity`
- `affine(a,b)`: `x ↦ a*x+b`

The exhaustive input carrier is every vector of length 3 with entries in
`{-2,-1,0,1,2}`.

Structural execution cost is:

`10 * number_of_operations + number_of_nontrivial_intermediates`.

It is an IR metric, not GPU wall time.

## Frozen candidate transformations

Search order:

1. `unsafe_drop_last` — negative control, normally fails verification.
2. `reverse_ops` — negative control, normally fails verification.
3. `swap_affine_coefficients` — negative control.
4. `remove_identity`.
5. `fuse_adjacent_affine`.

A promoted capability contains only transformation identity, applicability
signature, verified source evidence, expected cost effect and dependencies.

## Prospective split

Source kernels are fixed in source code.

Target instances are generated from SHA-256(`GITHUB_SHA:GITHUB_RUN_ID`) after
the tested commit exists. Target IDs/coefficients are not stored in promoted
capabilities.

## Arms

- COLD: search frozen transformation family in frozen order.
- WARM: try applicable verified capabilities first; fall back to COLD.
- RESTART: serialize and reload only promoted capabilities, then run WARM.
- SHAM: matched capability objects with impossible applicability signatures.
- ABLATION: remove the exact capability used by WARM, then fall back to COLD.

Every chosen optimized kernel is exhaustively reverified.

## Primary gate

WARM must use less developmental search than COLD, SHAM and ABLATION; RESTART
must match WARM; exact ablation must restore the cold frontier; every arm must
remain semantically exact.

Hardware promotion is a separate evidence object. If no GPU is present, the
workflow must record `GPU_HARDWARE_AUTHORITY_UNAVAILABLE` rather than turning
the finite IR result into a hardware claim.
