import Kernel
import Completeness

namespace OpenDevelopment

universe u v w

/-- A typed domain-to-IR realization. Encoding alone is insufficient: the
observation square is an explicit proof obligation. -/
structure Realization
    (DProgram : Type u) (DInput : Type v) (DResult : Type w)
    (IProgram : Type u) (IInput : Type v) (IResult : Type w)
    (Observation : Type w) where
  encodeProgram : DProgram → IProgram
  encodeInput : DInput → IInput
  runDomain : DProgram → DInput → DResult
  runIR : IProgram → IInput → IResult
  observeDomain : DResult → Observation
  observeIR : IResult → Observation
  preserves : ∀ p x,
    observeIR (runIR (encodeProgram p) (encodeInput x)) =
      observeDomain (runDomain p x)

theorem realization_commutes
    {DProgram : Type u} {DInput : Type v} {DResult : Type w}
    {IProgram : Type u} {IInput : Type v} {IResult : Type w}
    {Observation : Type w}
    (r : Realization DProgram DInput DResult IProgram IInput IResult Observation)
    (p : DProgram) (x : DInput) :
    r.observeIR (r.runIR (r.encodeProgram p) (r.encodeInput x)) =
      r.observeDomain (r.runDomain p x) :=
  r.preserves p x

/-- The state distinguishes observations, executable means, and revisable policy. -/
structure State (C : Type u) where
  observations : List C := []
  capabilities : List C := []
  policy : Nat := 0
  deriving Repr, DecidableEq

/-- These are different changes; acquisition does not silently refine identity. -/
inductive Repair (C : Type u) where
  | observe : C → Repair C
  | acquire : C → Repair C
  | revisePolicy : Nat → Repair C
  deriving Repr, DecidableEq

/-- Pure, total compilation. Authority is supplied separately. -/
def apply {C : Type u} (s : State C) : Repair C → State C
  | .observe c => { s with observations := c :: s.observations }
  | .acquire c => { s with capabilities := c :: s.capabilities }
  | .revisePolicy p => { s with policy := p }

/-- A certificate is a proof of a declared, domain-specific contract. -/
structure CheckedRepair (C : Type u) (Valid : Repair C → Prop) where
  repair : Repair C
  certificate : Valid repair

/-- The same transition accepts object- and policy-level repairs. -/
def applyChecked {C : Type u} {Valid : Repair C → Prop}
    (s : State C) (r : CheckedRepair C Valid) : State C :=
  apply s r.repair

/-- Executable checker with an explicit soundness obligation. -/
structure Authority (C : Type u) where
  valid : Repair C → Prop
  check : Repair C → Bool
  sound : ∀ r, check r = true → valid r

def develop {C : Type u} (a : Authority C) (s : State C)
    (r : Repair C) : Option (State C) :=
  if a.check r then some (apply s r) else none

theorem develop_sound {C : Type u} (a : Authority C) (s : State C)
    (r : Repair C) (s' : State C)
    (h : develop a s r = some s') :
    a.valid r ∧ s' = apply s r := by
  by_cases hcheck : a.check r = true
  · have heq : apply s r = s' := by simpa [develop, hcheck] using h
    exact ⟨a.sound r hcheck, heq.symm⟩
  · simp [develop, hcheck] at h

/-- The concrete interface is the existing MSI observational equivalence. -/
def Interface {X : Type u} {C : Type v} {O : Type w}
    (P : X → C → O) (s : State C) (x y : X) : Prop :=
  EquivalentOn P s.observations x y

/-- A retained observation is exactly a meet with its observational kernel. -/
theorem observe_meet {X : Type u} {C : Type v} {O : Type w}
    (P : X → C → O) (s : State C) (c : C) (x y : X) :
    Interface P (apply s (.observe c)) x y ↔
      P x c = P y c ∧ Interface P s x y := by
  exact EquivalentOn.cons P c s.observations x y

/-- Acquisition changes available means, not the current observational quotient. -/
theorem acquire_preserves_interface {X : Type u} {C : Type v} {O : Type w}
    (P : X → C → O) (s : State C) (c : C) (x y : X) :
    Interface P (apply s (.acquire c)) x y ↔ Interface P s x y := by
  rfl

/-- Policy revision is a typed change, not a representation repair. -/
theorem policy_preserves_interface {X : Type u} {C : Type v} {O : Type w}
    (P : X → C → O) (s : State C) (p : Nat) (x y : X) :
    Interface P (apply s (.revisePolicy p)) x y ↔ Interface P s x y := by
  rfl

end OpenDevelopment
