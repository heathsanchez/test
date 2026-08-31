import Std

namespace FiniteVersionSpaceAdmitsFiniteCompleteTests

/-- Pairwise extensional distinction: different hypotheses disagree somewhere. -/
def PairwiseDistinguishable {n : Nat} (F : Fin n → Nat → Bool) : Prop :=
  ∀ i j : Fin n, i ≠ j → ∃ x : Nat, F i x ≠ F j x

noncomputable def decidingContext {n : Nat}
    (F : Fin n → Nat → Bool)
    (h : PairwiseDistinguishable F) (i j : Fin n) : Nat :=
  if hij : i = j then 0 else Classical.choose (h i j hij)

theorem decidingContext_separates {n : Nat}
    (F : Fin n → Nat → Bool)
    (h : PairwiseDistinguishable F)
    {i j : Fin n} (hij : i ≠ j) :
    F i (decidingContext F h i j) ≠ F j (decidingContext F h i j) := by
  simp only [decidingContext, dif_neg hij]
  exact Classical.choose_spec (h i j hij)

/-- Pair-indexed verifier signature; there are only n² deciding contexts. -/
noncomputable def finiteSignature {n : Nat}
    (F : Fin n → Nat → Bool)
    (h : PairwiseDistinguishable F) (k : Fin n) :
    (Fin n → Fin n → Bool) :=
  fun i j => F k (decidingContext F h i j)

theorem finite_signature_injective {n : Nat}
    (F : Fin n → Nat → Bool)
    (h : PairwiseDistinguishable F) :
    Function.Injective (finiteSignature F h) := by
  intro i j hsig
  by_cases hij : i = j
  · exact hij
  · have hpoint :
        F i (decidingContext F h i j) =
        F j (decidingContext F h i j) := by
      exact congrFun (congrFun hsig i) j
    exact False.elim ((decidingContext_separates F h hij) hpoint)

/-- A finite extensionally distinct version space always admits a finite complete
    verifier test family.  The constructed family has at most n² contexts. -/
theorem finite_version_space_admits_finite_complete_tests {n : Nat}
    (F : Fin n → Nat → Bool)
    (h : PairwiseDistinguishable F) :
    ∃ sig : Fin n → (Fin n → Fin n → Bool), Function.Injective sig := by
  exact ⟨finiteSignature F h, finite_signature_injective F h⟩

theorem signature_equality_forces_same_hypothesis {n : Nat}
    (F : Fin n → Nat → Bool)
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
