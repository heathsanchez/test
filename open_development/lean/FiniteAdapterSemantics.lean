import Core

namespace OpenDevelopment.FiniteAdapterSemantics

/-- The worlds and probes in `examples/finite.json`. -/
inductive World where | zero | one | two
  deriving DecidableEq

inductive Probe where | constant | split | identity
  deriving DecidableEq

def runDomain : Probe → World → Nat
  | .constant, _ => 0
  | .split, .zero => 0
  | .split, .one => 1
  | .split, .two => 1
  | .identity, .zero => 0
  | .identity, .one => 1
  | .identity, .two => 2

/-- The deliberately small shared executable IR used by this finite adapter. -/
structure IRProgram where code : Nat
structure IRInput where code : Nat

def encodeProbe : Probe → IRProgram
  | .constant => ⟨0⟩
  | .split => ⟨1⟩
  | .identity => ⟨2⟩

def encodeWorld : World → IRInput
  | .zero => ⟨0⟩
  | .one => ⟨1⟩
  | .two => ⟨2⟩

def runIR (p : IRProgram) (x : IRInput) : Nat :=
  match p.code, x.code with
  | 0, _ => 0
  | 1, 0 => 0
  | 1, _ => 1
  | 2, n => n
  | _, _ => 0

def realization : Realization Probe World Nat IRProgram IRInput Nat Nat where
  encodeProgram := encodeProbe
  encodeInput := encodeWorld
  runDomain := runDomain
  runIR := runIR
  observeDomain := id
  observeIR := id
  preserves := by
    intro p x
    cases p <;> cases x <;> rfl

theorem finite_adapter_commutes (p : Probe) (x : World) :
    realization.observeIR
        (realization.runIR (realization.encodeProgram p) (realization.encodeInput x)) =
      realization.observeDomain (realization.runDomain p x) := by
  exact realization_commutes realization p x

end OpenDevelopment.FiniteAdapterSemantics
