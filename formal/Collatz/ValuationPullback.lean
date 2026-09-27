import Collatz.AssembledConstructorCloseout

namespace CollatzFinal
namespace SourceProduct

/-- Repeated source lift underlying the valuation-pullback constructor.
Closed form: ownerLift k p = 4^k*p + (4^k-1)/3. -/
def ownerLift : Nat → Nat → Nat
  | 0, p => p
  | k + 1, p => 4 * ownerLift k p + 1

theorem ownerLift_odd
    {p : Nat} (hpodd : p % 2 = 1) :
    ∀ k, ownerLift k p % 2 = 1 := by
  intro k
  induction k with
  | zero => simpa [ownerLift] using hpodd
  | succ k =>
      change (4 * ownerLift k p + 1) % 2 = 1
      omega

/-- One lift layer adds exactly two redundant shortcut steps:
three steps from 4*x+1 coalesce with one step from odd x. -/
theorem iter_three_four_mul_add_one
    {x : Nat} (hxodd : x % 2 = 1) :
    iter shortcut 3 (4 * x + 1) = shortcut x := by
  have hxne : x % 2 ≠ 0 := by omega
  have h1 : shortcut (4 * x + 1) = 6 * x + 2 := by
    unfold shortcut
    have ho : (4 * x + 1) % 2 ≠ 0 := by omega
    simp only [ho, ite_false]
    omega
  have h2 : shortcut (6 * x + 2) = 3 * x + 1 := by
    unfold shortcut
    have he : (6 * x + 2) % 2 = 0 := by omega
    simp only [he, ite_true]
    omega
  have h3 : shortcut (3 * x + 1) = shortcut x := by
    unfold shortcut
    have he : (3 * x + 1) % 2 = 0 := by omega
    simp only [he, ite_true, hxne, ite_false]
  simp [iter, h1, h2, h3]

/-- Exact parametric coalescence law for every owner lift. -/
theorem ownerLift_coalesces
    {p : Nat} (hpodd : p % 2 = 1) :
    ∀ k, iter shortcut (2 * k + 1) (ownerLift k p) = shortcut p := by
  intro k
  induction k with
  | zero =>
      simp [ownerLift, iter]
  | succ k ih =>
      have hkodd : ownerLift k p % 2 = 1 := ownerLift_odd hpodd k
      have h3 :
          iter shortcut 3 (ownerLift (k + 1) p) =
            shortcut (ownerLift k p) := by
        simpa [ownerLift] using iter_three_four_mul_add_one hkodd
      calc
        iter shortcut (2 * (k + 1) + 1) (ownerLift (k + 1) p) =
            iter shortcut (2 * k)
              (iter shortcut 3 (ownerLift (k + 1) p)) := by
                rw [show 2 * (k + 1) + 1 = 3 + 2 * k by omega, iter_add]
        _ = iter shortcut (2 * k) (shortcut (ownerLift k p)) := by rw [h3]
        _ = iter shortcut (2 * k + 1) (ownerLift k p) := by
              simp [iter]
        _ = shortcut p := ih

/-- If an owner lift occurs on n's orbit and its owner p is smaller than n,
it is an exact lower-source coalescence certificate. -/
theorem lower_merge_of_ownerLift_on_orbit
    {n p j k : Nat}
    (hpodd : p % 2 = 1)
    (hlt : p < n)
    (horbit : iter shortcut j n = ownerLift k p) :
    LowerMerge shortcut n p := by
  refine ⟨hlt, j + (2 * k + 1), 1, ?_⟩
  rw [iter_add, horbit]
  simpa [iter] using ownerLift_coalesces hpodd k

/-- Ordinary-exit form of the same constructor at the common future. -/
theorem ordinary_exit_of_ownerLift_on_orbit
    {n p j k : Nat}
    (hp : 0 < p)
    (hpodd : p % 2 = 1)
    (hlt : p < n)
    (horbit : iter shortcut j n = ownerLift k p) :
    ∃ a, OrdinaryExit n (iter shortcut a n) := by
  refine ⟨j + (2 * k + 1), ?_⟩
  refine Or.inr (Or.inr ⟨p, 1, hp, hlt, ?_⟩)
  rw [iter_add, horbit]
  simpa [iter] using (ownerLift_coalesces hpodd k).symm

