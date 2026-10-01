import Collatz.GuardedExitObligation

namespace CollatzFinal.SourceProduct

/-- One protected exit relation is enough: the current endpoint lies on the
forward orbit of some strictly earlier positive source. -/
def EarlierSourceCollision (source current : Nat) : Prop :=
  ∃ p b, 0 < p ∧ p < source ∧ iter shortcut b p = current

/-- For every source above 1, the three OrdinaryExit constructors are exactly
one relation. Terminal 1/2 and direct descent are already special cases of
earlier-source collision. -/
theorem ordinaryExit_iff_earlierSourceCollision
    {source current : Nat} (hsource : 1 < source) :
    OrdinaryExit source current ↔ EarlierSourceCollision source current := by
  constructor
  · intro h
    rcases h with ht | hd | hm
    · rcases ht with rfl | rfl
      · exact ⟨1, 0, by decide, hsource, rfl⟩
      · refine ⟨1, 1, by decide, hsource, ?_⟩
        simpa [iter] using shortcut_one
    · exact ⟨current, 0, hd.1, hd.2, rfl⟩
    · exact hm
  · intro h
    exact Or.inr (Or.inr h)

/-- The contracted exit relation is forward invariant for the same simple
reason as a lower-source merge: keep the earlier source and advance one step. -/
theorem earlierSourceCollision_forward (source : Nat) :
    ForwardInvariant shortcut (EarlierSourceCollision source) := by
  intro current h
  rcases h with ⟨p, b, hp, hlt, heq⟩
  refine ⟨p, b + 1, hp, hlt, ?_⟩
  rw [iter_succ_last, heq]

/-- The protected eventual-exit objective itself therefore factors through the
single earlier-source collision predicate. -/
theorem exitObligation_iff_eventual_earlierSourceCollision
    {source current : Nat} (hsource : 1 < source) :
    ExitObligation source current ↔
      Eventually shortcut (EarlierSourceCollision source) current := by
  constructor
  · rintro ⟨k, hk⟩
    exact ⟨k, (ordinaryExit_iff_earlierSourceCollision hsource).mp hk⟩
  · rintro ⟨k, hk⟩
    exact ⟨k, (ordinaryExit_iff_earlierSourceCollision hsource).mpr hk⟩

/-- This is the contracted QED seam. The only Collatz-specific universal
premise is that every source n>1 eventually collides with the orbit of some
strictly earlier positive source. -/
theorem collatz_of_universal_earlierSourceCollision
    (hcomplete :
      ∀ n, 1 < n →
        Eventually shortcut (EarlierSourceCollision n) n) :
    ∀ n, 0 < n → ∃ k, iter shortcut k n = 1 := by
  apply collatz_of_universal_exit_obligation
  intro n hn
  exact (exitObligation_iff_eventual_earlierSourceCollision hn).mpr
    (hcomplete n hn)

/-- Exact no-exit residual in the contracted language. -/
theorem no_ordinaryExit_iff_no_earlierSourceCollision
    {source current : Nat} (hsource : 1 < source) :
    (¬ OrdinaryExit source current) ↔
      (¬ EarlierSourceCollision source current) := by
  exact not_congr (ordinaryExit_iff_earlierSourceCollision hsource)

#print axioms ordinaryExit_iff_earlierSourceCollision
#print axioms earlierSourceCollision_forward
#print axioms exitObligation_iff_eventual_earlierSourceCollision
#print axioms collatz_of_universal_earlierSourceCollision
#print axioms no_ordinaryExit_iff_no_earlierSourceCollision

end CollatzFinal.SourceProduct
