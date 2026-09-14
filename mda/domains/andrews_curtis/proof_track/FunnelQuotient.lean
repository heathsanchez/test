import FunnelCore

/-!
# The funnel / conjugacy-difference quotient calculus

The mined funnel law is most naturally packaged as a derived move relation.
A derived twist inserts or removes

  R_j⁻¹ * w * R_j * w⁻¹

on the left of a distinct relator R_i.

Both directions are finite ordinary Andrews--Curtis paths by
`commutatorTwist_contract` and symmetry of `AC.Reachable`.

This gives a small quotient calculus that can safely be used by search:
identifying states along this relation cannot change any ordinary-AC
reachability consequence.
-/

namespace AC

/-- A derived conjugacy-difference twist, in either direction. -/
inductive TwistStep {n : ℕ} : Relators n → Relators n → Prop
  | insert (R : Relators n) (i j : Fin n) (hij : i ≠ j) (w : Word n) :
      TwistStep R
        (Function.update R i ((R j)⁻¹ * w * R j * w⁻¹ * R i))
  | remove (R : Relators n) (i j : Fin n) (hij : i ≠ j) (w : Word n) :
      TwistStep
        (Function.update R i ((R j)⁻¹ * w * R j * w⁻¹ * R i))
        R

/-- Reflexive-transitive closure of the derived twist calculus. -/
def TwistReachable {n : ℕ} : Relators n → Relators n → Prop :=
  Relation.ReflTransGen (@TwistStep n)

/-- Every derived twist step expands to a finite ordinary AC path. -/
theorem twistStep_reachable {n : ℕ} {R S : Relators n}
    (h : TwistStep R S) : Reachable R S := by
  cases h with
  | insert R i j hij w =>
      exact reachable_symm (commutatorTwist_contract R i j hij w)
  | remove R i j hij w =>
      exact commutatorTwist_contract R i j hij w

/-- Every finite path in the twist calculus expands to an ordinary AC path. -/
theorem twistReachable_reachable {n : ℕ} {R S : Relators n}
    (h : TwistReachable R S) : Reachable R S := by
  induction h with
  | refl =>
      exact Relation.ReflTransGen.refl
  | tail hprefix hstep ih =>
      exact ih.trans (twistStep_reachable hstep)

/-- The derived primitive relation is symmetric. -/
theorem twistStep_symm {n : ℕ} {R S : Relators n}
    (h : TwistStep R S) : TwistStep S R := by
  cases h with
  | insert R i j hij w =>
      exact TwistStep.remove R i j hij w
  | remove R i j hij w =>
      exact TwistStep.insert R i j hij w

/-- Hence finite twist reachability is symmetric. -/
theorem twistReachable_symm {n : ℕ} {R S : Relators n}
    (h : TwistReachable R S) : TwistReachable S R := by
  induction h with
  | refl =>
      exact Relation.ReflTransGen.refl
  | tail hprefix hstep ih =>
      exact (Relation.ReflTransGen.single (twistStep_symm hstep)).trans ih

/-- Twist-equivalent states have exactly the same reachability consequences
for every target presentation. -/
theorem twistReachable_target_iff {n : ℕ} {R S T : Relators n}
    (h : TwistReachable R S) :
    Reachable R T ↔ Reachable S T := by
  exact reachable_target_iff_of_reachable (twistReachable_reachable h)

/-- In particular, quotienting by finite derived twists preserves the ordinary
Andrews--Curtis target question. -/
theorem twistReachable_standard_iff {n : ℕ} {R S : Relators n}
    (h : TwistReachable R S) :
    Reachable R (standard n) ↔ Reachable S (standard n) :=
  twistReachable_target_iff h

end AC
