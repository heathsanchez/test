import Collatz.LawfulFutureJoin

namespace CollatzFinal

/-!
# V125: the mod-3 reverse-root theorem, with an exact counterfactual separator

A natural endpoint divisible by 3 has EXACTLY ONE positive predecessor
at each fixed reverse clock: its pure doubling ancestor. This is an
ALL-CLOCK theorem, not finite empirical search, and it says NOTHING
about eventual behavior of any source's FORWARD orbit.

For a positive source n divisible by 3, a lawful lower-source join
cannot have source clock 0. Thus the witness grammar must permit a
later real forward endpoint, and cannot be completed by reverse
search from the original source alone.

The V122 first lower-source clock for n=27 is 59. Yet inside its very
same parity cylinder 27 + 2^59*q, sources q=3*t+1 have an immediate
lower-source coalescence at clock 0. This distinguishes the protected
source's ternary offset, not the (identical) forward parity prefix.
-/

/-- Every shortcut predecessor of a multiple of 3 must be the
    even predecessor 2*y. An odd predecessor would require
    3*p+1=2*y, impossible modulo 3. -/
theorem three_reverse_step_unique
    (x y : Nat) (hy : y % 3 = 0)
    (hx : shortcut x = y) : x = 2 * y := by
  by_cases he : x % 2 = 0
  · have hq : x / 2 = y := by
      simpa [shortcut, he] using hx
    omega
  · have hq : (3 * x + 1) / 2 = y := by
      simpa [shortcut, he] using hx
    have hpar : x % 2 = 1 := by omega
    have hnum : (3 * x + 1) % 2 = 0 := by omega
    omega

/-- All inverse trajectories terminating at a multiple of 3 are
    uniquely its power-of-two doubling ray. -/
theorem three_reverse_ray_unique :
    ∀ k (y x : Nat), y % 3 = 0 →
       iter shortcut k x = y → x = 2 ^ k * y := by
  intro k
  induction k with
  | zero =>
      intro y x _ h
      simpa [iter] using h
  | succ k ih =>
      intro y x hy h
      have hlast :
          iter shortcut (k + 1) x =
            shortcut (iter shortcut k x) := by
        simpa [iter] using (iter_add shortcut k 1 x)
      have hprev : shortcut (iter shortcut k x) = y := by
        rw [← hlast]
        exact h
      have hback : iter shortcut k x = 2 * y :=
        three_reverse_step_unique _ _ hy hprev
      have hthree : (2 * y) % 3 = 0 := by omega
      have hx : x = 2 ^ k * (2 * y) :=
        ih (2 * y) x hthree hback
      calc
        x = 2 ^ k * (2 * y) := hx
        _ = 2 ^ (k + 1) * y := by
          simp [pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]

theorem shortcut_of_double (y : Nat) :
    shortcut (2 * y) = y := by
  have he : (2 * y) % 2 = 0 := by omega
  simp only [shortcut, if_pos he]
  omega

