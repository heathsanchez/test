# Higher-Arity Test-Language Expansion V1 — Frozen Candidate

**Status:** FROZEN BEFORE TEST  
**Date:** 2026-09-14

Purpose: test whether the State–Test Kernel survives a family where every
lower-arity projection is insufficient.

## Candidate

The universal object is the evaluation relation, not a fixed pairwise probe language.

For an n-ary relation hypothesis x, authorized tests may themselves need arity n.
A fixed test family restricted to proper coordinate projections can induce a false merge.

The developmental response should be:

```text
lower-arity test kernel merges alternatives
+ certified separator exists only outside current test language
-> expand T
-> recompute Phi
-> split if future consequence now differs
```

The kernel law itself must remain unchanged.

## Frozen adversary

For n >= 3 over bits, define:

- E_n = all n-bit tuples of even parity;
- O_n = all n-bit tuples of odd parity.

Claim:

1. every projection onto any proper coordinate subset S has the same image for E_n and O_n;
2. therefore every fixed proper-subtuple probe language merges E_n and O_n;
3. a full n-ary membership test separates them;
4. the minimum separating arity is n.

## Falsifiers

V1 fails if any n in the tested family:
- has a proper-coordinate projection that distinguishes E_n from O_n; or
- cannot be distinguished by an n-ary test; or
- requires changing the state–test kernel rather than only expanding T.
