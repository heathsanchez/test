# Bounded canonical closure V1

2026-09-26. Global Collatz: **UNKNOWN**.

## Qualified claim

Every legal first-coefficient-crossing word of depth `j <= 271782` with canonical source `R > 1` has `M = 2^j(Y-R) < 0`.

This closes the bounded canonical residual, not just the minimal-counterexample subset. No published convergence computation, Rhin bound, or P16 estimate is assumed for this bounded consequence.

Parent state: `5242a12a17fadf50a028fde5eb7817230971e6bf` (V10). Qualified implementation: `04714672d4eb53ef1ab169c0823e82e83b42f984`. Hosted run `36227106830`, job `108363128252`, SUCCESS. Artifact `10901058141`, SHA-256 `cef86992e1aad4d6f247f5375ee0bedb4951604c6e9a99556bec4effb792cbb5`.

## Exact deduction

Write `2^j T^j(R)=3^q R+B` and `D=2^j-3^q>0`. V10's Lean-checked no-earlier-crossing lemma gives `3B <= q*3^q`. Thus `M>=0` would force

    R <= floor(q*3^(q-1)/D),  q>0.

The exact coefficient sweep covers all 171476 necessary pairs with `j<=271782` and `2^(j-1)<=3^q<2^j`. Its maximum cap is `7216089270`, attained at `(j,q)=(125743,79335)`, below `2^33`. The `q=0` case has `B=0` and cannot give positive non-descent.

The new source cover proves that every `1<R<2^33` has a finite first crossing and strictly descends at that crossing. First-crossing uniqueness therefore contradicts `M>=0` for the proposed word. This uses strict coefficient-stopping-time descent, not eventual convergence; V10 explicitly did not have this finite canonical implication from its external convergence floor alone.

## Exhaustive source cover

For `n=r+2^K u`, `0<=r<2^K`, induction for `i<=K` gives

    q_i(n)=q_i(r),
    T^i(n)=T^i(r)+3^q_i(r)*2^(K-i)*u.

The shift is even before each step, preserving parity. If the representative first crosses at `j<=K`, its nontrivial negative margin lifts to every tail because

    T^j(n)-n = T^j(r)-r + (3^q-2^j)*2^(K-j)*u.

The representative `r=1` has equality only at the trivial source; its positive tail lifts strictly descend. Every positive even source greater than one descends immediately. Representatives still live at K are continued for every tail in the finite source domain. The residue/tail partition is disjoint and exhaustive.

Two complete covers, K=20 and K=24, each account for all 4294967296 odd sources below `2^33`. They agree on the full crossing histogram, have largest crossing depth 447, and report zero nontrivial nondescending sources, unresolved cases, or arithmetic overflows. Their live-representative counts are 27328 and 286581; explicit continuation counts are 223870976 and 146729472 respectively. Histogram digest: `51fcdcce2c81ddae9cea127e2c68c4282eae7718a15020db9eab2da5660217b5`.

## Verification boundary

The full covers share one C++ implementation; different partitions are cross-checks, not independent implementations. Direct C++ with an independently indexed coefficient threshold, direct arbitrary-integer Python, and a prefix cover agree on every odd source below `2^20`. The V10 C++ big-integer coefficient checker is replayed freshly; its earlier independently implemented Python qualification remains part of the lineage. Unsigned-128 trajectory arithmetic rejects overflow. The prefix-reconstruction ranges are within that width.

The combined hosted gate rechecks `FirstCrossingBias.lean` and the source-product/crossing modules with pinned Lean. The general source-bound theorems depend only on `propext` and `Quot.sound`; no `sorryAx` or native-reduction trust extension is admitted. The large finite computations and the exhaustive prefix-cover implementation are **not** supplied as a complete Lean proof term. Authority is therefore mixed: exact computational certificate plus the stated algebra/formal interface, not an end-to-end Lean proof of this finite theorem.

## P37 semantic obstruction

The V10 graph's off-type competitor `(n,j)->(n,k)`, `k!=j`, is a rejection of the parent, not a residual successor. `formal/Collatz/P37Rejection.lean` proves this at all depths: an earlier crossing rejects first-crossing membership at j; a later crossing already proves no crossing at j. The concrete source 45127 is kernel-checked as not crossing at depth 111, so there is no obligation to follow it to depth129 to reject that parent candidate.

The general theorems use at most `propext` and `Quot.sound`; the concrete example uses no axioms. Qualification: `4db2890a20b2b22b1dd53de8253563e6fc097421`, run `36226898784`, repeated by the combined gate. A rank on these bookkeeping edges cannot be substituted for a proved residual-preserving transition rule. A different witness-changing P37 recursion is **not** ruled out.

Preserve failed semantic runs `36226612025` (concrete predicate decidability) and `36226649447` (concrete kernel recursion limit); the general statements were not weakened. Local direct full-range scanning and a redundant aggregate Python-cap replay hit runtime limits and provide no additional certificate.

## Remaining research

Universal canonical M-negativity beyond 271782, universal live-origin exhaustion, and exclusion of a positive source that never crosses are all **UNKNOWN**. Do not extend the finite result by induction without a new sound induction rule. The live-origin inequality remains a candidate rather than a supplied premise. Rejected routes remain rejected.

Reproduce with the committed workflow `.github/workflows/collatz-bounded-canonical-closure-v1.yml`; committed summary: `evidence/collatz-bounded-canonical-closure-v1/result.json`.
