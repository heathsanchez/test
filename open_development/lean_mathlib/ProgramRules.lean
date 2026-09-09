import Mathlib
import ProcedureRules

namespace OpenDevelopment.ProgramRules

inductive Domain where
  | ray
  | interval (l u : ℝ)

inductive Program where
  | constant (c : ℝ)
  | monomial (c : ℝ) (k : ℕ)
  | square (a b : ℝ)
  | affine (a b : ℝ)
  | sum (p q : Program)
  | product (p q : Program)

def InDomain : Domain → ℝ → Prop
  | .ray, x => 0 ≤ x
  | .interval l u, x => l ≤ x ∧ x ≤ u

def NonnegativeDomain : Domain → Prop
  | .ray => True
  | .interval l u => 0 ≤ l ∧ l ≤ u

def Valid (d : Domain) : Program → Prop
  | .constant c => 0 ≤ c
  | .monomial c _ => 0 ≤ c ∧ NonnegativeDomain d
  | .square _ _ => True
  | .affine a b => match d with
      | .ray => False
      | .interval l u => l ≤ u ∧ 0 ≤ a * l + b ∧ 0 ≤ a * u + b
  | .sum p q => Valid d p ∧ Valid d q
  | .product p q => Valid d p ∧ Valid d q

def eval : Program → ℝ → ℝ
  | .constant c, _ => c
  | .monomial c k, x => c * x ^ k
  | .square a b, x => (a * x + b) ^ 2
  | .affine a b, x => a * x + b
  | .sum p q, x => eval p x + eval q x
  | .product p q, x => eval p x * eval q x

theorem domain_nonneg (d : Domain) {x : ℝ}
    (hd : NonnegativeDomain d) (hx : InDomain d x) : 0 ≤ x := by
  cases d with
  | ray => exact hx
  | interval l u => exact le_trans hd.1 hx.1

theorem sound : ∀ (p : Program) (d : Domain) (x : ℝ),
    Valid d p → InDomain d x → 0 ≤ eval p x := by
  intro p
  induction p with
  | constant c => intro d x h hx; exact h
  | monomial c k =>
      intro d x h hx
      exact mul_nonneg h.1 (pow_nonneg (domain_nonneg d h.2 hx) _)
  | square a b => intro d x h hx; exact sq_nonneg _
  | affine a b =>
      intro d x h hx
      cases d with
      | ray => exact False.elim h
      | interval l u =>
          exact ProcedureRules.intervalAffine_sound a b l u h.2.1 h.2.2 hx
  | sum p q ihp ihq =>
      intro d x h hx
      exact add_nonneg (ihp d x h.1 hx) (ihq d x h.2 hx)
  | product p q ihp ihq =>
      intro d x h hx
      exact mul_nonneg (ihp d x h.1 hx) (ihq d x h.2 hx)

#print axioms sound
end OpenDevelopment.ProgramRules
