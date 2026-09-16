import Init

/-- Forward reachability under a deterministic map. -/
inductive Reach (f : Nat → Nat) : Nat → Nat → Prop where
  | refl (a : Nat) : Reach f a a
  | step {a b c : Nat} : f a = b → Reach f b c → Reach f a c

namespace Reach

theorem trans {f : Nat → Nat} {a b c : Nat}
    (hab : Reach f a b) (hbc : Reach f b c) : Reach f a c := by
  induction hab with
  | refl => exact hbc
  | step hxy hyr ih =>
      exact Reach.step hxy (ih hbc)

theorem tailOfNe {f : Nat → Nat} {a z : Nat}
    (h : Reach f a z) (hne : a ≠ z) : Reach f (f a) z := by
  cases h with
  | refl =>
      exact False.elim (hne rfl)
  | step hab htail =>
      rw [hab]
      exact htail

end Reach

def Converges (f : Nat → Nat) (n : Nat) : Prop :=
  Reach f n 1

/--
A strict lower witness for n.

Either:
* a positive y < n is reached directly from n; or
* n reaches y, while a positive p < n has f p = y.

The p = 1 edge case additionally records f y = 1.  This is exactly the
small exception needed because convergence of p = 1 is reflexive rather than
being witnessed through its first successor.
-/
structure LowerWitness (f : Nat → Nat) (n : Nat) where
  y : Nat
  reach : Reach f n y
  kind :
    (0 < y ∧ y < n) ∨
    (∃ p : Nat, 0 < p ∧ p < n ∧ f p = y ∧ (p = 1 → f y = 1))

/--
Abstract strong-induction closure theorem.

If every n > 1 has a LowerWitness, then every positive natural converges to 1.
This theorem contains no Collatz-specific arithmetic.
-/
theorem allConvergeOfLowerWitness
    (f : Nat → Nat)
    (lower : ∀ n : Nat, 1 < n → LowerWitness f n) :
    ∀ n : Nat, 0 < n → Converges f n := by
  intro n
  refine Nat.strongRecOn n ?_
  intro n ih hn
  cases n with
  | zero =>
      exact False.elim (Nat.lt_irrefl 0 hn)
  | succ k =>
      cases k with
      | zero =>
          exact Reach.refl 1
      | succ m =>
          have hgt : 1 < Nat.succ (Nat.succ m) := by
            exact Nat.succ_lt_succ (Nat.zero_lt_succ m)
          let w := lower (Nat.succ (Nat.succ m)) hgt
          cases w.kind with
          | inl hdir =>
              have hyConv : Converges f w.y :=
                ih w.y hdir.2 hdir.1
              exact Reach.trans w.reach hyConv
          | inr hcone =>
              cases hcone with
              | intro p hp =>
                  have hpPos : 0 < p := hp.1
                  have hpLt : p < Nat.succ (Nat.succ m) := hp.2.1
                  have hfp : f p = w.y := hp.2.2.1
                  have hOne : p = 1 → f w.y = 1 := hp.2.2.2
                  by_cases hp1 : p = 1
                  · have hy1 : f w.y = 1 := hOne hp1
                    have hyConv : Converges f w.y :=
                      Reach.step hy1 (Reach.refl 1)
                    exact Reach.trans w.reach hyConv
                  · have hpConv : Converges f p := ih p hpLt hpPos
                    have htail : Reach f (f p) 1 :=
                      Reach.tailOfNe hpConv hp1
                    rw [hfp] at htail
                    exact Reach.trans w.reach htail

/--
A convenient Collatz-shaped corollary interface: if a proposed cone theorem
constructs LowerWitness values, the global convergence conclusion follows.
-/
theorem convergenceFromConeCompiler
    (f : Nat → Nat)
    (coneCompiler : ∀ n : Nat, 1 < n → LowerWitness f n) :
    ∀ n : Nat, 0 < n → Reach f n 1 :=
  allConvergeOfLowerWitness f coneCompiler
