import Collatz.Certificate

namespace CollatzFinal

/-- Finite acyclic Crystal residual fixture: 2 -> 1 -> 0, with 0 an exit. -/
def crystalFiniteModel : FiniteResidualModel 3 where
  residual := fun s => s.val != 0
  next := fun s t =>
    (s.val == 2 && t.val == 1) || (s.val == 1 && t.val == 0)
  rank := fun s => s.val

theorem crystalFiniteRankValid :
    FiniteResidualModel.RankValid crystalFiniteModel := by
  intro s t hs hnext
  fin_cases s <;> fin_cases t <;>
    simp [FiniteResidualModel.ResidualP, FiniteResidualModel.NextP,
      crystalFiniteModel] at hs hnext ⊢

theorem crystalFiniteKernelEmpty :
    KernelEmpty
      (FiniteResidualModel.ResidualP crystalFiniteModel)
      (FiniteResidualModel.NextP crystalFiniteModel) := by
  exact FiniteResidualModel.kernelEmpty crystalFiniteModel crystalFiniteRankValid

end CollatzFinal
