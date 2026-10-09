# Collatz V108 — source-relative prefix and inverse-odd merger reclosure

Status: **CANDIDATE until pinned Lean/Actions qualification passes**. Global Collatz **UNKNOWN**. No QED.

## Objective / protected consequence

Use the V65–V66 future-coalescence interface, not a local trajectory rank. A successful witness for a positive source n>1 is a strictly smaller p>0 and finite a,b with shortcut^a(n)=shortcut^b(p).

Base authority: V106 has both signs of genuine admitted returns; monotone return-defect ranking is REJECTED. V107 checked only depth-12 terminal coefficients and counted 3,302 / 4,096 guarded cylinders (794 UNKNOWN).

## New V108 experiment

For each residue 0<=r<4096 and each prefix 1<=j<=12, derive the exact affine family

    shortcut^j(r + 4096*q) = x_j + a_j*q,
    a_j = 2^(12-j) * 3^oddCount(r,j).

Two competing *uniform* source-merger witnesses are tested:

1. **Direct:** a_j<4096 and x_j+a_j*q < r+4096*q. This gives p=shortcut^j(n)<n and merger clocks a=j,b=0.
2. **Inverse odd:** oddCount>0, x_j>=2, x_j mod 3=2, 2*a_j<3*4096, and 2*(x_j+a_j*q)-1<3*(r+4096*q). Then p=(2*shortcut^j(n)-1)/3 is positive odd, p<n, and shortcut(p)=shortcut^j(n), giving merger clocks a=j,b=1.

For each possible witness, an exact threshold q_min is calculated algebraically. The only promoted families with q_min=1 are r=0 and r=1, whose missing offsets are source 0 and terminal 1 respectively; for every n>1 in these cylinders the guard holds. The script retains source residue, selected prefix, odd count, exact coefficient/intercept and threshold per cylinder. Five offset checks per selected witness are regression tests only, not the universal reason the certificate works.

**Local bounded outcome (subject to CI requalification):**
- 3,870 direct certificates,
- 34 additional inverse-odd certificates,
- 192 UNKNOWN cylinders,
- 3,904 / 4,096 source cylinders admitted uniformly for n>1.

Lean module `formal/Collatz/CylinderCoalescence.lean` formalizes the all-offset affine shift, the direct all-offset merger constructor, the exact odd predecessor, and the inverse-odd all-offset merger constructor. The Python enumerator is a bounded witness compiler: **individual numerical witness-selection and the 3,904 count are executable evidence, not 3,904 separately kernel-checked Lean instances.**

## Critical boundary

A residue cylinder can contain infinitely many positive sources. A fixed finite depth's coverage of many residue cylinders does not prove all natural sources merge downward, and the 192 unresolved cylinders are neither Collatz counterexamples nor proved nonmergers. Finite source exceptions must not be silently lost, nor may a 2-adic survivor be treated automatically as a fixed natural orbit.

## Next cheapest decisive test

Replay existing verified V65/V66/q7 lower-source merger families specifically on the 192 UNKNOWN residue cylinders, and emit the first uncovered *source-relative* constraint for each. Do not promote deeper modulus or a sign-based return rank without a checked new lower-source-merger consequence.

Global Collatz: UNKNOWN. No QED.
