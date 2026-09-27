import Collatz.Certificate

namespace CollatzFinal

def crystalBadModel : FiniteResidualModel 1 where
  residual := fun _ => true
  next := fun _ _ => true
  rank := fun _ => 0

example : FiniteResidualModel.RankValid crystalBadModel := by
  intro s t hs hnext
  simp [FiniteResidualModel.ResidualP, FiniteResidualModel.NextP, crystalBadModel] at hs hnext ⊢

end CollatzFinal
