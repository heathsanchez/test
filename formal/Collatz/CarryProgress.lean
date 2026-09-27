import Collatz.OriginPhaseBarrier
import Collatz.SurvivalDeficit

namespace CollatzFinal
namespace SourceProduct

/-- Once the dyadic depth exceeds a fixed positive source, the exact
source-product tail is zero. From this point onward no new source bit/carry
can be supplied; only the actual endpoint dynamics remain. -/
theorem source_tail_zero_of_lt_pow
    {n k : Nat} (hn : 0 < n) (hlt : n < 2 ^ k) :
    (stateAt n k).tail = 0 := by
  have htail := (common_tail (at_valid hn k)).1
  rw [at_source, at_depth, Nat.div_eq_of_lt hlt] at htail
  exact htail.symm

/-- At zero tail the canonical source residue is the actual fixed source. -/
theorem sourceResidue_eq_source_of_tail_zero
    {s : State} (hs : Valid s) (hzero : s.tail = 0) :
    s.sourceResidue = s.source := by
  have he := hs.2.2.2
  simp [hzero] at he
  exact he.symm

/-- A zero source tail freezes the canonical source residue on the next step. -/
theorem sourceResidue_frozen_of_tail_zero
    (s : State) (hzero : s.tail = 0) :
    (step s).sourceResidue = s.sourceResidue := by
  simp [step, hzero]

/-- Exact one-step arithmetic behind a first coefficient crossing.

qmin <= q says the parent is still live. Both the actual odd-count increment
e and the moving coefficient-boundary increment delta are bits. If the child
falls below the boundary, the parent was exactly on it, the endpoint supplied
no odd-step replenishment, and the boundary carried. -/
theorem first_crossing_carry_shape
    {q qmin e delta : Nat}
    (he : e ≤ 1)
    (hdelta : delta ≤ 1)
    (hlive : qmin ≤ q)
    (hcross : q + e < qmin + delta) :
    q = qmin ∧ e = 0 ∧ delta = 1 := by
  omega

/-- The fatal carry shape is sufficient for a one-step boundary crossing. -/
theorem crossing_of_boundary_even_carry
    {q qmin e delta : Nat}
    (hboundary : q = qmin)
    (heven : e = 0)
    (hcarry : delta = 1) :
    q + e < qmin + delta := by
  omega

/-- Odd count never decreases along an actual source orbit. -/
theorem oddCount_le_succ (n k : Nat) :
    oddCount n k ≤ oddCount n (k + 1) := by
  simp only [oddCount]
  split <;> omega

/-- After the all-ones prefix of 2^j-1 has been consumed, the accumulated
odd-count credit j can only persist or increase. -/
theorem all_ones_tail_oddCount_lower (j t : Nat) :
    j ≤ oddCount (2 ^ j - 1) (j + t) := by
  induction t with
  | zero =>
      simpa using all_ones_odd_count j j (Nat.le_refl j)
  | succ t ih =>
      have hs := oddCount_le_succ (2 ^ j - 1) (j + t)
      rw [show j + (t + 1) = (j + t) + 1 by omega]
      exact Nat.le_trans ih hs

/-- Elementary base-gap inequality: three dyadic steps cost 8 while two
ternary credits provide 9. -/
private theorem two_pow_three_mul_le_three_pow_two_mul (r : Nat) :
    2 ^ (3 * r) ≤ 3 ^ (2 * r) := by
  induction r with
  | zero => norm_num
  | succ r ih =>
      have hm : 2 ^ (3 * r) * 8 ≤ 3 ^ (2 * r) * 9 :=
        Nat.mul_le_mul ih (by norm_num)
      calc
        2 ^ (3 * (r + 1)) = 2 ^ (3 * r + 3) := by congr 1 <;> omega
        _ = 2 ^ (3 * r) * 2 ^ 3 := by rw [Nat.pow_add]
        _ = 2 ^ (3 * r) * 8 := by norm_num
        _ ≤ 3 ^ (2 * r) * 9 := hm
        _ = 3 ^ (2 * r) * 3 ^ 2 := by norm_num
        _ = 3 ^ (2 * r + 2) := by rw [Nat.pow_add]
        _ = 3 ^ (2 * (r + 1)) := by congr 1 <;> omega

