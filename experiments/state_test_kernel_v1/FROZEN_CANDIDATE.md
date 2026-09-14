# State–Test Kernel V1 — Frozen Reduction Candidate

**Status:** FROZEN BEFORE DEDICATED FALSIFICATION  
**Date:** 2026-09-14  
**Parent candidate:** WCD V1 remains unchanged at `978af4e94815128b4c517562f9a0bae26eea1e55`.

This candidate tests whether the warranted-consequential-difference formulation can be reduced further to a state–test evaluation pairing and the kernel of its future-consequence map.

No failed gate may be repaired in this V1 file.

---

## 1. Evaluation pairing

Let

```math
e:X\times T\to Y
```

where:
- `X` = possible situations / histories / candidate presents,
- `T` = authorized tests / contexts / future continuations,
- `Y` = consequences.

Curry:

```math
\Phi:X\to Y^T,
\qquad
\Phi(x)=\big(t\mapsto e(x,t)\big).
```

---

## 2. Consequential kernel

```math
x\sim y
\iff
\Phi(x)=\Phi(y)
\iff
\forall t\in T:\;e(x,t)=e(y,t).
```

Thus

```math
\sim=\ker\Phi
=
\bigcap_{t\in T}\ker(e_t).
```

A consequential distinction is exactly a pair outside `ker Phi`.

---

## 3. State quotient

```math
Q=X/\ker\Phi
```

and, in Set,

```math
X/\ker\Phi\cong\operatorname{im}\Phi.
```

State is derived: an equivalence class of histories with the same authorized future consequential signature.

---

## 4. Exact sufficiency

For a representation

```math
r:X\to R,
```

call `r` sufficient when

```math
\Phi=g\circ r
```

for some `g`.

Then

```math
\ker r\subseteq\ker\Phi.
```

The future-consequence quotient is the unique coarsest exact sufficient representation up to relabeling.

Equivalently, under deterministic factorization ordering,

```math
r_1\succeq r_2
\iff
\exists f:\;r_2=f\circ r_1,
```

and

```math
r\text{ sufficient}\iff r\succeq\Phi.
```

---

## 5. Representation error

For the current representation `r_t`, let

```math
K_t=\ker r_t,
\qquad
K^*=\ker\Phi.
```

Then

```math
\mathrm{Problem}(R_t)=K_t\triangle K^*.
```

The discrepancy has two components:

```math
K_t\setminus K^*
```

false merges requiring split, and

```math
K^*\setminus K_t
```

false splits permitting merge.

Genesis and Solvent are derived correction directions.

---

## 6. State–probe duality

For a probe subset `S subseteq T` define

```math
R(S)=\bigcap_{t\in S}\ker e_t.
```

For an equivalence relation `R` on `X` define

```math
T(R)=\{t\in T:R\subseteq\ker e_t\}.
```

Claim:

```math
S\subseteq T(R)
\iff
R\subseteq R(S).
```

This is an order-reversing Galois connection between retained distinctions and admissible probes.

Rows and columns of the evaluation matrix may both be quotiented by equality of their evaluation profiles.

---

## 7. Probe basis

A probe basis is a subset `S subseteq T` such that

```math
R(S)=\ker\Phi.
```

In finite systems, inclusion-minimal probe bases may be sought. They need not be unique.

---

## 8. Dynamic closure

When future continuations form a monoid `M` and

```math
e(x,s)=C(x\circ s),
```

full future equivalence is:

```math
x\sim y
\iff
\forall s\in M:C(x\circ s)=C(y\circ s).
```

Then authorized continuation closure implies right congruence:

```math
x\sim y\Rightarrow x\circ a\sim y\circ a.
```

Without closure of the test family under continuation, descriptive equivalence need not be executable state.

---

## 9. Epistemic UNKNOWN via possible kernels

Under finite evidence, suppose:

- `E_eq` = pairs definitely equivalent,
- `E_sep` = pairs definitely separated.

Define

```math
\mathcal K_E
=
\{K:
K\text{ is an equivalence relation},
E_{eq}\subseteq K,
K\cap E_{sep}=\varnothing
\}.
```

For a pair `x,y`:
- if all `K in mathcal K_E` merge them: `EQ`;
- if all `K in mathcal K_E` separate them: `SEP`;
- otherwise: `UNKNOWN`.

This section is intentionally frozen exactly in this form for falsification.

---

## 10. Stochastic / approximate extension

The exact deterministic kernel may be extended by allowing

```math
e(x,t)\in\Delta(Y).
```

Exact equivalence remains equality of all test-conditioned consequence distributions.

For approximate comparison define

```math
d_T(x,y)=\sup_{t\in T}d_Y(e(x,t),e(y,t)).
```

Exact equivalence is `d_T=0`. Approximate abstraction may use `d_T<=epsilon`, but epsilon-closeness is not assumed transitive; approximate systems may require a pseudometric rather than a literal quotient.

---

## 11. Falsifiers

V1 fails or requires explicit repair if any of the following occurs:

1. the kernel quotient is not the coarsest exact sufficient representation in a finite exact case;
2. the stated state–probe Galois law fails;
3. a closed future-test family yields a non-right-congruent consequential quotient;
4. a non-closed family is incorrectly guaranteed right congruent;
5. the possible-kernel EQ/SEP/UNKNOWN rule gives contradictory epistemic commitments;
6. deterministic factorization and kernel refinement disagree;
7. the symmetric-difference decomposition omits a representation error;
8. row/column quotient claims fail on a finite evaluation matrix.

A failed result must be recorded before any V2 repair.
