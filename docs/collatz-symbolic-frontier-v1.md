# Exact symbolic descent frontier V1

This is an executable direct-descent certificate compiler, with an exact finite
partition audit and explicit residual. It is not a Collatz proof or a full
implementation of the Complete-O/lower-merge portfolio.

## Certificate

Each record states n=2^k q+b and T^k(n)=3^c q+d for q>=0. The compiler uses
binary source refinement; the independent verification routine instead replays
the affine map (a*q+d) over the whole cylinder, checking at every step that a
is even so parity is independent of q. It rejects an incorrect endpoint or c.

When A=2^k-3^c>0, the exact strict-descent threshold is
Q=max(0,floor((d-b)/A)+1). The certificate covers q>=Q, n>1. Every smaller
positive source n>1 is retained as an explicit scalar exception. A capped
scalar attempt returns UNKNOWN if it cannot find descent. No timeout is closure.

Terminal certificates and residual cylinders must be pairwise prefix-disjoint,
and their exact dyadic measures must sum to one. These finite prefix conditions
establish a partition of all nonnegative ordinary integers. Terminal tails and
their explicit exceptions split the terminal cylinders; n=0,1 are outside the
lower-descent obligation. Each residual record also passes affine verification.

## Depth-18 result

* 1752 terminal cylinder certificates.
* 7495 unresolved cylinders, exact residue density 7495/262144.
* Zero positive scalar exceptions in this run.
* Evaluation interval 65537 through 131072: 63673 symbolically closed;
  1863 explicitly unresolved.
* Each admitted certificate propagates to its matching arithmetic progression
  of evaluation obligations. There are 63673 application guard visits and
  zero forward steps during application.
* Independent qualification replay performs 167092 forward steps and verifies
  every propagated descent. Removing the bank removes all symbolic closures.
* Serialization/reload reproduces exactly the same discharged obligations.

The evaluation interval was fixed in code before this run. It is a bounded
application check, not evidence for universal coverage or a statistically sealed
benchmark. The certificates themselves are universal on their checked guards.

## Cost and claim boundary

Zero application forward steps does not mean zero work. Compilation, affine
verification, integer arithmetic, indexing by residue progression, and independent
qualification replay all cost work. No end-to-end speed advantage over direct
iteration has been measured here. The previous stepwise-replay dominance result
remains protected and does not apply to this different execution/cost model.

The graph in this version is an exact source-refinement tree with certificate
edges into integer obligations. There is no inferred quotient, general multi-hop
composition, asynchronous cancellation, or universal rank. Refinement depth is
bounded. The number of residual cylinders can grow even when their total residue
density decreases; density alone cannot establish ordinary-integer termination.

The precise remaining obligation is to close every residual and any future
scalar exception using sound certificates, or establish a well-founded argument
for their continuing refinement. Existing S_k, 119/104, and local-departure
obstructions remain unchanged. CI success means exact bookkeeping and certificate
checks passed while the unresolved regions remain unresolved.

## Reproduce

```
python -m unittest discover -s experiments -p test_collatz_symbolic_frontier.py -v
python experiments/collatz_symbolic_frontier.py --depth 18 --output /tmp/symbolic-frontier
```
