import Collatz.OneArrowBasinRepair

namespace CollatzFinal
namespace SourceProduct

/-!
V174 — EVERY FINITE HEIGHT/CLOCK AUDIT HAS A TWO-BASIN ADVERSARY.

For ANY original-source cutoff X and ANY finite real clock H, a
specific odd a ≡ 2 (mod 3) is chosen beyond ALL actual shortcut
endpoints of sources n<X at clocks t<=H. Freezing just the arrow
a -> T(a) into a -> a yields a non-Collatz deterministic Nat map
with an independent positive fixed-point basin, yet preserves EVERY
audited original source/clock state exactly.

This does not refute any TRUE all-source affine theorem; the adversary
violates that law at the single protected defect. It proves a precise
LIMITATION of finite exhaustive search, not Collatz QED.
-/

/-- The true shortcut can at most double a nonnegative state in
one real shortcut clock. The estimate is deliberately coarse but
uniform and exact. -/
theorem v174_shortcut_le_twice (n : Nat) :
    shortcut n ≤ 2*n := by
  unfold shortcut
  by_cases he : n%2=0
  · simp only [he, ite_true]
    omega
  · simp only [he, ite_false]
    omega

theorem v174_actual_endpoint_bound (t n : Nat) :
    iter shortcut t n ≤ 2^t*n := by
  induction t with
  | zero => simp [iter]
  | succ t ih =>
      calc
        iter shortcut (t+1) n =
            shortcut (iter shortcut t n) := by rw [iter_succ_last]
        _ ≤ 2*(iter shortcut t n) :=
          v174_shortcut_le_twice _
        _ ≤ 2*(2^t*n) :=
          Nat.mul_le_mul_left _ ih
        _ = 2^(t+1)*n := by
          simp [Nat.pow_succ, Nat.mul_assoc,
            Nat.mul_comm, Nat.mul_left_comm]

theorem v174_two_pow_mono
    (j H : Nat) (h : j ≤ H) : 2^j ≤ 2^H := by
  induction H with
  | zero =>
      have hj : j=0 := by omega
      subst j
      exact Nat.le_refl _
  | succ H ih =>
      by_cases hle : j ≤ H
      · calc
          2^j ≤ 2^H := ih hle
          _ ≤ 2^(H+1) := by
            rw [Nat.pow_succ]
            omega
      · have hEq : j=H+1 := by omega
        subst j
        exact Nat.le_refl _

/-- The chosen artificial defect is beyond the coarse upper bound
for every original source n<X, any clock ≤H. -/
def v174HiddenDefect (X H : Nat) : Nat :=
  6*(2^H*(X+1))+5

theorem v174_defect_large_and_odd (X H : Nat) :
    5 ≤ v174HiddenDefect X H ∧
    v174HiddenDefect X H % 2 = 1 ∧
    v174HiddenDefect X H % 3 = 2 := by
  unfold v174HiddenDefect
  omega

theorem v174_audited_endpoints_below_defect
    (X H n t : Nat)
    (hn : n < X) (ht : t ≤ H) :
    iter shortcut t n < v174HiddenDefect X H := by
  have hStep := v174_actual_endpoint_bound t n
  have hPow := v174_two_pow_mono t H ht
  have hMul : 2^t*n ≤ 2^H*n :=
    Nat.mul_le_mul_right n hPow
  have hHeight : 2^H*n ≤ 2^H*(X+1) :=
    Nat.mul_le_mul_left (2^H) (by omega)
  let B : Nat := 2^H*(X+1)
  have hB : B < 6*B+5 := by omega
  exact lt_of_le_of_lt (hStep.trans (hMul.trans hHeight)) hB

