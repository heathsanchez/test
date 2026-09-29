import Collatz.Certificate

namespace CollatzFinal

/-- Exact 12-node intrinsic Q2×Q3 diagnostic model reproduced from
collatz-biadic-cell-rank-diagnostic-v0, run 36098310952.

Node order follows the emitted cell rows:
0 [11,99,0,0]
1 [16,59157,4,79]
2 [3,1,2,1]
3 [3,1,2,6]
4 [3,1,4,43]
5 [3,1,9,15852]
6 [4,15,4,80]
7 [4,7,3,1]
8 [7,11,3,7]
9 [7,15,2,1]
10 [7,45,0,0]
11 [9,253,2,6]

The only residual chain is 3→1→5→4→2→7. -/
def biadicDiagnosticResidual (_ : Fin 12) : Bool := true

def biadicDiagnosticNext (s t : Fin 12) : Bool :=
  decide (
    (s = 3 ∧ t = 1) ∨
    (s = 1 ∧ t = 5) ∨
    (s = 5 ∧ t = 4) ∨
    (s = 4 ∧ t = 2) ∨
    (s = 2 ∧ t = 7))

def biadicDiagnosticRank (s : Fin 12) : Nat :=
  if s = 3 then 5 else
  if s = 1 then 4 else
  if s = 5 then 3 else
  if s = 4 then 2 else
  if s = 2 then 1 else
  0

def biadicDiagnosticModel : FiniteResidualModel 12 where
  residual := biadicDiagnosticResidual
  next := biadicDiagnosticNext
  rank := biadicDiagnosticRank

theorem biadicDiagnosticRankValid :
    FiniteResidualModel.RankValid biadicDiagnosticModel := by
  decide

theorem biadicDiagnosticKernelEmpty :
    KernelEmpty
      (FiniteResidualModel.ResidualP biadicDiagnosticModel)
      (FiniteResidualModel.NextP biadicDiagnosticModel) := by
  exact FiniteResidualModel.kernelEmpty
    biadicDiagnosticModel biadicDiagnosticRankValid

#print axioms biadicDiagnosticRankValid
#print axioms biadicDiagnosticKernelEmpty

end CollatzFinal
