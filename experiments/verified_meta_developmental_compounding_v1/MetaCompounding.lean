import TypedResidualKernel

namespace VerifiedMetaDevelopmentalCompounding
open TypedResidualKernel

inductive Capability where | d1 | d2 | temporal deriving DecidableEq
def omega0 : List Capability := []
def omega1 : List Capability := [.d1]
def omega2 : List Capability := [.d1, .d2]
def residual1 : Nat := 1
def residual2 : Nat := 2

theorem retained_d1 (h : Capability.d1 ∈ omega1) : Capability.d1 ∈ omega2 := by
  simpa [omega1, omega2] using h
theorem d1_not_d2 : Capability.d2 ∉ omega1 := by decide
theorem d2_accumulated : Capability.d1 ∈ omega2 ∧ Capability.d2 ∈ omega2 := by decide
theorem ablate_d2_restores_omega1 : omega2.erase Capability.d2 = omega1 := by decide

def K : Kernel where
  State := List Capability; Language := List Capability
  Authority := Unit; Policy := Unit; Residual := Nat; Candidate := Capability
  Future := Capability; Fact := Capability
  selectionObligation := fun _ _ _ _ _ => True
  uniqueIfRequired := fun _ _ => True
  identityResidual := fun _ _ _ _ => True
  choiceResidual := fun _ _ _ _ _ => True
  searchIncomplete := fun _ _ _ => True
  complete := fun _ _ _ => True
  inLanguage := fun M c => c ∈ M
  resolves := fun c r => (c = .d1 ∧ r = residual1) ∨ (c = .d2 ∧ r = residual2)
  isProtected := fun Ω c => c ∈ Ω

def r1 : Result K omega0 omega0 () () residual1 :=
  Result.unknownExpressivity trivial (by simp [NoCurrentResolution, K, omega0])
def step1 : Step K r1 omega1 := Step.proposeGenerator (by simp [K, omega0, omega1])

theorem step1_preserves : ∀ c, K.isProtected omega0 c → K.isProtected omega1 c :=
  step_preserves K step1

end VerifiedMetaDevelopmentalCompounding
