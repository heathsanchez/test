# Coupled Collatz residual — proof boundary

Status: theorem-discovery branch. This is **not** a Collatz proof.

## Verified exact local gate

For an ordinary positive odd integer n under the shortcut map,

    T(n) = (3n+1)/2,

we have

    T(n)+1 = 3(n+1)/2.

Hence every consecutive odd shortcut step removes exactly one factor 2 from
n+1. An ordinary integer therefore cannot follow an all-odd continuation
forever. The executable gate in `collatz_minus_one_cycle_breaker.py` checks
this identity and the associated residue behavior independently over a large
finite control set; the identity itself is elementary algebra.

## Candidate recurrent residual

The bounded Complete-O coupled probe repeatedly exposes the residue

    d == -1 (mod 3^J)

as the apparent recurrent state when the 3-adic precision is truncated. The
odd shortcut branch preserves this residue; the even branch exits it.

This observation is **not yet a universal classification theorem**. A bounded
SCC census cannot establish that every recurrent RIGID component of the
unbounded concrete residual is this class.

## Exact missing theorem

A completion requires a finite sound abstraction H of every concrete
nonterminal coupled state, with universal transition closure:

    concrete s -> s'
    implies
    alpha(s) ->_H alpha(s').

After adding enough state to distinguish the finite odd-run countdown, the
reachable RIGID part of H must be proved acyclic.

Equivalently, it is sufficient to prove:

1. every concrete unresolved state is represented;
2. every concrete continuation is represented by an abstract edge;
3. every abstract terminal outcome carries its universal lower-merge theorem;
4. every abstract RIGID cycle is impossible for ordinary integers.

Only after these are proved may SCC acyclicity be used to derive a finite
height and hence universal certificate termination.

## Why this boundary is deliberately strict

Finite-depth stabilization, repeated appearance of -1 modulo growing powers of
3, and exhaustive SCC checks are discovery evidence only. None establishes
the required universal abstraction theorem. The branch therefore prints
`GLOBAL_STATUS CONDITIONAL` until that theorem is supplied.

The lower-merge strong-induction finish already exists separately in
`formal/CollatzFirstDescentBoundary.lean`.
