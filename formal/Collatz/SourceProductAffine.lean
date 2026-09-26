import Collatz.SourceProduct

namespace CollatzFinal
namespace SourceProduct

/-- Odd steps counted directly on the source orbit, independently of the product. -/
def oddCount (n : Nat) : Nat → Nat
  | 0 => 0
  | k + 1 => if iter shortcut k n % 2 = 0 then oddCount n k else oddCount n k + 1

/-- Full affine intercept, independently accumulated on the source orbit. -/
def bias (n : Nat) : Nat → Nat
  | 0 => 0
  | k + 1 => if iter shortcut k n % 2 = 0 then bias n k else 3 * bias n k + 2 ^ k

theorem local_parity (s : State) :
    (s.endpointResidue + 3 ^ s.odds * (s.tail % 2)) % 2 = endpoint s % 2 := by
  unfold endpoint
  rw [split_mul (3 ^ s.odds) s.tail]
  omega

theorem at_odds (n k : Nat) : (stateAt n k).odds = oddCount n k := by
  induction k with
  | zero => rfl
  | succ k ih =>
      change (if ((stateAt n k).endpointResidue +
          3 ^ (stateAt n k).odds * ((stateAt n k).tail % 2)) % 2 = 0
        then (stateAt n k).odds else (stateAt n k).odds + 1) = _
      rw [local_parity, at_endpoint, ih]
      rfl

theorem double_shortcut (x : Nat) :
    2 * shortcut x = (if x % 2 = 0 then x else 3 * x + 1) := by
  unfold shortcut
  split <;> omega

