import Collatz.DistinctCentreSwitch

namespace CollatzFinal
namespace SourceProduct

/-- The only residual after the separated-switch gain theorem:
the centre-separation injection itself survives through all D+1 forced
bits of the newly admitted return cylinder. -/
def DeepSwitchCancellation
    (A₁ B₁ : Int) (D₁ : Nat)
    (A₂ B₂ : Int) (D₂ : Nat) : Prop :=
  ∃ h,
    D₂ + 1 ≤ h ∧
    DyadicOrder
      (returnInjection
        A₁ B₁ ((2 : Int) ^ D₁)
        A₂ B₂ ((2 : Int) ^ D₂)) h

/-- Every nonzero injection has an exact dyadic order.  Relative to the
new cylinder's forced precision D₂+1, that order is either below the
boundary (the V88 strict-gain case) or at/above it (deep cancellation). -/
theorem admitted_switch_separated_or_deep
    {A₁ B₁ A₂ B₂ : Int} {D₁ D₂ : Nat}
    (hJne :
      returnInjection
        A₁ B₁ ((2 : Int) ^ D₁)
        A₂ B₂ ((2 : Int) ^ D₂) ≠ 0) :
    (∃ h,
      DyadicOrder
        (returnInjection
          A₁ B₁ ((2 : Int) ^ D₁)
          A₂ B₂ ((2 : Int) ^ D₂)) h ∧
      h < D₂ + 1) ∨
    DeepSwitchCancellation A₁ B₁ D₁ A₂ B₂ D₂ := by
  obtain ⟨h, hh⟩ := dyadic_order_exists hJne
  by_cases hlt : h < D₂ + 1
  · exact Or.inl ⟨h, hh, hlt⟩
  · exact Or.inr ⟨h, by omega, hh⟩

/-- A deep-cancellation switch makes the old-centre defect share at least
the new cylinder's full forced D₂+1 divisibility.

This is the exact strengthened congruence earned when V88's strict-gain
separator is absent. -/
theorem deep_switch_old_defect_forced
    {A₁ B₁ A₂ B₂ m : Int}
    {D₁ D₂ : Nat}
    (hD₁ : 0 < D₁)
    (hD₂ : 0 < D₂)
    (hA₁ : A₁ % 2 = 1)
    (hA₂ : A₂ % 2 = 1)
    (hadm : ReturnCylinderAdmissible A₂ B₂ D₂ m)
    (hdeep : DeepSwitchCancellation A₁ B₁ D₁ A₂ B₂ D₂) :
    ∃ v,
      D₂ + 1 ≤ v ∧
      DyadicOrder
        (returnDefect A₁ B₁ ((2 : Int) ^ D₁) m) v := by
  obtain ⟨w, hwD, hw⟩ := hadm
  obtain ⟨h, hhD, hh⟩ := hdeep
  have hC₁ :
      (((2 : Int) ^ D₁) - A₁) % 2 = 1 :=
    return_denominator_coefficient_odd hD₁ hA₁
  have hC₂ :
      (((2 : Int) ^ D₂) - A₂) % 2 = 1 :=
    return_denominator_coefficient_odd hD₂ hA₂
  have hnewMul :
      DyadicOrder
        ((((2 : Int) ^ D₁) - A₁) *
          returnDefect A₂ B₂ ((2 : Int) ^ D₂) m) w :=
    dyadic_mul_odd hw hC₁
  by_cases heq : w = h
  · have hsumEven :=
      dyadic_equal_sum_even hnewMul (by simpa [heq] using hh)
    obtain ⟨z, hz⟩ := hsumEven
    have hpair := returnDefect_pair_injection
      A₁ B₁ ((2 : Int) ^ D₁)
      A₂ B₂ ((2 : Int) ^ D₂) m
    have hprod :
        ((((2 : Int) ^ D₂) - A₂) *
          returnDefect A₁ B₁ ((2 : Int) ^ D₁) m) =
          (2 : Int) ^ (w + 1) * z := by
      rw [hpair]
      simpa [Int.add_comm, heq] using hz
    have hprodOrderOrZero :
        ((((2 : Int) ^ D₂) - A₂) *
          returnDefect A₁ B₁ ((2 : Int) ^ D₁) m) = 0) ∨
        ∃ v, w + 1 ≤ v ∧
          DyadicOrder
            ((((2 : Int) ^ D₂) - A₂) *
              returnDefect A₁ B₁ ((2 : Int) ^ D₁) m) v := by
      by_cases hz0 : z = 0
      · left
        rw [hprod, hz0]
        simp
      · right
        obtain ⟨t, ht⟩ := dyadic_order_exists z
        refine ⟨w + 1 + t, by omega, ?_⟩
        obtain ⟨u, hzu, hu⟩ := ht
        refine ⟨u, ?_, hu⟩
        rw [hprod, hzu]
        simp [Int.pow_add, Int.mul_assoc]
    rcases hprodOrderOrZero with hp0 | ⟨v, hv, hpv⟩
    · have hCne : (((2 : Int) ^ D₂) - A₂) ≠ 0 := by
        intro hc
        have hmod : ((((2 : Int) ^ D₂) - A₂) % 2) = 0 := by simp [hc]
        omega
      have hd0 : returnDefect A₁ B₁ ((2 : Int) ^ D₁) m = 0 :=
        (Int.mul_eq_zero.mp hp0).resolve_left hCne
      exfalso
      have hne := dyadic_order_nonzero hw
      have hpair := returnDefect_pair_injection
        A₁ B₁ ((2 : Int) ^ D₁)
        A₂ B₂ ((2 : Int) ^ D₂) m
      rw [hd0] at hpair
      have hjrel :
          returnInjection
            A₁ B₁ ((2 : Int) ^ D₁)
            A₂ B₂ ((2 : Int) ^ D₂) =
          -((((2 : Int) ^ D₁) - A₁) *
            returnDefect A₂ B₂ ((2 : Int) ^ D₂) m) := by
        omega
      have hjOrder : DyadicOrder
          (returnInjection
            A₁ B₁ ((2 : Int) ^ D₁)
            A₂ B₂ ((2 : Int) ^ D₂)) w := by
        rw [hjrel]
        obtain ⟨u, hu, huodd⟩ := hnewMul
        refine ⟨-u, ?_, ?_⟩
        · rw [hu]
          simp [Int.mul_neg]
        · omega
      have := dyadic_order_unique hjOrder hh
      exact hne (by
        have hzero : returnDefect A₂ B₂ ((2 : Int) ^ D₂) m = 0 := by
          have hmul0 :
              (((2 : Int) ^ D₁) - A₁) *
                returnDefect A₂ B₂ ((2 : Int) ^ D₂) m = 0 := by
            rw [← hjrel]
            have hjne := dyadic_order_nonzero hh
            omega
          have hC1ne : (((2 : Int) ^ D₁) - A₁) ≠ 0 := by
            intro hc
            have hmod : ((((2 : Int) ^ D₁) - A₁) % 2) = 0 := by simp [hc]
            omega
          exact (Int.mul_eq_zero.mp hmul0).resolve_left hC1ne
        exact hzero)
    · have hold := dyadic_order_cancel_odd hpv hC₂
      exact ⟨v, le_trans hwD (by omega), hold⟩
  · have hsum :
      DyadicOrder
        ((((2 : Int) ^ D₁) - A₁) *
            returnDefect A₂ B₂ ((2 : Int) ^ D₂) m +
          returnInjection
            A₁ B₁ ((2 : Int) ^ D₁)
            A₂ B₂ ((2 : Int) ^ D₂)) (min w h) :=
      dyadic_sum_unequal hnewMul hh heq
    have hprod :
      DyadicOrder
        ((((2 : Int) ^ D₂) - A₂) *
          returnDefect A₁ B₁ ((2 : Int) ^ D₁) m) (min w h) := by
      rw [returnDefect_pair_injection]
      exact hsum
    have hold := dyadic_order_cancel_odd hprod hC₂
    exact ⟨min w h, by omega, hold⟩