/-- An artificial freeze cannot change a finite trajectory before
the first visit to the modified source. -/
theorem v174_freeze_matches_avoided_prefix
    (a n t : Nat)
    (hAvoid : ∀ j : Nat, j<t → iter shortcut j n ≠ a) :
    iter (v173FreezeAt a) t n = iter shortcut t n := by
  induction t with
  | zero => rfl
  | succ t ih =>
      have hPrior : ∀ j : Nat, j<t → iter shortcut j n ≠ a := by
        intro j hj
        exact hAvoid j (by omega)
      have hEq := ih hPrior
      have hNe : iter shortcut t n ≠ a :=
        hAvoid t (by omega)
      rw [iter_succ_last, iter_succ_last, hEq]
      exact v173_freeze_agrees_before_seed a
        (iter shortcut t n) hNe

/-- Every source/clock outcome in ANY finite audit is EXACTLY
indistinguishable from the real shortcut under this false map. -/
theorem v174_every_bounded_audit_agrees
    (X H n t : Nat)
    (hn : n<X) (ht : t≤H) :
    iter (v173FreezeAt (v174HiddenDefect X H)) t n =
      iter shortcut t n := by
  apply v174_freeze_matches_avoided_prefix
  intro j hj
  have hBound :=
    v174_audited_endpoints_below_defect X H n j hn (by omega)
  omega

/-- The false map contains an actual new fixed-point cycle at
the hidden source. This is not a Collatz counterexample. -/
theorem v174_false_map_has_fixed_defect (X H t : Nat) :
    iter (v173FreezeAt (v174HiddenDefect X H)) t
      (v174HiddenDefect X H) = v174HiddenDefect X H := by
  have hStep :
      v173FreezeAt (v174HiddenDefect X H)
        (v174HiddenDefect X H) = v174HiddenDefect X H := by
    simp [v173FreezeAt]
  induction t with
  | zero => rfl
  | succ t ih =>
      rw [iter_succ_last, ih, hStep]

/-- The genuine 1↔2 class survives the artificial high defect,
because the defect is at least 5. -/
theorem v174_false_map_keeps_one_two (X H t : Nat) :
    iter (v173FreezeAt (v174HiddenDefect X H)) t 1 = 1 ∨
    iter (v173FreezeAt (v174HiddenDefect X H)) t 1 = 2 := by
  have ha : 5 ≤ v174HiddenDefect X H :=
    (v174_defect_large_and_odd X H).1
  have hOne :
      v173FreezeAt (v174HiddenDefect X H) 1=2 := by
    simp [v173FreezeAt, shortcut]
    omega
  have hTwo :
      v173FreezeAt (v174HiddenDefect X H) 2=1 := by
    simp [v173FreezeAt, shortcut]
    omega
  induction t with
  | zero => exact Or.inl rfl
  | succ t ih =>
      rw [iter_succ_last]
      rcases ih with h1 | h2
      · rw [h1, hOne]
        exact Or.inr rfl
      · rw [h2, hTwo]
        exact Or.inl rfl

/-- Two completely disjoint future classes coexist in the false
map, even though ALL chosen bounded input/output audits agree
exactly with the genuine Collatz shortcut. -/
theorem v174_false_map_has_two_disjoint_positive_classes
    (X H : Nat) :
    ¬ ∃ i j : Nat,
      iter (v173FreezeAt (v174HiddenDefect X H)) i
        (v174HiddenDefect X H) =
      iter (v173FreezeAt (v174HiddenDefect X H)) j 1 := by
  intro h
  obtain ⟨i,j,hEq⟩ := h
  rw [v174_false_map_has_fixed_defect] at hEq
  rcases v174_false_map_keeps_one_two X H j with hOne | hTwo
  · rw [hOne] at hEq
    have hLarge := (v174_defect_large_and_odd X H).1
    omega
  · rw [hTwo] at hEq
    have hLarge := (v174_defect_large_and_odd X H).1
    omega

#print axioms v174_shortcut_le_twice
#print axioms v174_actual_endpoint_bound
#print axioms v174_two_pow_mono
#print axioms v174_audited_endpoints_below_defect
#print axioms v174_freeze_matches_avoided_prefix
#print axioms v174_every_bounded_audit_agrees
#print axioms v174_false_map_has_two_disjoint_positive_classes

end SourceProduct
end CollatzFinal
