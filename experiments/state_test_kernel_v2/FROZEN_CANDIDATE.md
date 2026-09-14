# State–Test Kernel V2 — Consistency-Gated Reduction Candidate

**Status:** FROZEN BEFORE V2 TESTS  
**Date:** 2026-09-14

V1 (`9e6102ab8e1b1f2b3e10ae663a56d8178c975d3a`) is permanently falsified by the empty-compatible-kernel vacuity bug.

V2 makes one minimal repair:

> **No universal consequence statement may license EQ or DIST unless the current compatible model/kernel class is nonempty.**

The exact state–test algebra is otherwise unchanged.

---

## 1. Evaluation pairing and future signature

```math
e:X\times T\to Y,
\qquad
\Phi(x)=\big(t\mapsto e(x,t)\big).
```

Exact consequential equivalence:

```math
x\sim y
\iff
\Phi(x)=\Phi(y)
\iff
\forall t\in T:e(x,t)=e(y,t).
```

Thus

```math
\ker\Phi=\bigcap_{t\in T}\ker(e_t).
```

---

## 2. State quotient and exact sufficiency

```math
Q=X/\ker\Phi
\cong
\operatorname{im}\Phi.
```

For `r:X->R`, exact sufficiency means:

```math
\Phi=g\circ r
```

for some `g`, equivalently:

```math
\ker r\subseteq\ker\Phi.
```

Therefore the future-consequence quotient is the unique coarsest exact sufficient representation up to relabeling.

Deterministic information order:

```math
r_1\succeq r_2
\iff
\exists f:r_2=f\circ r_1.
```

Then `r` is sufficient iff `r >= Phi` in this factorization order.

---

## 3. Representation discrepancy

For current representation kernel `K_t` and consequence kernel `K^*`:

```math
\mathrm{Problem}(R_t)=K_t\triangle K^*.
```

- `K_t\setminus K^*`: false merges -> split.
- `K^*\setminus K_t`: false splits -> merge.

Both can occur simultaneously for incomparable partitions.

---

## 4. State–probe duality

For `S subseteq T`:

```math
R(S)=\bigcap_{t\in S}\ker e_t.
```

For state equivalence relation `R`:

```math
T(R)=\{t\in T:R\subseteq\ker e_t\}.
```

Claim:

```math
S\subseteq T(R)
\iff
R\subseteq R(S).
```

Rows and columns may both be quotiented by equality of their evaluation profiles.

A probe basis is any `S` with `R(S)=ker Phi`; inclusion-minimal bases may be nonunique.

---

## 5. Dynamic closure

If authorized continuations form a monoid `M` and

```math
e(x,s)=C(x\circ s),
```

then full future equivalence is right congruent:

```math
x\sim y
\Rightarrow
x\circ a\sim y\circ a.
```

This guarantee does not apply to a test family that is not closed under continuation.

---

## 6. Epistemic consistency gate

Let `W(E)` be the compatible worlds/laws remaining after evidence.

Before warranted consequence classification require:

```math
\boxed{W(E)\neq\varnothing.}
```

If:

```math
W(E)=\varnothing,
```

return:

```text
INCONSISTENT_EVIDENCE
```

(or the domain's corresponding inadequate-authority status), preserve the current present, and license neither split nor merge.

Only when `W(E)` is nonempty define:

```math
DIST_E(x,y)
\iff
\forall\omega\in W(E)\;\exists t\in T:
e_\omega(x,t)\neq e_\omega(y,t),
```

```math
EQ_E(x,y)
\iff
\forall\omega\in W(E)\;\forall t\in T:
e_\omega(x,t)=e_\omega(y,t).
```

Otherwise:

```text
UNKNOWN
```

A robust common separator

```math
\exists t\;\forall\omega:
e_\omega(x,t)\neq e_\omega(y,t)
```

is sufficient for DIST but not required.

---

## 7. Possible-kernel form

Given pair evidence `E_eq`, `E_sep`:

```math
\mathcal K_E=
\{K:
K\text{ equivalence relation},
E_{eq}\subseteq K,
K\cap E_{sep}=\varnothing
\}.
```

First require:

```math
\boxed{\mathcal K_E\neq\varnothing.}
```

If empty: `INCONSISTENT_EVIDENCE`.

If nonempty:
- all compatible `K` merge a pair -> EQ;
- all compatible `K` separate a pair -> SEP/DIST;
- otherwise -> UNKNOWN.

---

## 8. Approximate extension

For metric/pseudometric consequence space:

```math
d_T(x,y)=\sup_{t\in T}d_Y(e(x,t),e(y,t)).
```

Exact equivalence is `d_T=0`.

Threshold relation `d_T<=epsilon` is not assumed transitive and therefore is not automatically an equivalence quotient.

---

## 9. V2 falsifiers

V2 fails if:

1. any V1 exact algebraic claim that previously survived now fails;
2. any compatible-world set, including the empty set, receives contradictory EQ/DIST commitments;
3. any finite possible-kernel evidence state receives contradictory commitments;
4. an empty compatible model/kernel class licenses merge or split;
5. a nonempty compatible class fails to realize a proper EQ/DIST/UNKNOWN trichotomy;
6. closed future equivalence fails right congruence;
7. nonclosed tests are incorrectly guaranteed right congruent;
8. the state–probe Galois law fails.
