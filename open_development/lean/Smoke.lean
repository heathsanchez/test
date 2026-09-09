import Core

open OpenDevelopment

def natIdentityRealization : Realization Nat Nat Nat Nat Nat Nat Nat where
  encodeProgram := id
  encodeInput := id
  runDomain := fun p x => p + x
  runIR := fun p x => p + x
  observeDomain := id
  observeIR := id
  preserves := by intro p x; rfl

example (p x : Nat) :
    natIdentityRealization.observeIR
        (natIdentityRealization.runIR
          (natIdentityRealization.encodeProgram p)
          (natIdentityRealization.encodeInput x)) =
      natIdentityRealization.observeDomain
        (natIdentityRealization.runDomain p x) := by
  exact realization_commutes natIdentityRealization p x

-- A concrete finite realization, not a claim about arbitrary external worlds.
def observation (x c : Fin 4) : Nat := (x.val + c.val) % 2

def initial : State (Fin 4) := {}

def after : State (Fin 4) := apply initial (.observe 0)

-- Reduce the singleton observation obligation before checking concrete values.
-- The abstract Interface has no blanket Decidable instance.
example : Interface observation after (0 : Fin 4) 2 := by
  simp [Interface, after, initial, apply, EquivalentOn, observation]

example : ¬ Interface observation after (0 : Fin 4) 1 := by
  intro h
  have h01 := h (0 : Fin 4) (by simp [after, initial, apply])
  simp [observation] at h01

example (x y : Fin 4) :
    Interface observation after x y ↔
      observation x 0 = observation y 0 := by
  simpa [after, initial, Interface, apply, EquivalentOn] using
    (observe_meet observation initial (0 : Fin 4) x y)

-- The authority can check a concrete repair without being the source of truth.
def finiteAuthority : Authority (Fin 4) where
  valid := fun _ => True
  check := fun _ => true
  sound := by intros; trivial

example : develop finiteAuthority initial (.observe 0) = some after := by decide
