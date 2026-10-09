import Collatz.DistinctCentreSwitch

namespace CollatzFinal
namespace SourceProduct

/-- A nonzero centre-separation injection that survives at least the new
return cylinder's forced D₂+1 dyadic digits. -/
def DeepSwitchOrder
    (A₁ B₁ A₂ B₂ : Int) (D₁ D₂ : Nat) : Prop :=
  ∃ h,
    D₂ + 1 ≤ h ∧
      DyadicOrder
        (returnInjection
          A₁ B₁ ((2 : Int) ^ D₁)
          A₂ B₂ ((2 : Int) ^ D₂)) h

/-- Split the unique finite dyadic order of a nonzero injection at the
new return cylinder's forced precision. No outcome is discarded. -/
theorem switch_injection_low_or_deep
    {A₁ B₁ A₂ B₂ : Int} {D₁ D₂ : Nat}
    (hJne :
      returnInjection A₁ B₁ ((2 : Int) ^ D₁)
        A₂ B₂ ((2 : Int) ^ D₂) ≠ 0) :
    (∃ h,
      DyadicOrder
        (returnInjection A₁ B₁ ((2 : Int) ^ D₁)
          A₂ B₂ ((2 : Int) ^ D₂)) h ∧
      h < D₂ + 1) ∨
    DeepSwitchOrder A₁ B₁ A₂ B₂ D₁ D₂ := by
  obtain ⟨h, hh⟩ := dyadic_order_exists hJne
  by_cases hlt : h < D₂ + 1
  · exact Or.inl ⟨h, hh, hlt⟩
  · exact Or.inr ⟨h, by omega, hh⟩

/-- An exact dyadic-order witness v carries divisibility by every
smaller or equal power 2^k. -/
theorem dyadic_order_implies_divisible
    {x : Int} {v k : Nat}
    (hx : DyadicOrder x v) (hk : k ≤ v) :
    (2 : Int) ^ k ∣ x := by
  obtain ⟨u, hu, huodd⟩ := hx
  refine ⟨(2 : Int) ^ (v - k) * u, ?_⟩
  have hsum : v = k + (v - k) := by omega
  calc
    x = (2 : Int) ^ v * u := hu
    _ = (2 : Int) ^ (k + (v - k)) * u := by rw [← hsum]
    _ = (2 : Int) ^ k * ((2 : Int) ^ (v - k) * u) := by
      rw [Int.pow_add, Int.mul_assoc]

