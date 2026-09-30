import Collatz.ReturnDefectTransport

namespace CollatzFinal.SourceProduct

/-- Exact finite dyadic order. Zero has no such order. -/
def DyadicOrder (x : Int) (k : Nat) : Prop :=
  ∃ u : Int, x = (2 : Int) ^ k * u ∧ u % 2 = 1

theorem pow_two_succ_even (k : Nat) : (2 : Int) ^ (k + 1) % 2 = 0 := by
  simp [Int.pow_succ, Int.mul_emod]

theorem nat_dyadic_decomposition : ∀ n : Nat, 0 < n →
    ∃ k u : Nat, n = 2 ^ k * u ∧ u % 2 = 1 := by
  intro n
  refine Nat.strongRecOn n ?_
  intro n ih hn
  by_cases ho : n % 2 = 1
  · exact ⟨0, n, by simp, ho⟩
  · have he : n % 2 = 0 := by omega
    have hq : 0 < n / 2 := by omega
    have hlt : n / 2 < n := by omega
    obtain ⟨k, u, hk, hu⟩ := ih (n / 2) hlt hq
    refine ⟨k + 1, u, ?_, hu⟩
    have hnq : n = 2 * (n / 2) := by omega
    rw [hnq, hk]
    simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]

theorem dyadic_order_exists {x : Int} (hx : x ≠ 0) :
    ∃ k, DyadicOrder x k := by
  obtain ⟨k, u, hn, hu⟩ :=
    nat_dyadic_decomposition x.natAbs (Int.natAbs_pos.mpr hx)
  rcases Int.natAbs_eq x with hp | hm
  · refine ⟨k, (u : Int), ?_, ?_⟩
    · rw [hp, hn]
      simp
    · omega
  · refine ⟨k, -(u : Int), ?_, ?_⟩
    · rw [hm, hn]
      simp [Int.mul_neg]
    · omega

theorem dyadic_order_nonzero {x : Int} {k : Nat}
    (hx : DyadicOrder x k) : x ≠ 0 := by
  obtain ⟨u, hxu, hu⟩ := hx
  have hp : (2 : Int) ^ k ≠ 0 := Int.pow_ne_zero (by decide)
  have hune : u ≠ 0 := by omega
  rw [hxu]
  exact Int.mul_ne_zero hp hune

theorem dyadic_mul_odd {x A : Int} {v : Nat}
    (hx : DyadicOrder x v) (hA : A % 2 = 1) :
    DyadicOrder (A * x) v := by
  obtain ⟨u, hxu, hu⟩ := hx
  refine ⟨A * u, ?_, ?_⟩
  · rw [hxu]
    simp [Int.mul_assoc, Int.mul_comm, Int.mul_left_comm]
  · simp [Int.mul_emod, hA, hu]

theorem dyadic_sum_low {x y : Int} {v w : Nat}
    (hx : DyadicOrder x v) (hy : DyadicOrder y w) (hvw : v < w) :
    DyadicOrder (x + y) v := by
  obtain ⟨u, hxu, hu⟩ := hx
  obtain ⟨z, hyz, hz⟩ := hy
  let e := w - v - 1
  have he : w = v + (e + 1) := by dsimp [e]; omega
  have hp : (2 : Int) ^ w = (2 : Int) ^ v * (2 : Int) ^ (e + 1) := by
    rw [he, Int.pow_add]
  refine ⟨u + (2 : Int) ^ (e + 1) * z, ?_, ?_⟩
  · rw [hxu, hyz, hp, Int.mul_assoc, Int.mul_add]
  · simp [Int.add_emod, Int.mul_emod, pow_two_succ_even, hu]

theorem dyadic_sum_unequal {x y : Int} {v w : Nat}
    (hx : DyadicOrder x v) (hy : DyadicOrder y w) (hne : v ≠ w) :
    DyadicOrder (x + y) (min v w) := by
  by_cases hlt : v < w
  · have hm : min v w = v := by omega
    rw [hm]
    exact dyadic_sum_low hx hy hlt
  · have hgt : w < v := by omega
    have hm : min v w = w := by omega
    rw [hm, Int.add_comm]
    exact dyadic_sum_low hy hx hgt

theorem dyadic_equal_sum_even {x y : Int} {v : Nat}
    (hx : DyadicOrder x v) (hy : DyadicOrder y v) :
    ∃ z : Int, x + y = (2 : Int) ^ (v + 1) * z := by
  obtain ⟨u, hxu, hu⟩ := hx
  obtain ⟨w, hyw, hw⟩ := hy
  have he : u + w = 2 * ((u + w) / 2) := by omega
  refine ⟨(u + w) / 2, ?_⟩
  rw [hxu, hyw, ← Int.mul_add]
  calc
    (2 : Int)^v * (u + w) = (2 : Int)^v * (2 * ((u + w) / 2)) :=
      congrArg (fun z : Int => (2 : Int)^v * z) he
    _ = (2 : Int)^(v + 1) * ((u + w) / 2) := by
      rw [Int.pow_succ, Int.mul_assoc]

