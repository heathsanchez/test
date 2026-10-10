import Collatz.FinalKernel

namespace CollatzFinal
namespace SourceProduct

/-!
V154: two-basin countercontrol for density amplification.

A deliberately non-Collatz map reproduces:
  * exact even shortcut, toy (2*n) = n for n > 0;
  * strict descent for EVERY n >= 4;
  * exponentially wide arithmetic interval families of actual
    predecessors of EVERY fixed positive target;
  * two separate absorbing positive roots, 1 and 3.

Thus positive predecessor density, strong finite descent, and a
positive-density known terminal basin cannot by themselves force
uniqueness of the terminal future class.

The genuine Collatz odd equation (3*n+1)/2 is a protected,
essential distinction. Nothing here claims a counterexample to
Collatz or removes V151's still-unproved density-one terminal premise.
-/

def v154Toy (n : Nat) : Nat :=
  if n = 1 then 1 else if n = 3 then 3 else n / 2

theorem v154_toy_one : v154Toy 1 = 1 := by decide
theorem v154_toy_two : v154Toy 2 = 1 := by decide
theorem v154_toy_three : v154Toy 3 = 3 := by decide

theorem v154_even_half (n : Nat) (hn : 0 < n) :
    v154Toy (2*n) = n := by
  have h1 : 2*n ≠ 1 := by omega
  have h3 : 2*n ≠ 3 := by omega
  simp [v154Toy,h1,h3]

theorem v154_eventual_strict_descent (n : Nat) (hn : 4 ≤ n) :
    v154Toy n < n := by
  have h1 : n ≠ 1 := by omega
  have h3 : n ≠ 3 := by omega
  simp [v154Toy,h1,h3]
  omega

theorem v154_step_at_positive_binary_block
    (q r : Nat) (hq : 2 ≤ q) :
    v154Toy (2*q+r) = q+r/2 := by
  have h1 : 2*q+r ≠ 1 := by omega
  have h3 : 2*q+r ≠ 3 := by omega
  simp [v154Toy,h1,h3]
  omega

/-- A complete source interval of length 2^t for every a>=2:
    all numbers 2^t*a + r, r<2^t, hit EXACT target a after t
    real steps; not a mere cardinality or root-class assumption. -/
theorem v154_every_target_binary_interval (t : Nat) :
    ∀ a r : Nat, 2 ≤ a → r < 2^t →
      iter v154Toy t (2^t*a+r) = a := by
  induction t with
  | zero =>
      intro a r _ hr
      have hr0 : r=0 := by simpa using hr
      simp [iter,hr0]
  | succ t ih =>
      intro a r ha hr
      have hp : 0 < (2:Nat)^t := Nat.pow_pos (by decide)
      have hq : 2 ≤ 2^t*a := by
        have hmul := Nat.mul_le_mul_right a (show 1 ≤ (2:Nat)^t by omega)
        omega
      have heq : 2^(t+1)*a+r = 2*(2^t*a)+r := by
        rw [Nat.pow_succ]
        ac_rfl
      have hsmall : r/2 < 2^t := by
        have ht : r < 2*(2^t) := by
          simpa [Nat.pow_succ, Nat.mul_comm] using hr
        omega
      have hstep :
          v154Toy (2^(t+1)*a+r) = 2^t*a+r/2 := by
        rw [heq]
        exact v154_step_at_positive_binary_block (2^t*a) r hq
      calc
        iter v154Toy (t+1) (2^(t+1)*a+r) =
            iter v154Toy t (v154Toy (2^(t+1)*a+r)) := by rfl
        _ = iter v154Toy t (2^t*a+r/2) := by rw [hstep]
        _ = a := ih a (r/2) ha hsmall

theorem v154_one_is_absorbing (t : Nat) :
    iter v154Toy t 1 = 1 := by
  induction t with
  | zero => rfl
  | succ t ih => simpa [iter,v154_toy_one] using ih

theorem v154_three_is_absorbing (t : Nat) :
    iter v154Toy t 3 = 3 := by
  induction t with
  | zero => rfl
  | succ t ih => simpa [iter,v154_toy_three] using ih

theorem v154_two_families_reach_one
    (t r : Nat) (hr : r < 2^t) :
    iter v154Toy (t+1) (2^t*2+r) = 1 := by
  have heq := v154_every_target_binary_interval t 2 r (by decide) hr
  calc
    iter v154Toy (t+1) (2^t*2+r) =
      iter v154Toy 1 (iter v154Toy t (2^t*2+r)) := by
        simpa using (iter_add v154Toy t 1 (2^t*2+r))
    _ = 1 := by simp [heq,iter,v154_toy_two]

theorem v154_three_families_reach_three
    (t r : Nat) (hr : r < 2^t) :
    iter v154Toy t (2^t*3+r) = 3 :=
  v154_every_target_binary_interval t 3 r (by decide) hr

/-- Deterministic trajectories cannot hit both distinct absorbing
    roots. In particular every certified target-3 ancestor is NOT
    a terminal-1 ancestor. -/
theorem v154_reach_three_excludes_one
    {n : Nat} (hthree : ∃ t, iter v154Toy t n = 3) :
    ¬ Eventually v154Toy (fun x => x = 1) n := by
  intro hgood
  obtain ⟨t,ht⟩ := hthree
  obtain ⟨s,hs⟩ := hgood
  by_cases hst : s ≤ t
  · have hsum : s + (t-s) = t := by omega
    have hf := iter_add v154Toy s (t-s) n
    rw [hsum,hs,v154_one_is_absorbing] at hf
    omega
  · have hts : t ≤ s := by omega
    have hsum : t + (s-t) = s := by omega
    have hf := iter_add v154Toy t (s-t) n
    rw [hsum,ht,v154_three_is_absorbing] at hf
    omega

theorem v154_target_three_has_infinite_bad_blocks
    (t r : Nat) (hr : r < 2^t) :
    ¬ Eventually v154Toy (fun x => x = 1) (2^t*3+r) := by
  apply v154_reach_three_excludes_one
  exact ⟨t,v154_three_families_reach_three t r hr⟩

theorem v154_one_is_good :
    Eventually v154Toy (fun x => x=1) 1 :=
  ⟨0,rfl⟩

theorem v154_three_is_bad :
    ¬ Eventually v154Toy (fun x => x=1) 3 := by
  exact v154_reach_three_excludes_one ⟨0,rfl⟩

#print axioms v154_even_half
#print axioms v154_eventual_strict_descent
#print axioms v154_step_at_positive_binary_block
#print axioms v154_every_target_binary_interval
#print axioms v154_two_families_reach_one
#print axioms v154_target_three_has_infinite_bad_blocks
#print axioms v154_one_is_good
#print axioms v154_three_is_bad

end SourceProduct
end CollatzFinal
