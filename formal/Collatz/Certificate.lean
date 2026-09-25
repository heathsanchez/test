import Collatz.FinalKernel

namespace CollatzFinal

structure FiniteResidualModel (n : Nat) where
  residual : Fin n → Bool
  next : Fin n → Fin n → Bool
  rank : Fin n → Nat

namespace FiniteResidualModel

def ResidualP {n : Nat} (M : FiniteResidualModel n) (s : Fin n) : Prop :=
  M.residual s = true

def NextP {n : Nat} (M : FiniteResidualModel n) (s t : Fin n) : Prop :=
  M.next s t = true

def RankValid {n : Nat} (M : FiniteResidualModel n) : Prop :=
  ∀ s t, ResidualP M s → NextP M s t → M.rank t < M.rank s

theorem kernelEmpty
    {n : Nat}
    (M : FiniteResidualModel n)
    (h : RankValid M) :
    KernelEmpty (ResidualP M) (NextP M) := by
  exact kernel_empty_of_rank
    (ResidualP M) (NextP M) M.rank h

/--
A generated certificate may close the residual kernel by proving only the
finite rank condition. For concrete tables this proposition is decidable,
so a generated Lean witness can normally be discharged by decide.
-/
theorem closes_of_decidable_rank
    {n : Nat}
    (M : FiniteResidualModel n)
    (h : RankValid M) :
    KernelEmpty (ResidualP M) (NextP M) :=
  kernelEmpty M h

end FiniteResidualModel

/-- Tiny non-Collatz fixture proving the certificate interface itself. -/
def fixtureModel : FiniteResidualModel 1 where
  residual := fun _ => true
  next := fun _ _ => false
  rank := fun _ => 0

theorem fixtureRankValid :
    FiniteResidualModel.RankValid fixtureModel := by
  intro s t hs hnext
  simp [FiniteResidualModel.NextP, fixtureModel] at hnext

theorem fixtureKernelEmpty :
    KernelEmpty
      (FiniteResidualModel.ResidualP fixtureModel)
      (FiniteResidualModel.NextP fixtureModel) := by
  exact FiniteResidualModel.kernelEmpty fixtureModel fixtureRankValid

end CollatzFinal
