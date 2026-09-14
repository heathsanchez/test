import PartialGroupCoordinate
import PresentationInvariance

namespace AC

/-- A presentation of the trivial group has full relator normal closure. -/
theorem relatorNormalClosure_eq_top_of_presentsTrivial {n : ℕ}
    (R : Relators n) (h : PresentsTrivialGroup R) :
    relatorNormalClosure R = ⊤ := by
  letI : Subsingleton (Word n ⧸ relatorNormalClosure R) := by
    simpa [PresentsTrivialGroup, PresentedGroup, relatorNormalClosure] using h
  rw [eq_top_iff]
  intro x _hx
  have hq :
      QuotientGroup.mk' (relatorNormalClosure R) x = 1 :=
    Subsingleton.elim _ _
  exact (QuotientGroup.eq_one_iff _).mp hq

/-- In a trivial presentation, the omitted coordinate normally generates the
partial-presentation group defined by all the other relators. -/
theorem coordinateClass_normalClosure_eq_top {n : ℕ}
    (R : Relators n) (i : Fin n)
    (htriv : PresentsTrivialGroup R) :
    Subgroup.normalClosure
        ({coordinateClass R i} : Set (PartialPresentationGroup R i))
      = ⊤ := by
  let N := otherRelatorNormalClosure R i
  letI : N.Normal := by
    unfold N otherRelatorNormalClosure sourceNormalClosure
    infer_instance
  let π : Word n →* (Word n ⧸ N) := QuotientGroup.mk' N

  have hfull : Subgroup.normalClosure (Set.range R) = ⊤ := by
    simpa [relatorNormalClosure] using
      relatorNormalClosure_eq_top_of_presentsTrivial R htriv

  have hmap :=
    Subgroup.map_normalClosure
      (Set.range R) π (QuotientGroup.mk'_surjective N)

  have himageTop :
      Subgroup.normalClosure (π '' Set.range R) = ⊤ := by
    rw [← hmap, hfull]
    simp [π]

  have himage :
      π '' Set.range R ⊆
        Subgroup.normalClosure
          ({coordinateClass R i} : Set (PartialPresentationGroup R i)) := by
    rintro y ⟨x, ⟨j, rfl⟩, rfl⟩
    by_cases hji : j = i
    · subst j
      exact Subgroup.subset_normalClosure (by simp [π, N, coordinateClass])
    · have hRjN : R j ∈ N := by
        change R j ∈ Subgroup.normalClosure (otherRelatorSet R i)
        exact Subgroup.subset_normalClosure ⟨j, hji, rfl⟩
      have hz : π (R j) = 1 :=
        (QuotientGroup.eq_one_iff _).mpr hRjN
      rw [hz]
      exact
        (Subgroup.normalClosure
          ({coordinateClass R i} : Set (PartialPresentationGroup R i))).one_mem

  have hle :
      Subgroup.normalClosure (π '' Set.range R) ≤
        Subgroup.normalClosure
          ({coordinateClass R i} : Set (PartialPresentationGroup R i)) :=
    Subgroup.normalClosure_le_normal himage

  apply top_unique
  rw [← himageTop]
  exact hle

end AC