theorem three_reverse_ray_exists :
    ∀ k (y : Nat), iter shortcut k (2 ^ k * y) = y := by
  intro k
  induction k with
  | zero =>
      intro y
      simp [iter]
  | succ k ih =>
      intro y
      have hp : 2 ^ (k + 1) * y = 2 * (2 ^ k * y) := by
        simp [pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
      calc
        iter shortcut (k + 1) (2 ^ (k + 1) * y) =
            iter shortcut k (shortcut (2 ^ (k + 1) * y)) := rfl
        _ = iter shortcut k (2 ^ k * y) := by
          rw [hp, shortcut_of_double]
        _ = y := ih y

theorem all_preimages_of_three_multiple
    (k x y : Nat) (hy : y % 3 = 0) :
    iter shortcut k x = y ↔ x = 2 ^ k * y := by
  constructor
  · exact three_reverse_ray_unique k y x hy
  · intro h
    rw [h]
    exact three_reverse_ray_exists k y

/-- No strictly smaller positive source can reach a positive
    multiple-of-three endpoint at any reverse clock. -/
theorem no_lower_preimage_of_three_multiple
    (y p k : Nat) (hy : y % 3 = 0)
    (hlt : p < y) :
    iter shortcut k p ≠ y := by
  intro h
  have heq : p = 2 ^ k * y :=
    (all_preimages_of_three_multiple k p y hy).mp h
  have hp : (1 : Nat) ≤ 2 ^ k := by positivity
  have hle : y ≤ 2 ^ k * y := by
    simpa using (Nat.mul_le_mul_right y hp)
  omega

/-- This is a structural guarantee for EVERY lawful two-clock
    source-indexed witness, not an assumption about the Collatz conjecture. -/
theorem three_divisible_join_has_positive_source_clock
    (w : LawfulFutureJoin) (hy : w.source % 3 = 0) :
    0 < w.sourceClock := by
  by_contra hnot
  have hz : w.sourceClock = 0 := by omega
  have hp : iter shortcut w.earlierClock w.earlier = w.source := by
    simpa [hz, iter] using w.common.symm
  exact
    (no_lower_preimage_of_three_multiple
       w.source w.earlier w.earlierClock hy w.smaller) hp

/-!
A source-relative protected-future SEPARATOR: n=27 has exact earliest
smaller-source meeting time 59, but its dyadic parity-cylinder lift
n=27+2^59*(3*t+1) has a zero-clock lawful inverse-odd witness.

This does not extend the optimality bound 59 to its entire dyadic
cylinder. The new ternary coordinate is required by the protected
future and is not a redundant cached solver statistic.
-/

def three_lift_source (t : Nat) : Nat :=
  576460752303423515 + 1729382256910270464 * t

def three_lift_earlier (t : Nat) : Nat :=
  384307168202282343 + 1152921504606846976 * t

theorem three_lift_is_source27_dyadic (t : Nat) :
    three_lift_source t = 27 + 2 ^ 59 * (3 * t + 1) := by
  unfold three_lift_source
  norm_num
  omega

theorem three_lift_is_ternary_two (t : Nat) :
    (three_lift_source t) % 3 = 2 := by
  unfold three_lift_source
  omega

theorem three_lift_exact_inverse_odd (t : Nat) :
    shortcut (three_lift_earlier t) = three_lift_source t := by
  have heq :
      2 * three_lift_source t =
      3 * three_lift_earlier t + 1 := by
    unfold three_lift_source three_lift_earlier
    omega
  have hpodd : three_lift_earlier t % 2 ≠ 0 := by
    unfold three_lift_earlier
    omega
  simp only [shortcut, if_neg hpodd]
  omega

theorem three_lift_zero_clock_join (t : Nat) :
    ∃ w : LawfulFutureJoin,
      w.source = three_lift_source t ∧
      w.earlier = three_lift_earlier t ∧
      w.sourceClock = 0 ∧
      w.earlierClock = 1 := by
  have hp : 0 < three_lift_earlier t := by
    unfold three_lift_earlier
    omega
  have hlt : three_lift_earlier t < three_lift_source t := by
    unfold three_lift_earlier three_lift_source
    omega
  let w : LawfulFutureJoin :=
    { source := three_lift_source t
      earlier := three_lift_earlier t
      sourceClock := 0
      earlierClock := 1
      positive := hp
      smaller := hlt
      common := by
        simpa [iter] using (three_lift_exact_inverse_odd t).symm }
  exact ⟨w, rfl, rfl, rfl, rfl⟩

#print axioms three_reverse_step_unique
#print axioms three_reverse_ray_unique
#print axioms three_reverse_ray_exists
#print axioms all_preimages_of_three_multiple
#print axioms no_lower_preimage_of_three_multiple
#print axioms three_divisible_join_has_positive_source_clock
#print axioms three_lift_is_source27_dyadic
#print axioms three_lift_zero_clock_join

end CollatzFinal
