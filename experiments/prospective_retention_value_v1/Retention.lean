structure Candidate where
  warranted : Prop
  proof : warranted
  estimatedValue : Int

structure Retention (budget : Nat) where
  kept : List Candidate
  withinBudget : kept.length ≤ budget

theorem retainedIsWarranted {b : Nat} (r : Retention b) (c : Candidate)
    (h : c ∈ r.kept) : c.warranted := c.proof

theorem scarcityBound {b : Nat} (r : Retention b) : r.kept.length ≤ b := r.withinBudget
