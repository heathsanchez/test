import Std

namespace FiniteVersionSpaceAdmitsFiniteCompleteTests

/-- A finite residual-relative hypothesis class of global Bool-valued
    constructors. -/
variable {n : Nat} (F : Fin n → Nat → Bool)

/-- Pairwise extensional distinction: different hypotheses disagree somewhere. -/
def PairwiseDistinguishable : Prop :=
  ∀ i j : Fin n, i ≠ j → ∃ x : Nat, F i x ≠ F j x

/-- Choose one deciding context for each ordered pair of hypotheses. -/
noncomputable def decidingContext
    (h : PairwiseDistinguishable F) (i j : Fin n) : Nat :=
  if hij : i = j then 0 else Classical.choose (h i j hij)

/-- The chosen context separates every distinct pair. -/
theorem decidingContext_separates
    (h : PairwiseDistinguishable F)
    {i j : Fin n} (hij : i ≠ j) :
    F i (decidingContext F h i j) ≠ F j (decidingContext F h i j) := by
  simp only [decidingContext, dif_neg hij]
  exact Classical.choose_spec (h i j hij)

/-- Finite verifier signature: evaluate a hypothesis at the n² pair-indexed
    deciding contexts.  The codomain is finite because Fin n × Fin n is finite. -/
noncomputable def finiteSignature
    (h : PairwiseDistinguishable F) (k : Fin n) :
    (Fin n → Fin n → Bool) :=
  fun i j => F k (decidingContext F h i j)

/-- The finite signature is injective on the finite version space. -/
theorem finite_signature_injective
    (h : PairwiseDistinguishable F) :
    Function.Injective (finiteSignature F h) := by
  intro i j hsig
  by_contra hij
  have hpoint := congrFun (congrFun hsig i) j
  exact (decidingContext_separates F h hij) hpoint

/-- Therefore a finite hypothesis class that is extensionally pairwise distinct
    always admits a finite complete verifier test family: at most n² selected
    contexts suffice for exact identification within that class. -/
theorem finite_version_space_admits_finite_complete_tests
    (h : PairwiseDistinguishable F) :
    ∃ sig : Fin n → (Fin n → Fin n → Bool), Function.Injective sig := by
  exact ⟨finiteSignature F h, finite_signature_injective F h⟩

/-- Completeness is relative to the hypothesis class, not unrestricted function
    space.  Equal finite signatures force equality of hypothesis indices. -/
theorem signature_equality_forces_same_hypothesis
    (h : PairwiseDistinguishable F)
    {i j : Fin n}
    (hsig : finiteSignature F h i = finiteSignature F h j) :
    i = j :=
  finite_signature_injective F h hsig

#check decidingContext_separates
#check finite_signature_injective
#check finite_version_space_admits_finite_complete_tests
#check signature_equality_forces_same_hypothesis

end FiniteVersionSpaceAdmitsFiniteCompleteTests