theorem exact_affine (n k : Nat) :
    2 ^ k * iter shortcut k n = 3 ^ oddCount n k * n + bias n k := by
  induction k with
  | zero => simp [iter, oddCount, bias]
  | succ k ih =>
      have hm := congrArg (fun z => 2 ^ k * z) (double_shortcut (iter shortcut k n))
      rw [iter_succ_last]
      by_cases h : iter shortcut k n % 2 = 0
      · simp only [h, ite_true] at hm
        simp only [oddCount, bias, h, ite_true, Nat.pow_succ]
        calc
          2 ^ k * 2 * shortcut (iter shortcut k n) =
              2 ^ k * (2 * shortcut (iter shortcut k n)) := by simp [Nat.mul_assoc]
          _ = 2 ^ k * iter shortcut k n := hm
          _ = _ := ih
      · simp only [h, ite_false] at hm
        simp only [oddCount, bias, h, ite_false, Nat.pow_succ]
        calc
          2 ^ k * 2 * shortcut (iter shortcut k n) =
              2 ^ k * (2 * shortcut (iter shortcut k n)) := by simp [Nat.mul_assoc]
          _ = 2 ^ k * (3 * iter shortcut k n + 1) := hm
          _ = 3 * (2 ^ k * iter shortcut k n) + 2 ^ k := by
            simp [Nat.mul_add, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
          _ = 3 * (3 ^ oddCount n k * n + bias n k) + 2 ^ k := by rw [ih]
          _ = _ := by
            simp [Nat.mul_add, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm, Nat.add_assoc]

/-- The product stores the same exact affine source/endpoint coupling. -/
theorem residue_cocycle {n : Nat} (hn : 0 < n) (k : Nat) :
    2 ^ k * (stateAt n k).endpointResidue =
      3 ^ (stateAt n k).odds * (stateAt n k).sourceResidue + bias n k := by
  let s := stateAt n k
  have hs : Valid s := at_valid hn k
  have he : 2 ^ s.depth * endpoint s = 3 ^ s.odds * s.source + bias n k := by
    simpa only [s, at_depth, at_endpoint, at_odds, at_source] using exact_affine n k
  have he' : 2 ^ s.depth * (s.endpointResidue + 3 ^ s.odds * s.tail) =
      3 ^ s.odds * (s.sourceResidue + 2 ^ s.depth * s.tail) + bias n k := by
    calc
      _ = 3 ^ s.odds * s.source + bias n k := he
      _ = _ := by rw [hs.2.2.2]
  simp only [Nat.mul_add] at he'
  have ht : 2 ^ s.depth * (3 ^ s.odds * s.tail) =
      3 ^ s.odds * (2 ^ s.depth * s.tail) := by
    simp [Nat.mul_assoc, Nat.mul_left_comm]
  rw [ht] at he'
  have hc : 2 ^ s.depth * s.endpointResidue =
      3 ^ s.odds * s.sourceResidue + bias n k := by omega
  simpa only [s, at_depth] using hc

/-- At a coefficient crossing, non-descent of an actual source forces the
    canonical residue cylinder to have nonnegative exact joint margin.
    This is the universal bridge from the source-product representation to
    the archived M-verifier problem. -/
theorem canonical_margin_nonnegative_of_nondescending
    {n k : Nat} (hn : 0 < n)
    (hcross : 3 ^ (stateAt n k).odds < 2 ^ k)
    (hnd : n <= iter shortcut k n) :
    (2 ^ k - 3 ^ (stateAt n k).odds) * (stateAt n k).sourceResidue
      <= bias n k := by
  let s := stateAt n k
  have hs : Valid s := at_valid hn k
  have hdepth : s.depth = k := by simpa [s] using at_depth n k
  have hsource : s.source = n := by simpa [s] using at_source n k
  have hendpoint : endpoint s = iter shortcut k n := by
    simpa [s] using at_endpoint n k
  have hnd' : s.source <= endpoint s := by
    simpa [hsource, hendpoint] using hnd
  have hscale :
      3 ^ s.odds * s.tail <= 2 ^ k * s.tail := by
    exact Nat.mul_le_mul_right s.tail (Nat.le_of_lt (by simpa [s] using hcross))
  have hres : s.sourceResidue <= s.endpointResidue := by
    have hsrc := hs.2.2.2
    rw [hdepth] at hsrc
    simp only [endpoint] at hnd'
    rw [hsrc] at hnd'
    omega
  have hc :
      2 ^ k * s.endpointResidue =
        3 ^ s.odds * s.sourceResidue + bias n k := by
    simpa [s] using residue_cocycle hn k
  have hmul :
      2 ^ k * s.sourceResidue <=
        3 ^ s.odds * s.sourceResidue + bias n k := by
    calc
      2 ^ k * s.sourceResidue <= 2 ^ k * s.endpointResidue :=
        Nat.mul_le_mul_left (2 ^ k) hres
      _ = _ := hc
  change (2 ^ k - 3 ^ s.odds) * s.sourceResidue <= bias n k
  rw [Nat.sub_mul]
  omega


/-- If the affine bias is smaller than one full tail unit across a coefficient
    crossing, a nondescending source cannot carry any nonzero product tail.
    This is the algebraic core of the first-crossing zero-tail reduction. -/
theorem tail_eq_zero_of_nondescending_of_bias_lt_tail_unit
    {n k : Nat} (hn : 0 < n)
    (hcross : 3 ^ (stateAt n k).odds < 2 ^ k)
    (hnd : n <= iter shortcut k n)
    (hbias :
      bias n k <
        2 ^ k * (2 ^ k - 3 ^ (stateAt n k).odds)) :
    (stateAt n k).tail = 0 := by
  let s := stateAt n k
  have hs : Valid s := at_valid hn k
  have hdepth : s.depth = k := by simpa [s] using at_depth n k
  have hsource : s.source = n := by simpa [s] using at_source n k
  have hendpoint : endpoint s = iter shortcut k n := by
    simpa [s] using at_endpoint n k
  have hnd' : s.source <= endpoint s := by
    simpa [hsource, hendpoint] using hnd
  have hsrc := hs.2.2.2
  rw [hdepth] at hsrc
  simp only [endpoint] at hnd'
  rw [hsrc] at hnd'
  have hc :
      2 ^ k * s.endpointResidue =
        3 ^ s.odds * s.sourceResidue + bias n k := by
    simpa [s] using residue_cocycle hn k
  have hcross' : 3 ^ s.odds < 2 ^ k := by simpa [s] using hcross
  have htail :
      2 ^ k * (2 ^ k - 3 ^ s.odds) * s.tail <= bias n k := by
    rw [Nat.sub_mul]
    have hscaled := Nat.mul_le_mul_left (2 ^ k) hnd'
    simp only [Nat.mul_add] at hscaled
    omega
  have hbias' :
      bias n k < 2 ^ k * (2 ^ k - 3 ^ s.odds) := by
    simpa [s] using hbias
  cases Nat.eq_zero_or_pos s.tail with
  | inl hz => exact hz
  | inr htpos =>
      have hone :
          2 ^ k * (2 ^ k - 3 ^ s.odds) <=
            2 ^ k * (2 ^ k - 3 ^ s.odds) * s.tail := by
        have hmul := Nat.mul_le_mul_left
          (2 ^ k * (2 ^ k - 3 ^ s.odds)) htpos
        simpa [Nat.mul_assoc] using hmul
      omega


#print axioms at_odds
#print axioms exact_affine
#print axioms residue_cocycle
#print axioms canonical_margin_nonnegative_of_nondescending
#print axioms tail_eq_zero_of_nondescending_of_bias_lt_tail_unit

end SourceProduct
end CollatzFinal
