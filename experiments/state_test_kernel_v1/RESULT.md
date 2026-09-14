# State–Test Kernel V1 — Falsification Result

**Frozen candidate:** `9e6102ab8e1b1f2b3e10ae663a56d8178c975d3a`  
**Test commit:** `0ad19d0ffb7494e867abdd6963db4fc43eb3dec7`  
**Workflow commit:** `576cbb9281e583ffabb077038b29e7cab5f148b8`  
**Run:** 34819099809  
**Job:** 103896286581  
**Artifact:** 10337214709  
**Digest:** `sha256:7270432c4b2ba318d592c5a1224868f831ab67d50a5824673fbc7efabbfaef19`

## Verdict

```text
FALSIFIED_STATE_TEST_KERNEL_V1
18/19 checks passed
```

## What survived

Exhaustive over all 4,096 binary 4-state x 3-test evaluation matrices:

- quotient cardinality = image(Phi) cardinality;
- exact sufficiency iff `ker(r) subseteq ker(Phi)`;
- future-consequence quotient is the unique coarsest exact sufficient partition;
- deterministic factorization order agrees with kernel refinement;
- the state–probe Galois law held for every state partition and every probe subset;
- collapsing duplicate probe columns preserved the full state kernel;
- every finite matrix had an inclusion-minimal probe basis;
- representation discrepancy decomposed exactly into false merges and false splits.

Probe-basis minimum-size distribution:
- size 0: 8 matrices
- size 1: 392
- size 2: 2,928
- size 3: 768

Exhaustive over all 5,832 deterministic 3-state / 2-action / binary-output systems:

- full future behavioral equivalence was always right congruent;
- a non-closed shallow test family produced an explicit right-congruence failure.

Approximate boundary:

- epsilon-closeness was explicitly non-transitive;
- finite sup-test distance obeyed the triangle inequality.

## Falsifier

The possible-kernel epistemic rule was not total/contradiction-free when the compatible kernel set was empty.

Across all 64 assignments of pairwise `E_eq` and `E_sep` evidence on three states:

- 40 evidence assignments produced `K_E = empty`;
- these yielded 120 pair-level cases where both universal statements
  "all compatible kernels merge" and "all compatible kernels separate"
  were vacuously true.

Simplest witness:

```text
E_eq  = {(0,1)}
E_sep = {(0,1)}
K_E   = empty
```

A transitive inconsistency also exists without direct overlap, e.g. evidence can force 0~1 and 1~2 while separately forcing 0 !~ 2.

Therefore V1's rule:

```text
all K in K_E merge -> EQ
all K in K_E separate -> SEP
otherwise UNKNOWN
```

requires an explicit consistency/adequacy precondition `K_E != empty`.

## Minimal repair suggested by the falsifier

Before EQ / SEP / UNKNOWN classification:

```math
\mathcal K_E = \varnothing
\quad\Longrightarrow\quad
\text{INCONSISTENT_EVIDENCE / INADEQUATE_AUTHORITY}
```

and no merge/split is licensed.

This is best interpreted as an epistemic-ground precondition rather than a new state/probe primitive.

V1 remains frozen and falsified.