/-- Corrected V89 theorem. Deep injection plus an admitted new return
forces *divisibility* of the old-centre defect at the same precision.
If that defect is nonzero it has finite dyadic order ≥ D₂+1; if it
vanishes, no finite dyadic order may be assigned. -/
theorem deep_switch_zero_or_high_order
    {A₁ B₁ A₂ B₂ m : Int} {D₁ D₂ : Nat}
    (hD₁ : 0 < D₁) (hD₂ : 0 < D₂)
    (hA₁ : A₁ % 2 = 1) (hA₂ : A₂ % 2 = 1)
    (hadm : ReturnCylinderAdmissible A₂ B₂ D₂ m)
    (hdeep : DeepSwitchOrder A₁ B₁ A₂ B₂ D₁ D₂) :
    returnDefect A₁ B₁ ((2 : Int) ^ D₁) m = 0 ∨
      ∃ v,
        D₂ + 1 ≤ v ∧
          DyadicOrder
            (returnDefect A₁ B₁ ((2 : Int) ^ D₁) m) v := by
  let oldDefect := returnDefect A₁ B₁ ((2 : Int) ^ D₁) m
  by_cases hz : oldDefect = 0
  · exact Or.inl hz
  · right
    obtain ⟨v, hv⟩ := dyadic_order_exists hz
    obtain ⟨w, hwD, hw⟩ := hadm
    obtain ⟨h, hhD, hh⟩ := hdeep
    have hC₂ :
        (((2 : Int) ^ D₂) - A₂) % 2 = 1 :=
      return_denominator_coefficient_odd hD₂ hA₂
    have hprod :
        DyadicOrder
          ((((2 : Int) ^ D₂) - A₂) * oldDefect) v :=
      dyadic_mul_odd hv hC₂
    have hdivNew :
        (2 : Int) ^ (D₂ + 1) ∣
          returnDefect A₂ B₂ ((2 : Int) ^ D₂) m :=
      dyadic_order_implies_divisible hw hwD
    have hdivJ :
        (2 : Int) ^ (D₂ + 1) ∣
          returnInjection A₁ B₁ ((2 : Int) ^ D₁)
            A₂ B₂ ((2 : Int) ^ D₂) :=
      dyadic_order_implies_divisible hh hhD
    obtain ⟨u, hu⟩ := hdivNew
    obtain ⟨z, hzJ⟩ := hdivJ
    have hpair := returnDefect_pair_injection
      A₁ B₁ ((2 : Int) ^ D₁)
      A₂ B₂ ((2 : Int) ^ D₂) m
    have hstep :
        (2 : Int) ^ (D₂ + 1) *
          ((((2 : Int) ^ D₁) - A₁) * u + z) =
        (((2 : Int) ^ D₂) - A₂) * oldDefect := by
      dsimp [oldDefect]
      calc
        (2 : Int) ^ (D₂ + 1) *
            ((((2 : Int) ^ D₁) - A₁) * u + z) =
          ((((2 : Int) ^ D₁) - A₁) *
              ((2 : Int) ^ (D₂ + 1) * u) +
            (2 : Int) ^ (D₂ + 1) * z) := by
              simp [Int.mul_add, Int.mul_assoc,
                Int.mul_comm, Int.mul_left_comm]
        _ = ((((2 : Int) ^ D₁) - A₁) *
              returnDefect A₂ B₂ ((2 : Int) ^ D₂) m +
            returnInjection A₁ B₁ ((2 : Int) ^ D₁)
              A₂ B₂ ((2 : Int) ^ D₂)) := by
                rw [← hu, ← hzJ]
        _ = (((2 : Int) ^ D₂) - A₂) *
              returnDefect A₁ B₁ ((2 : Int) ^ D₁) m := hpair.symm
    have hbound :=
      (dyadic_divide hprod hstep).1
    exact ⟨v, hbound, hv⟩

/-- The full algebraic boundary: low separation produces the V88 gain,
while deep cancellation exposes zero or a high-order old defect.
This does not assert that successive actual returns must occur. -/
theorem admitted_switch_gain_or_zero_or_high
    {A₁ B₁ A₂ B₂ m : Int} {H D₁ D₂ : Nat}
    (hD₁ : 0 < D₁) (hD₂ : 0 < D₂)
    (hA₁ : A₁ % 2 = 1) (hA₂ : A₂ % 2 = 1)
    (hadm : ReturnCylinderAdmissible A₂ B₂ D₂ m)
    (hJne :
      returnInjection A₁ B₁ ((2 : Int) ^ D₁)
        A₂ B₂ ((2 : Int) ^ D₂) ≠ 0) :
    (∃ h w,
      DyadicOrder
        (returnInjection A₁ B₁ ((2 : Int) ^ D₁)
          A₂ B₂ ((2 : Int) ^ D₂)) h ∧
      DyadicOrder
        (returnDefect A₂ B₂ ((2 : Int) ^ D₂) m) w ∧
      pulledPrecision H h < pulledPrecision H w) ∨
    (returnDefect A₁ B₁ ((2 : Int) ^ D₁) m = 0 ∨
      ∃ v, D₂ + 1 ≤ v ∧
        DyadicOrder
          (returnDefect A₁ B₁ ((2 : Int) ^ D₁) m) v) := by
  rcases switch_injection_low_or_deep hJne with hlow | hdeep
  · obtain ⟨h, hh, hlt⟩ := hlow
    obtain ⟨w, hw, hgain⟩ :=
      separated_admissible_switch_precision_gain
        (H := H) hD₁ hD₂ hA₁ hA₂ hadm hh hlt
    exact Or.inl ⟨h, w, hh, hw, hgain⟩
  · exact Or.inr
      (deep_switch_zero_or_high_order hD₁ hD₂ hA₁ hA₂ hadm hdeep)

#print axioms dyadic_order_implies_divisible
#print axioms deep_switch_zero_or_high_order
#print axioms admitted_switch_gain_or_zero_or_high

end SourceProduct
end CollatzFinal
