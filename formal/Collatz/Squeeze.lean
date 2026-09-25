import Collatz.FinalKernel

namespace CollatzFinal

def liveGapCeiling : Nat := 4142380787

def squeezeModulus : Nat := 2 * 3^20

theorem liveGap_lt_squeezeModulus :
    liveGapCeiling < squeezeModulus := by
  decide

theorem zero_of_squeeze_divisibility
    {d : Nat}
    (hgap : d ≤ liveGapCeiling)
    (hdiv : squeezeModulus ∣ d) :
    d = 0 := by
  rcases hdiv with ⟨k, rfl⟩
  cases k with
  | zero =>
      simp
  | succ k =>
      have hlt : liveGapCeiling < squeezeModulus :=
        liveGap_lt_squeezeModulus
      have hpos : 0 < squeezeModulus := by
        decide
      omega

/--
Certificate-facing form of the exact-return squeeze.  The generator need only
establish the real gap bound and the combined 2/3-adic divisibility.
-/
theorem exact_recurrence_of_gap_and_biadic_spacing
    {d : Nat}
    (hgap : d ≤ 4142380787)
    (hspace : (2 * 3^20) ∣ d) :
    d = 0 := by
  exact zero_of_squeeze_divisibility hgap hspace

end CollatzFinal
