import Collatz.NineCongruenceMerger

namespace CollatzFinal
namespace SourceProduct

/-
V115: two structural laws replace the three V113/V112/V114 depth-specific
(4,10), (5,11), (6,12) reverse certificates.

T^6(64*q+47) = 3*(81*q+60)+2, for EVERY q.
The affine transform F(n)=3*n+2 is equivariant on odd shortcut steps.
An even-then-odd boundary coalesces F(n) with n after two further steps.
This gives a variable-depth lower-source certificate for any initial
odd-run followed by even,odd. It does not prove every natural orbit has
that prefix, nor eliminate global Collatz counterexamples.
-/

/-- F(n)=3n+2 commutes with shortcut when n is odd. -/
theorem three_plus_two_commutes_odd (n : Nat) (hn : n % 2 = 1) :
    shortcut (3*n+2) = 3*shortcut n+2 := by
  have hn0 : n % 2 ≠ 0 := by omega
  have hm0 : (3*n+2) % 2 ≠ 0 := by omega
  simp only [shortcut, if_neg hn0, if_neg hm0]
  omega

/-- The first even shortcut changes the offset 2 to offset 1. -/
theorem three_plus_two_even_step (n : Nat) (hn : n % 2 = 0) :
    shortcut (3*n+2) = 3*shortcut n+1 := by
  have hm : (3*n+2) % 2 = 0 := by omega
  simp only [shortcut, if_pos hn, if_pos hm]
  omega

/-- That offset-1 branch collapses on the next odd shortcut. -/
theorem three_plus_one_odd_step (n : Nat) (hn : n % 2 = 1) :
    shortcut (3*n+1) = shortcut n := by
  have hn0 : n % 2 ≠ 0 := by omega
  have hm : (3*n+1) % 2 = 0 := by omega
  simp only [shortcut, if_neg hn0, if_pos hm]

/-- The local critical pair: even followed by odd makes the two
    trajectories literally equal, not merely congruent modulo a bound. -/
theorem three_plus_two_even_odd_collision (n : Nat)
    (heven : n % 2 = 0)
    (hodd : (shortcut n) % 2 = 1) :
    iter shortcut 2 (3*n+2) = iter shortcut 2 n := by
  have h1 := three_plus_two_even_step n heven
  have h2 := three_plus_one_odd_step (shortcut n) hodd
  change shortcut (shortcut (3*n+2)) = shortcut (shortcut n)
  rw [h1, h2]

/-- Exact six-step shortcut trace from a uniformly smaller predecessor. -/
theorem q7_shifted_six_step_predecessor (q : Nat) :
    iter shortcut 6 (64*q+47) = 3*(81*q+60)+2 := by
  have h1 : shortcut (64*q+47) = 96*q+71 := by
    have hpar : (64*q+47)%2 ≠ 0 := by omega
    simp only [shortcut, if_neg hpar]
    omega
  have h2 : shortcut (96*q+71) = 144*q+107 := by
    have hpar : (96*q+71)%2 ≠ 0 := by omega
    simp only [shortcut, if_neg hpar]
    omega
  have h3 : shortcut (144*q+107) = 216*q+161 := by
    have hpar : (144*q+107)%2 ≠ 0 := by omega
    simp only [shortcut, if_neg hpar]
    omega
  have h4 : shortcut (216*q+161) = 324*q+242 := by
    have hpar : (216*q+161)%2 ≠ 0 := by omega
    simp only [shortcut, if_neg hpar]
    omega
  have h5 : shortcut (324*q+242) = 162*q+121 := by
    have hpar : (324*q+242)%2 = 0 := by omega
    simp only [shortcut, if_pos hpar]
    omega
  have h6 : shortcut (162*q+121) = 243*q+182 := by
    have hpar : (162*q+121)%2 ≠ 0 := by omega
    simp only [shortcut, if_neg hpar]
    omega
  have hchain : iter shortcut 6 (64*q+47) = 243*q+182 := by
    simp only [iter, h1, h2, h3, h4, h5, h6]
  calc
    iter shortcut 6 (64*q+47) = 243*q+182 := hchain
    _ = 3*(81*q+60)+2 := by omega

/-- Source-attached odd prefix, retaining the actual shortcut path. -/
def InitialOddRun (n : Nat) : Nat → Prop
  | 0 => True
  | k+1 => n%2=1 ∧ InitialOddRun (shortcut n) k

/-- Odd-prefix conjugacy holds for every natural run length, not only
    the finite depths observed by the earlier reverse-word search. -/
theorem three_plus_two_transports_odd_run :
    ∀ k n, InitialOddRun n k →
      iter shortcut k (3*n+2) = 3*iter shortcut k n+2 := by
  intro k
  induction k with
  | zero =>
      intro n _
      rfl
  | succ k ih =>
      intro n hn
      rcases hn with ⟨hodd, htail⟩
      change iter shortcut k (shortcut (3*n+2)) =
        3*iter shortcut k (shortcut n)+2
      rw [three_plus_two_commutes_odd n hodd]
      exact ih (shortcut n) htail

/-- Any initial odd-run/even/odd critical pair closes F(n)=3n+2
    against the original source with equal forward clocks. -/
theorem three_plus_two_collision_after_odd_run (n k : Nat)
    (hodd : InitialOddRun n k)
    (heven : (iter shortcut k n)%2 = 0)
    (hnextodd : (shortcut (iter shortcut k n))%2 = 1) :
    iter shortcut (k+2) (3*n+2) = iter shortcut (k+2) n := by
  calc
    iter shortcut (k+2) (3*n+2) =
      iter shortcut 2 (iter shortcut k (3*n+2)) :=
        iter_add shortcut k 2 (3*n+2)
    _ = iter shortcut 2 (3*iter shortcut k n+2) := by
      rw [three_plus_two_transports_odd_run k n hodd]
    _ = iter shortcut 2 (iter shortcut k n) :=
      three_plus_two_even_odd_collision
        (iter shortcut k n) heven hnextodd
    _ = iter shortcut (k+2) n := (iter_add shortcut k 2 n).symm

/-- Consequence-level theorem: a whole infinite parametric family
    admits a genuinely smaller ORIGINAL source whenever the exact initial
    parity critical pair is present. No QED for general natural sources. -/
theorem q7_source_merge_of_odd_run_even_odd (q k : Nat)
    (hodd : InitialOddRun (81*q+60) k)
    (heven : (iter shortcut k (81*q+60))%2 = 0)
    (hnextodd :
      (shortcut (iter shortcut k (81*q+60)))%2 = 1) :
    LowerMerge shortcut (81*q+60) (64*q+47) := by
  have hc :=
    three_plus_two_collision_after_odd_run
      (81*q+60) k hodd heven hnextodd
  refine ⟨by omega, k+2, 6+(k+2), ?_⟩
  calc
    iter shortcut (k+2) (81*q+60) =
      iter shortcut (k+2) (3*(81*q+60)+2) := hc.symm
    _ = iter shortcut (k+2) (iter shortcut 6 (64*q+47)) := by
      rw [q7_shifted_six_step_predecessor q]
    _ = iter shortcut (6+(k+2)) (64*q+47) :=
      (iter_add shortcut 6 (k+2) (64*q+47)).symm

#print axioms three_plus_two_even_odd_collision
#print axioms q7_shifted_six_step_predecessor
#print axioms three_plus_two_transports_odd_run
#print axioms three_plus_two_collision_after_odd_run
#print axioms q7_source_merge_of_odd_run_even_odd

end SourceProduct
end CollatzFinal
