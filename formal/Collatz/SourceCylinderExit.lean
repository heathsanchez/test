import Collatz.SourceProductAffine
import Collatz.OrdinaryExitReduction

namespace CollatzFinal.SourceProduct

/-- Exact parity-word availability on a dyadic source cylinder. -/
theorem shortcut_iter_source_lift (n k u : Nat) :
    iter shortcut k (n + 2 ^ k * u) =
      iter shortcut k n + 3 ^ oddCount n k * u := by
  induction k generalizing u with
  | zero => simp [iter, oddCount]
  | succ k ih =>
      rw [iter_succ_last]
      have hsource : n + 2 ^ (k + 1) * u = n + 2 ^ k * (2 * u) := by
        simp [Nat.pow_succ, Nat.mul_assoc]
      rw [hsource, ih]
      have hshift : 3 ^ oddCount n k * (2 * u) =
          2 * (3 ^ oddCount n k * u) := by
        simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
      rw [hshift, shortcut_shift]
      by_cases h : iter shortcut k n % 2 = 0 <;>
        simp [oddCount, h, iter_succ_last, Nat.pow_succ,
          Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]

/-- Linear-time certificate evaluator; its correctness is proved independently. -/
def sourceOrbit (n : Nat) : Nat → Nat × Nat
  | 0 => (n, 0)
  | k + 1 =>
      let z := sourceOrbit n k
      (shortcut z.1, if z.1 % 2 = 0 then z.2 else z.2 + 1)

theorem sourceOrbit_correct (n k : Nat) :
    sourceOrbit n k = (iter shortcut k n, oddCount n k) := by
  induction k with
  | zero => rfl
  | succ k ih =>
      simp only [sourceOrbit, ih, oddCount, iter_succ_last]

/-- A source-bound descent with slope at most one lifts to every natural
parameter. The actual iterate, not an assumed affine equation, is certified. -/
theorem ordinary_exit_of_source_cylinder_direct
    {n k y q : Nat}
    (htrace : sourceOrbit n k = (y, q))
    (hpositive : 0 < y)
    (hbelow : y < n)
    (hslope : 3 ^ q ≤ 2 ^ k)
    (u : Nat) :
    OrdinaryExit (n + 2 ^ k * u)
      (iter shortcut k (n + 2 ^ k * u)) := by
  have hpair := (sourceOrbit_correct n k).symm.trans htrace
  have hy : iter shortcut k n = y := congrArg Prod.fst hpair
  have hq : oddCount n k = q := congrArg Prod.snd hpair
  rw [shortcut_iter_source_lift, hy, hq]
  have hmul := Nat.mul_le_mul_right u hslope
  exact Or.inr (Or.inl ⟨by omega, by omega⟩)

/-- An exact odd lower-source merge lifts with its own source preserved.
This includes the three-step quarter-splice once its common endpoint is paid. -/
theorem ordinary_exit_of_source_cylinder_odd_merge
    {n k y q p : Nat}
    (htrace : sourceOrbit n k = (y, q + 1))
    (hpositive : 0 < p)
    (hbelow : p < n)
    (hodd : p % 2 = 1)
    (hmerge : shortcut p = y)
    (hslope : 2 * 3 ^ q ≤ 2 ^ k)
    (u : Nat) :
    OrdinaryExit (n + 2 ^ k * u)
      (iter shortcut k (n + 2 ^ k * u)) := by
  have hpair := (sourceOrbit_correct n k).symm.trans htrace
  have hy : iter shortcut k n = y := congrArg Prod.fst hpair
  have hq : oddCount n k = q + 1 := congrArg Prod.snd hpair
  rw [shortcut_iter_source_lift, hy, hq]
  let lower := p + 2 * (3 ^ q * u)
  have hlt : lower < n + 2 ^ k * u := by
    have hmul := Nat.mul_le_mul_right u hslope
    dsimp [lower]
    have heq : 2 * (3 ^ q * u) = (2 * 3 ^ q) * u := by
      simp [Nat.mul_assoc]
    rw [heq]
    omega
  have hstep : shortcut lower = y + 3 ^ (q + 1) * u := by
    dsimp [lower]
    rw [shortcut_shift, hmerge]
    have hnot : p % 2 ≠ 0 := by omega
    simp [hnot, Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
  refine Or.inr (Or.inr ⟨lower, 1, ?_, hlt, ?_⟩)
  · dsimp [lower]
    omega
  · simpa [iter] using hstep

#print axioms shortcut_iter_source_lift
#print axioms sourceOrbit_correct
#print axioms ordinary_exit_of_source_cylinder_direct
#print axioms ordinary_exit_of_source_cylinder_odd_merge

end CollatzFinal.SourceProduct
