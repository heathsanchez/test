import Spec
import Init.Data.Nat.Fold
import Init.Data.Nat.Lemmas

namespace Submission

/-!
# Universal additive partition recurrence, from locked SAIR partAux

No generating-function assumption, no input-specific answer data, no holes.
This is the missing source-side recurrence needed for proving that a
formal product of geometric factors supplies the same coefficient family.

It is NOT an impl_correct proof for the Euler packed solver.
-/

def sumFold (q : Nat) (f : Nat → Nat) : Nat :=
  Nat.fold q (fun i _ acc => acc + f i) 0

theorem sumFold_succ (q : Nat) (f : Nat → Nat) :
    sumFold (q + 1) f = sumFold q f + f q := by
  rfl

theorem sumFold_shift :
    ∀ q (f : Nat → Nat),
      sumFold (q + 1) f = f 0 + sumFold q (fun j => f (j + 1))
  | 0, f => by
      simp [sumFold, Nat.fold]
  | q + 1, f => by
      rw [sumFold_succ, sumFold_shift q f, sumFold_succ]
      simp [Nat.add_assoc]

theorem sumFold_congr :
    ∀ q (f g : Nat → Nat),
      (∀ i, i < q → f i = g i) →
      sumFold q f = sumFold q g
  | 0, f, g, _ => rfl
  | q + 1, f, g, h => by
      rw [sumFold_succ, sumFold_succ]
      rw [sumFold_congr q f g (fun i hi => h i (by omega))]
      rw [h q (by omega)]

theorem natFold_sum_eq_list (f : Nat → Nat) :
    ∀ q, Nat.fold q (fun i _ acc => acc + f i) 0 =
      ((List.range q).map f).foldl (· + ·) 0
  | 0 => rfl
  | q + 1 => by
      rw [Nat.fold_succ, List.range_succ, List.map_append, List.foldl_append]
      simp only [List.map, List.foldl_cons, List.foldl_nil]
      rw [natFold_sum_eq_list f q]

theorem sumFold_eq_list (q : Nat) (f : Nat → Nat) :
    sumFold q f = ((List.range q).map f).foldl (· + ·) 0 := by
  exact natFold_sum_eq_list f q

/-- One formal geometric-factor action on an arbitrary sequence of values. -/
def geometricStep (step : Nat) (prev : Nat → Nat) (m : Nat) : Nat :=
  sumFold (m / step + 1)
    (fun j => prev (m - j * step))

/-- A finite geometric factor obeys the in-place coin-change recurrence. -/
theorem geometricStep_recurrence
    (step : Nat) (prev : Nat → Nat) (m : Nat) (hs : 0 < step) :
    geometricStep step prev m =
      prev m + (if step ≤ m then geometricStep step prev (m - step) else 0) := by
  by_cases hle : step ≤ m
  · rw [if_pos hle]
    unfold geometricStep
    rw [sumFold_shift]
    simp only [Nat.zero_mul, Nat.sub_zero]
    have hdiv : m / step = (m - step) / step + 1 := by
      conv => lhs
              rw [show m = (m - step) + step by omega]
      rw [Nat.add_div_right _ hs]
    rw [hdiv]
    apply congrArg (fun x => prev m + x)
    apply sumFold_congr
    intro j hj
    simp only [Nat.add_mul, Nat.one_mul, Nat.sub_sub]
    congr 1
    omega
  · rw [if_neg hle]
    have hlt : m < step := by omega
    unfold geometricStep
    rw [Nat.div_eq_of_lt hlt]
    simp [sumFold, Nat.fold]

theorem partAux_as_geometricStep (k n : Nat) :
    partAux (k + 1) n = geometricStep (k + 1) (partAux k) n := by
  change
    ((List.range (n / (k + 1) + 1)).map
      (fun j => partAux k (n - j * (k + 1)))).foldl (· + ·) 0 =
    sumFold (n / (k + 1) + 1)
      (fun j => partAux k (n - j * (k + 1)))
  exact (sumFold_eq_list _ _).symm

/-- The universal additive coin-change law derived from the locked spec.
Unlike the multiplicity-sum recurrence, this form can be realized by
multiplication by a formal geometric factor without separate summation. -/
theorem partAux_coinchange (k n : Nat) :
    partAux (k + 1) n =
      partAux k n +
        (if k + 1 ≤ n then
           partAux (k + 1) (n - (k + 1))
         else 0) := by
  calc
    partAux (k + 1) n =
        geometricStep (k + 1) (partAux k) n :=
          partAux_as_geometricStep k n
    _ = partAux k n +
          (if k + 1 ≤ n then
            geometricStep (k + 1) (partAux k) (n - (k + 1))
          else 0) :=
            geometricStep_recurrence (k + 1) (partAux k) n (by omega)
    _ = partAux k n +
          (if k + 1 ≤ n then
             partAux (k + 1) (n - (k + 1))
           else 0) := by
             rw [partAux_as_geometricStep k (n - (k + 1))]

#print axioms geometricStep_recurrence
#print axioms partAux_as_geometricStep
#print axioms partAux_coinchange

end Submission