/-- The switch boundary is therefore exact:
* nonzero injection + low separation => V88 strict precision gain;
* otherwise deep cancellation => a strictly stronger shared source congruence.

This theorem deliberately does not claim the deep branch terminates; it names
the only remaining switch residual. -/
theorem admitted_distinct_switch_gain_or_deep
    {A₁ B₁ A₂ B₂ m : Int}
    {H D₁ D₂ : Nat}
    (hD₁ : 0 < D₁)
    (hD₂ : 0 < D₂)
    (hA₁ : A₁ % 2 = 1)
    (hA₂ : A₂ % 2 = 1)
    (hadm : ReturnCylinderAdmissible A₂ B₂ D₂ m)
    (hJne :
      returnInjection
        A₁ B₁ ((2 : Int) ^ D₁)
        A₂ B₂ ((2 : Int) ^ D₂) ≠ 0) :
    (∃ h w,
      DyadicOrder
        (returnInjection
          A₁ B₁ ((2 : Int) ^ D₁)
          A₂ B₂ ((2 : Int) ^ D₂)) h ∧
      DyadicOrder
        (returnDefect A₂ B₂ ((2 : Int) ^ D₂) m) w ∧
      pulledPrecision H h < pulledPrecision H w) ∨
    DeepSwitchCancellation A₁ B₁ D₁ A₂ B₂ D₂ := by
  rcases admitted_switch_separated_or_deep hJne with hsep | hdeep
  · obtain ⟨h, hh, hlt⟩ := hsep
    obtain ⟨w, hw, hgain⟩ :=
      separated_admissible_switch_precision_gain
        (H := H) hD₁ hD₂ hA₁ hA₂ hadm hh hlt
    exact Or.inl ⟨h, w, hh, hw, hgain⟩
  · exact Or.inr hdeep

#print axioms admitted_switch_separated_or_deep
#print axioms deep_switch_old_defect_forced
#print axioms admitted_distinct_switch_gain_or_deep

end SourceProduct
end CollatzFinal