theorem dyadic_divide {x y : Int} {v D : Nat}
    (hx : DyadicOrder x v) (hstep : (2 : Int) ^ D * y = x) :
    D ≤ v ∧ DyadicOrder y (v - D) := by
  obtain ⟨u, hxu, hu⟩ := hx
  have hle : D ≤ v := by
    by_cases hn : D ≤ v
    · exact hn
    · have hlt : v < D := by omega
      let e := D - v - 1
      have he : D = v + (e + 1) := by dsimp [e]; omega
      have hh : (2 : Int) ^ v * ((2 : Int) ^ (e + 1) * y) =
          (2 : Int) ^ v * u := by
        rw [← Int.mul_assoc, ← Int.pow_add, ← he, hstep, hxu]
      have hc : (2 : Int) ^ (e + 1) * y = u :=
        Int.eq_of_mul_eq_mul_left (Int.pow_ne_zero (by decide)) hh
      have hp : ((2 : Int) ^ (e + 1) * y) % 2 = 0 := by
        simp [Int.mul_emod, pow_two_succ_even]
      rw [hc] at hp
      omega
  have hv : v = D + (v - D) := by omega
  have hh : (2 : Int) ^ D * y =
      (2 : Int) ^ D * ((2 : Int) ^ (v - D) * u) := by
    rw [← Int.mul_assoc, ← Int.pow_add, ← hv, hstep, hxu]
  have hy : y = (2 : Int) ^ (v - D) * u :=
    Int.eq_of_mul_eq_mul_left (Int.pow_ne_zero (by decide)) hh
  exact ⟨hle, u, hy, hu⟩

theorem dyadic_order_unique {x : Int} {v w : Nat}
    (hv : DyadicOrder x v) (hw : DyadicOrder x w) : v = w := by
  obtain ⟨u, hxu, hu⟩ := hv
  obtain ⟨z, hxz, hz⟩ := hw
  have h1 : w ≤ v := (dyadic_divide ⟨u, hxu, hu⟩ hxz.symm).1
  have h2 : v ≤ w := (dyadic_divide ⟨z, hxz, hz⟩ hxu.symm).1
  omega

/-- Unequal incoming/injection orders force the exact minimum-minus-depth law. -/
theorem dyadic_switch_unequal {x J y A : Int} {v w D : Nat}
    (hx : DyadicOrder x v) (hJ : DyadicOrder J w)
    (hA : A % 2 = 1) (hne : v ≠ w)
    (hstep : (2 : Int) ^ D * y = A * x + J) :
    D ≤ min v w ∧ DyadicOrder y (min v w - D) := by
  exact dyadic_divide (dyadic_sum_unequal (dyadic_mul_odd hx hA) hJ hne) hstep

/-- Equal orders yield extra divisibility, with zero deliberately permitted. -/
theorem dyadic_switch_equal {x J y A : Int} {v D : Nat}
    (hx : DyadicOrder x v) (hJ : DyadicOrder J v)
    (hA : A % 2 = 1)
    (hstep : (2 : Int) ^ D * y = A * x + J) :
    ∃ z : Int, (2 : Int) ^ D * y = (2 : Int) ^ (v + 1) * z := by
  obtain ⟨z, hz⟩ := dyadic_equal_sum_even (dyadic_mul_odd hx hA) hJ
  exact ⟨z, hstep.trans hz⟩

theorem dyadic_switch_zero_injection {x y A : Int} {v D : Nat}
    (hx : DyadicOrder x v) (hA : A % 2 = 1)
    (hstep : (2 : Int) ^ D * y = A * x) :
    D ≤ v ∧ DyadicOrder y (v - D) := by
  exact dyadic_divide (dyadic_mul_odd hx hA) hstep

/-- Complete signed input split: zero is a distinct branch. -/
theorem dyadic_input_cases (x : Int) : x = 0 ∨ ∃ v, DyadicOrder x v := by
  by_cases hx : x = 0
  · exact Or.inl hx
  · exact Or.inr (dyadic_order_exists hx)