/-- On a hypothetical minimal positive bad orbit, every exact owner-lift
representation is source-anchored: its odd owner cannot lie below the source.
Otherwise the valuation-pullback constructor gives a lower-source ordinary
exit. -/
theorem minimal_bad_ownerLift_owner_ge
    {n p j k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hp : 0 < p)
    (hpodd : p % 2 = 1)
    (horbit : iter shortcut j n = ownerLift k p) :
    n ≤ p := by
  apply Nat.le_of_not_gt
  intro hlt
  obtain ⟨a, hexit⟩ :=
    ordinary_exit_of_ownerLift_on_orbit hp hpodd hlt horbit
  exact minimal_bad_has_no_ordinary_exit hmin a hexit


/-- ownerLift is monotone in its owner coordinate at every lift depth. -/
theorem ownerLift_mono
    (k : Nat) {a b : Nat} (hab : a ≤ b) :
    ownerLift k a ≤ ownerLift k b := by
  induction k with
  | zero =>
      simpa [ownerLift] using hab
  | succ k ih =>
      simp only [ownerLift]
      exact Nat.add_le_add_right (Nat.mul_le_mul_left 4 ih) 1

/-- Universal source-relative owner-lift barrier.

On a hypothetical minimal bad source n, an orbit occurrence of ownerLift k p
cannot sit below ownerLift k n: the coalescing owner p is forced to be at least
n, and ownerLift preserves source order.  This packages every finite
mod-8/mod-2^m valuation exclusion into one parametric height inequality. -/
theorem minimal_bad_ownerLift_height_ge
    {n p j k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hp : 0 < p)
    (hpodd : p % 2 = 1)
    (horbit : iter shortcut j n = ownerLift k p) :
    ownerLift k n ≤ iter shortcut j n := by
  have hpn : n ≤ p :=
    minimal_bad_ownerLift_owner_ge hmin hp hpodd horbit
  rw [horbit]
  exact ownerLift_mono k hpn

/-- Contrapositive constructor form: any represented owner lift below the
source-matched lift height is already an ordinary exit. -/
theorem ordinary_exit_of_ownerLift_below_source_height
    {n p j k : Nat}
    (hp : 0 < p)
    (hpodd : p % 2 = 1)
    (horbit : iter shortcut j n = ownerLift k p)
    (hlt : iter shortcut j n < ownerLift k n) :
    ∃ a, OrdinaryExit n (iter shortcut a n) := by
  have hpn : p < n := by
    apply Nat.lt_of_not_ge
    intro hnp
    have hmono := ownerLift_mono k hnp
    rw [← horbit] at hmono
    exact (Nat.not_le_of_gt hlt) hmono
  exact ordinary_exit_of_ownerLift_on_orbit hp hpodd hpn horbit

/-- First concrete valuation barrier.  Below 4*n+1 a minimal-bad orbit cannot
occupy residue 5 modulo 8, because every such value is exactly ownerLift 1 p
for an odd p<n. -/
theorem minimal_bad_below_four_source_not_mod8_five
    {n j : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hlt : iter shortcut j n < 4 * n + 1) :
    iter shortcut j n % 8 ≠ 5 := by
  intro hmod
  let x := iter shortcut j n
  let a := x / 8
  let p := 2 * a + 1
  have hx : x = 8 * a + 5 := by
    have hd := Nat.mod_add_div x 8
    dsimp [a]
    omega
  have hp : 0 < p := by
    dsimp [p]
    omega
  have hpodd : p % 2 = 1 := by
    dsimp [p]
    omega
  have hlift : ownerLift 1 p = x := by
    simp [ownerLift, p]
    omega
  have horbit : iter shortcut j n = ownerLift 1 p := by
    simpa [x] using hlift.symm
  have hge := minimal_bad_ownerLift_owner_ge hmin hp hpodd horbit
  have hxp : x = 4 * p + 1 := by
    calc
      x = ownerLift 1 p := hlift.symm
      _ = 4 * p + 1 := by simp [ownerLift]
  omega

