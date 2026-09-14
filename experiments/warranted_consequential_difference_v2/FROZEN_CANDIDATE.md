# Warranted Consequential Difference V2 — Consistency-Gated Candidate

**Status:** FROZEN BEFORE V2 TESTS  
**Date:** 2026-09-14

WCD V1 (`978af4e94815128b4c517562f9a0bae26eea1e55`) is permanently falsified on the empty-compatible-world case because its universal DIST and EQ formulas become simultaneously true by vacuity.

V2 makes one repair only:

> **Warranted consequence quantification is licensed only when the compatible world/model class is nonempty.**

Everything else is inherited unchanged on consistent evidence.

## 1. Consistency gate

Let `W(E)` be the worlds/laws still compatible with current evidence.

Before DIST/EQ/UNKNOWN:

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

## 2. Warranted consequential relation

Only for nonempty `W(E)`:

```math
DIST_E(P,Q)
\iff
\forall\omega\in W(E)\;\exists s\in\Pi_E:
C_\omega(P;s)\neq C_\omega(Q;s).
```

```math
EQ_E(P,Q)
\iff
\forall\omega\in W(E)\;\forall s\in\Pi_E:
C_\omega(P;s)=C_\omega(Q;s).
```

Otherwise:

```text
UNKNOWN
```

A robust separator

```math
RSEP_E(P,Q)
\iff
\exists s\in\Pi_E\;\forall\omega\in W(E):
C_\omega(P;s)\neq C_\omega(Q;s)
```

is sufficient for DIST but not required.

## 3. Derived correction directions

- current merge + DIST -> SPLIT;
- current distinction + EQ -> MERGE;
- UNKNOWN -> do not decide;
- INCONSISTENT_EVIDENCE -> do not decide and repair/clarify authority rather than the represented world.

Genesis and Solvent remain derived directions.

## 4. Joint sufficiency

The primitive comparison is between whole candidate presents/configurations.

```math
F_E=
\operatorname{Min}_{\preceq_E}
\{P':P'\text{ is lawful and jointly preserves all warranted protected consequence}\}.
```

Individual ablations do not establish context-free necessity.

## 5. Dynamic coherence

A descriptive quotient used as executable state must be right congruent under authorized continuation. When the authorized future family is closed under continuation, this follows from full future equivalence.

## 6. Ground / measure / preference

Semantic ground, developmental measurements, and preference remain distinct. Preference orders only already-lawful realizations and cannot redefine ground.

## 7. Relationship to State–Test Kernel V2

For each resolved compatible world `omega`, define:

```math
e_\omega:X\times T\to Y,
\qquad
\Phi_\omega(x)=\big(t\mapsto e_\omega(x,t)\big).
```

Then exact world-relative equivalence is `ker Phi_omega`.

WCD V2 is the epistemic layer over a nonempty set of such possible consequential kernels:
- EQ when every compatible kernel merges the pair;
- DIST when every compatible world has some authorized separator;
- UNKNOWN when compatible worlds disagree;
- INCONSISTENT_EVIDENCE when there are no compatible worlds.

## 8. Falsifiers

V2 fails if:
1. any nonempty evidence state receives a different DIST/EQ/UNKNOWN result from frozen WCD V1;
2. the empty evidence/model class licenses DIST or EQ;
3. DIST and EQ overlap on any nonempty world set;
4. RSEP fails to imply DIST;
5. a DIST case requiring world-specific separators is lost by requiring one common separator;
6. joint configuration minimality or the ground/preference separation fails.