/-- No infinite nonzero integer defect chain can consume positive depth forever. -/
theorem fixed_centre_exhaustion
    (delta A : Nat → Int) (D : Nat → Nat)
    (hA : ∀ i, A i % 2 = 1) (hD : ∀ i, 0 < D i)
    (htransport : ∀ i, (2 : Int) ^ D i * delta (i + 1) = A i * delta i)
    (hnz : ∀ i, delta i ≠ 0) : False := by
  classical
  have hex : ∀ i, ∃ v, DyadicOrder (delta i) v :=
    fun i => dyadic_order_exists (hnz i)
  let fuel : Nat → Nat := fun i => Classical.choose (hex i)
  have hf : ∀ i, DyadicOrder (delta i) (fuel i) :=
    fun i => Classical.choose_spec (hex i)
  have hdrop : ∀ i, fuel (i + 1) < fuel i := by
    intro i
    have ht := dyadic_switch_zero_injection (hf i) (hA i) (htransport i)
    have he := dyadic_order_unique (hf (i + 1)) ht.2
    have hd := hD i
    omega
  have hb : ∀ k, fuel k + k ≤ fuel 0 := by
    intro k
    induction k with
    | zero => omega
    | succ k ih =>
        have hd := hdrop k
        omega
  have hbad := hb (fuel 0 + 1)
  omega

/-- The exact-zero return branch is a fixed point, not finite valuation fuel. -/
theorem return_zero_defect_fixed_point
    (A B P m m' : Int) (hP : P ≠ 0)
    (hstep : P * m' = A * m + B)
    (hz : returnDefect A B P m = 0) : m' = m := by
  have hd : P * m - P * m' = returnDefect A B P m := by
    rw [hstep]
    simp only [returnDefect, Int.sub_mul]
    omega
  have he : P * m' = P * m := by omega
  exact Int.eq_of_mul_eq_mul_left hP he

/-- Equal-order cancellation can have arbitrarily large finite output order.
This is an algebraic obstruction, not an admitted Collatz itinerary. -/
theorem equal_order_cancellation_unbounded (k : Nat) :
    DyadicOrder 1 0 ∧ DyadicOrder ((2 : Int) ^ (k + 1) - 1) 0 ∧
      DyadicOrder (1 + ((2 : Int) ^ (k + 1) - 1)) (k + 1) := by
  constructor
  · exact ⟨1, by simp, by decide⟩
  constructor
  · refine ⟨(2 : Int) ^ (k + 1) - 1, by simp, ?_⟩
    have he := pow_two_succ_even k
    omega
  · refine ⟨1, ?_, by decide⟩
    simp only [Int.mul_one]
    omega

/-- The switch classification consumes the exact qualified affine transport. -/
theorem return_switch_unequal
    (A₁ B₁ P₁ A₂ B₂ m m' : Int) (D v w : Nat)
    (hstep : (2 : Int) ^ D * m' = A₂ * m + B₂)
    (hA : A₂ % 2 = 1)
    (hdelta : DyadicOrder (returnDefect A₁ B₁ P₁ m) v)
    (hJ : DyadicOrder
      (returnInjection A₁ B₁ P₁ A₂ B₂ ((2 : Int) ^ D)) w)
    (hne : v ≠ w) :
    D ≤ min v w ∧
      DyadicOrder (returnDefect A₁ B₁ P₁ m') (min v w - D) := by
  exact dyadic_switch_unequal hdelta hJ hA hne
    (returnDefect_transport A₁ B₁ P₁ A₂ B₂ ((2 : Int) ^ D) m m' hstep)

/-- Arbitrarily changing laws with zero injection share one exhausted reserve. -/
theorem shared_centre_return_exhaustion
    (A₀ B₀ P₀ : Int) (m A B : Nat → Int) (D : Nat → Nat)
    (hA : ∀ i, A i % 2 = 1) (hD : ∀ i, 0 < D i)
    (hstep : ∀ i, (2 : Int) ^ D i * m (i + 1) = A i * m i + B i)
    (hJ : ∀ i, returnInjection A₀ B₀ P₀ (A i) (B i) ((2 : Int) ^ D i) = 0)
    (hnz : ∀ i, returnDefect A₀ B₀ P₀ (m i) ≠ 0) : False := by
  apply fixed_centre_exhaustion
    (fun i => returnDefect A₀ B₀ P₀ (m i)) A D hA hD
  · intro i
    have ht := returnDefect_transport A₀ B₀ P₀
      (A i) (B i) ((2 : Int) ^ D i) (m i) (m (i + 1)) (hstep i)
    simpa [hJ i] using ht
  · exact hnz

#print axioms dyadic_order_exists
#print axioms dyadic_order_unique
#print axioms dyadic_sum_unequal
#print axioms dyadic_equal_sum_even
#print axioms dyadic_switch_unequal
#print axioms dyadic_switch_equal
#print axioms dyadic_switch_zero_injection
#print axioms fixed_centre_exhaustion
#print axioms return_zero_defect_fixed_point
#print axioms equal_order_cancellation_unbounded
#print axioms return_switch_unequal
#print axioms shared_centre_return_exhaustion

end CollatzFinal.SourceProduct
