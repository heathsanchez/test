import Collatz.Certificate

namespace CollatzFinal

/-- RED fixture: this self-loop cannot admit a strictly decreasing rank. -/
def crystalBadModel : FiniteResidualModel 1 where
  residual := fun _ => true
  next := fun _ _ => true
  rank := fun _ => 0

example : FiniteResidualModel.RankValid crystalBadModel := by
  decide

end CollatzFinal