/-- The old mod-12 large-crossing signature refines immediately once the
valuation barrier is joined with the first forced odd step.  The 19 mod 48
subclass would send the next orbit value into residue 5 mod 8 while it is still
below 4*n+1, which the owner-lift barrier forbids. -/
theorem minimal_bad_large_crossing_not_mod48_nineteen
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hfirst : FirstCoefficientCrossingAt n (k + 1))
    (hq : oddCount n (k + 1) < n) :
    iter shortcut (k + 1) n % 48 ≠ 19 := by
  let y := iter shortcut (k + 1) n
  let z := iter shortcut (k + 2) n
  have hsig :=
    minimal_bad_hard_crossing_large_source_signature hmin hfirst hq
  have hyodd : y % 2 ≠ 0 := by
    have hy : y % 2 = 1 := by
      simpa [y] using hsig.2.1
    omega
  have hzrel : 2 * z = 3 * y + 1 := by
    have hs := iter_succ_last n (k + 1)
    have hd := double_shortcut y
    rw [if_neg hyodd] at hd
    dsimp [z]
    rw [hs]
    simpa [y] using hd
  have hwin :
      3 * y < 4 * n := by
    simpa [y] using
      first_crossing_three_y_lt_four_n hmin.1.1 hfirst hq
  have hzlt : z < 4 * n + 1 := by
    have hn : 0 < n := hmin.1.1
    omega
  have hznot :
      z % 8 ≠ 5 := by
    simpa [z] using
      minimal_bad_below_four_source_not_mod8_five
        (j := k + 2) hmin (by simpa [z] using hzlt)
  intro h19
  have hy19 : y % 48 = 19 := by
    simpa [y] using h19
  have hz5 : z % 8 = 5 := by
    omega
  exact hznot hz5

/-- Pushing the same source-anchored valuation barrier through the second
forced odd step removes a second 2-adic refinement: y = 55 mod 96 would put
the depth-(k+3) value in residue 5 mod 8 while it is still at most 3*n. -/
theorem minimal_bad_large_crossing_not_mod96_fiftyfive
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hfirst : FirstCoefficientCrossingAt n (k + 1))
    (hq : oddCount n (k + 1) < n) :
    iter shortcut (k + 1) n % 96 ≠ 55 := by
  let y := iter shortcut (k + 1) n
  let z := iter shortcut (k + 2) n
  let w := iter shortcut (k + 3) n
  have hsig :=
    minimal_bad_hard_crossing_large_source_signature hmin hfirst hq
  have hyodd : y % 2 ≠ 0 := by
    have hy : y % 2 = 1 := by
      simpa [y] using hsig.2.1
    omega
  have hzodd : z % 2 ≠ 0 := by
    have hz : shortcut y % 2 = 1 := hsig.2.2
    have hzy : z = shortcut y := by
      dsimp [z, y]
      exact iter_succ_last n (k + 1)
    rw [hzy]
    omega
  have hzrel : 2 * z = 3 * y + 1 := by
    have hs := iter_succ_last n (k + 1)
    have hd := double_shortcut y
    rw [if_neg hyodd] at hd
    dsimp [z]
    rw [hs]
    simpa [y] using hd
  have hwrel : 2 * w = 3 * z + 1 := by
    have hs := iter_succ_last n (k + 2)
    have hd := double_shortcut z
    rw [if_neg hzodd] at hd
    dsimp [w]
    rw [hs]
    simpa [z] using hd
  have hwin : 3 * y < 4 * n := by
    simpa [y] using
      first_crossing_three_y_lt_four_n hmin.1.1 hfirst hq
  have hwlt : w < 4 * n + 1 := by
    have hn : 0 < n := hmin.1.1
    omega
  have hwnot : w % 8 ≠ 5 := by
    simpa [w] using
      minimal_bad_below_four_source_not_mod8_five
        (j := k + 3) hmin (by simpa [w] using hwlt)
  intro h55
  have hy55 : y % 96 = 55 := by
    simpa [y] using h55
  have hw5 : w % 8 = 5 := by
    omega
  exact hwnot hw5

#print axioms minimal_bad_large_crossing_not_mod96_fiftyfive

#print axioms minimal_bad_large_crossing_not_mod48_nineteen

#print axioms ownerLift_mono
#print axioms minimal_bad_ownerLift_height_ge
#print axioms ordinary_exit_of_ownerLift_below_source_height
#print axioms minimal_bad_ownerLift_owner_ge
#print axioms minimal_bad_below_four_source_not_mod8_five

#print axioms ownerLift_coalesces
#print axioms lower_merge_of_ownerLift_on_orbit
#print axioms ordinary_exit_of_ownerLift_on_orbit

end SourceProduct
end CollatzFinal
