import Collatz.Certificate

namespace CollatzFinal

/-- Finite acyclic Crystal residual fixture: residual states 1 and 2, edge 2 -> 1. -/
def crystalFiniteModel : FiniteResidualModel 3 where
  residual := fun s => s.val != 0
  next := fun s t => s.val == 2 && t.val == 1
  rank := fun s => s.val

theorem crystalFiniteRankValid :
    FiniteResidualModel.RankValid crystalFiniteModel := by
  intro s t hs hnext
  simp [FiniteResidualModel.NextP, crystalFiniteModel] at hnext
  rcases hnext with ⟨hs2, ht1⟩
  simp [crystalFiniteModel, hs2, ht1]

theorem crystalFiniteKernelEmpty :
    KernelEmpty
      (FiniteResidualModel.ResidualP crystalFiniteModel)
      (FiniteResidualModel.NextP crystalFiniteModel) := by
  exact FiniteResidualModel.kernelEmpty crystalFiniteModel crystalFiniteRankValid

end CollatzFinal
