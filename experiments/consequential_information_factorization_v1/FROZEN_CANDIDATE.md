# Consequential Information Factorization V1 — Frozen Candidate

**Status:** FROZEN BEFORE DEDICATED TESTS  
**Date:** 2026-09-14

Parent results:
- State–Test Kernel V2 exact algebra survived.
- Exact kernel equality was shown insufficient to order noisy representations.

This candidate tests the next reduction proposed by the state–test analysis:

> **Consequential information is ordered by factorization/post-processing, with kernel refinement as the deterministic special case.**

---

## 1. Representations as channels

Allow a representation to be deterministic or stochastic:

```math
r:X\leadsto R.
```

A consequence representation is similarly a channel:

```math
\Phi:X\leadsto Z.
```

---

## 2. Information preorder

Define:

```math
r_1\succeq r_2
\iff
\exists G:\; r_2 = G\circ r_1
```

where `G` is an allowed post-processing / stochastic garbling channel.

Interpretation:

> `r_1` contains at least as much consequential information as `r_2`.

This relation should be reflexive and transitive. Mutual factorization defines informational equivalence.

---

## 3. Consequential sufficiency

A representation `r` is sufficient for consequence channel `Phi` when:

```math
r\succeq\Phi
```

i.e.

```math
\Phi = G\circ r
```

for some post-processing channel `G`.

Minimal exact sufficiency, when `Phi` itself is an admissible representation, is the mutual-factorization class of `Phi`:

```math
r\simeq\Phi.
```

---

## 4. Deterministic reduction

When `r_1,r_2` are deterministic maps:

```math
r_1\succeq r_2
\iff
\ker r_1\subseteq\ker r_2.
```

Therefore exact state–test quotient refinement is the deterministic special case of the factorization order.

---

## 5. Stochastic strictness

In stochastic settings, identical exact kernels need not imply equal information.

Two channels can separate exactly the same state pairs while one is a noninvertible stochastic garbling of the other.

Therefore:

```math
\ker r_1 = \ker r_2
```

does not imply:

```math
r_1\simeq r_2.
```

---

## 6. Developmental boundary

Factorization orders consequential information. It does not by itself replace:

- warrant / compatible-world consistency;
- lawfulness constraints;
- developmental preference among already-sufficient realizations.

Those remain typed above the information order.

---

## 7. Falsifiers

V1 fails if:

1. the channel factorization relation is not reflexive/transitive on a finite stochastic channel family;
2. deterministic factorization disagrees with deterministic kernel refinement;
3. mutual factorization can change exact state-equivalence kernel;
4. every same-kernel stochastic pair is mutually factorization-equivalent;
5. a representation can be sufficient for Phi without factorizing Phi;
6. a strict factorization chain cannot be exhibited from more informative to less informative channels.