/-- Exact adversarial family against any constant post-origin block bound.
For n=2^(2r)-1, after the 2r source bits are exhausted the coefficient still
survives for every additional t<=r, regardless of what those later parity
bits are.  The proof uses only monotonicity of oddCount and 8^r<=9^r. -/
theorem all_ones_fixed_origin_survives_block
    (r t : Nat) (ht : t ≤ r) :
    CoefficientSurvives (2 ^ (2 * r) - 1) (2 * r + t) := by
  have hq :
      2 * r ≤ oddCount (2 ^ (2 * r) - 1) (2 * r + t) :=
    all_ones_tail_oddCount_lower (2 * r) t
  have hnum :
      3 ^ (2 * r) ≤
        3 ^ oddCount (2 ^ (2 * r) - 1) (2 * r + t) :=
    Nat.pow_le_pow_right (by decide : 0 < 3) hq
  have hexp : 2 * r + t ≤ 3 * r := by omega
  have hden : 2 ^ (2 * r + t) ≤ 2 ^ (3 * r) :=
    Nat.pow_le_pow_right (by decide : 0 < 2) hexp
  unfold CoefficientSurvives coefficientDenominator coefficientNumerator
  exact Nat.le_trans hden
    (Nat.le_trans (two_pow_three_mul_le_three_pow_two_mul r) hnum)

/-- Candidate stronger statement: a single constant B forces every positive
fixed-origin live source to coefficient-cross inside the next B steps. -/
def UniformFixedOriginBlock (B : Nat) : Prop :=
  ∀ n j, 0 < n → n < 2 ^ j → CoefficientSurvives n j →
    ∃ b, 0 < b ∧ b ≤ B ∧ ¬ CoefficientSurvives n (j + b)

/-- No such universal constant block exists.  For any proposed B, choose
r=B+1 and n=2^(2r)-1 at fixed-origin depth j=2r.  That actual positive source
remains coefficient-live for at least r>B further steps.

This is an all-depth theorem, not a finite counterexample search.  Therefore
the surviving Collatz residual must use an unbounded/adaptive carry resource;
a fixed B cannot close it. -/
theorem no_uniform_fixed_origin_block (B : Nat) :
    ¬ UniformFixedOriginBlock B := by
  intro hB
  let r := B + 1
  let j := 2 * r
  let n := 2 ^ j - 1
  have hr : 0 < r := by simp [r]
  have hp : 0 < 2 ^ (2 * B) := Nat.pow_pos (by decide : 0 < 2)
  have hjexp : j = 2 * B + 2 := by simp [j, r]; omega
  have hjpow : 2 ^ j = 2 ^ (2 * B) * 4 := by
    rw [hjexp, Nat.pow_add]
    norm_num
  have hn : 0 < n := by
    simp only [n]
    rw [hjpow]
    omega
  have hlt : n < 2 ^ j := by
    simp only [n]
    have hpos : 0 < 2 ^ j := Nat.pow_pos (by decide : 0 < 2)
    omega
  have hj : j = 2 * r := by rfl
  have hjlive : CoefficientSurvives n j := by
    rw [hj]
    exact all_ones_fixed_origin_survives_block r 0 (Nat.zero_le r)
  obtain ⟨b, hbpos, hbB, hcross⟩ := hB n j hn hlt hjlive
  have hbr : b ≤ r := by simp [r]; omega
  have hsurv : CoefficientSurvives n (j + b) := by
    rw [hj]
    exact all_ones_fixed_origin_survives_block r b hbr
  exact hcross hsurv

#print axioms source_tail_zero_of_lt_pow
#print axioms sourceResidue_eq_source_of_tail_zero
#print axioms sourceResidue_frozen_of_tail_zero
#print axioms first_crossing_carry_shape
#print axioms crossing_of_boundary_even_carry
#print axioms oddCount_le_succ
#print axioms all_ones_tail_oddCount_lower
#print axioms all_ones_fixed_origin_survives_block
#print axioms no_uniform_fixed_origin_block

end SourceProduct
end CollatzFinal
