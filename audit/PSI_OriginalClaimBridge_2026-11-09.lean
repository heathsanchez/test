import AaronsonAmbainis.Main

/-!
# Independent statement-entailment adapter for the Aaronson–Ambainis conjecture

STATUS: CANDIDATE / UNCOMPILED. This artifact is an audit experiment, not a
kernel-checked result. It is intentionally outside the upstream repository.

Source: Aaronson and Ambainis, "The Need for Structure in Quantum Speedups",
arXiv:0911.0996v3, Conjecture 6. The historical `(ε/d)^{O(1)}` is interpreted
as the existence of a *single positive natural exponent* for all instances.
This interpretation requires separate domain-expert acceptance.

Reproduction on a compatible toolchain:
  copy to the root of a checkout of PSI commit 2a6ceaef872ae993708950f951989134084b851a
  lake env lean PSI_OriginalClaimBridge_2026-11-09.lean

The definitions below do not refer to PSI's theorem statement. The bridge
itself imports PSI's Main module as the premise to be audited.
-/

namespace IndependentAAAudit

private noncomputable def cubeValue (N : ℕ) (p : MvPolynomial (Fin N) ℝ)
    (X : Fin N → Bool) : ℝ :=
  MvPolynomial.eval (fun i => if X i then (1 : ℝ) else 0) p

private noncomputable def cubeMean (N : ℕ) (p : MvPolynomial (Fin N) ℝ) : ℝ :=
  (∑ X : Fin N → Bool, cubeValue N p X) / 2 ^ N

private noncomputable def cubeVariance (N : ℕ) (p : MvPolynomial (Fin N) ℝ) : ℝ :=
  (∑ X : Fin N → Bool, (cubeValue N p X - cubeMean N p) ^ 2) / 2 ^ N

private noncomputable def cubeInfluence (N : ℕ) (p : MvPolynomial (Fin N) ℝ)
    (i : Fin N) : ℝ :=
  (∑ X : Fin N → Bool,
    (cubeValue N p X - cubeValue N p (Function.update X i (!X i))) ^ 2) / 2 ^ N

/-- Conjecture 6 with the original *exact degree* premise and an explicit
    existential, uniform interpretation of the constant hidden in `O(1)`.
    No PSI-defined propositions appear in this specification. -/
def OriginalConjecture6 : Prop :=
  ∃ k : ℕ, 0 < k ∧
    ∀ (N d : ℕ) (p : MvPolynomial (Fin N) ℝ), p.totalDegree = d →
      (∀ X : Fin N → Bool, 0 ≤ cubeValue N p X ∧ cubeValue N p X ≤ 1) →
      ∀ ε : ℝ, 0 < ε → cubeVariance N p ≥ ε →
        ∃ i : Fin N, cubeInfluence N p i ≥ (ε / (d : ℝ)) ^ k

/-- Intended bridge: the published exponent `7` instantiates the historical
    `O(1)` and an exact-degree instance is an at-most-degree instance.
    Do not claim success without a fresh native Lean compiler result. -/
theorem printed_implies_original
    (h : AaronsonAmbainis.PrintedConjecture) : OriginalConjecture6 := by
  refine ⟨7, by norm_num, ?_⟩
  intro N d p hDegree hBound ε hε hVar
  have hBound' :
      ∀ X : Fin N → Bool,
        0 ≤ MvPolynomial.eval (fun i => if X i then (1 : ℝ) else 0) p ∧
          MvPolynomial.eval (fun i => if X i then (1 : ℝ) else 0) p ≤ 1 := by
    simpa only [cubeValue] using hBound
  have hVar' :
      (∑ X : Fin N → Bool,
        (MvPolynomial.eval (fun i => if X i then (1 : ℝ) else 0) p
          - (∑ Y : Fin N → Bool,
              MvPolynomial.eval (fun i => if Y i then (1 : ℝ) else 0) p) / 2 ^ N) ^ 2)
        / 2 ^ N ≥ ε := by
    simpa only [cubeVariance, cubeMean, cubeValue] using hVar
  obtain ⟨i, hi⟩ := h N d p (le_of_eq hDegree) hBound' ε hε hVar'
  refine ⟨i, ?_⟩
  simpa only [cubeInfluence, cubeValue] using hi

/-- Final consumer: given the public theorem, the separately stated original
    conjecture is the deliverable (not a proof of the quantum reduction). -/
theorem historical_conjecture : OriginalConjecture6 :=
  printed_implies_original AaronsonAmbainis.aaronson_ambainis

end IndependentAAAudit

#print axioms IndependentAAAudit.historical_conjecture
