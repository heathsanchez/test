import Collatz.SourceCylinderExit

namespace CollatzFinal.SourceProduct

def familySource (r h u : Nat) : Nat :=
  38911100780481085467 + 3782158995862761504768 * (r + 2 ^ h * u)

theorem familySource_even_parameter {r h u : Nat} (hp : u % 2 = 0) :
    familySource r h u = familySource r (h + 1) (u / 2) := by
  unfold familySource
  rw [split_mul (2 ^ h) u]
  simp [hp, Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]

theorem familySource_odd_parameter {r h u : Nat} (hp : u % 2 = 1) :
    familySource r h u = familySource (r + 2 ^ h) (h + 1) (u / 2) := by
  unfold familySource
  rw [split_mul (2 ^ h) u]
  simp [hp, Nat.pow_succ, Nat.add_assoc,
    Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]

/-- Every closed leaf carries an actual universally available source exit.
Unresolved leaves remain explicit; splitting is a universal parameter partition. -/
inductive CertifiedParameterCover : Nat → Nat → Type where
  | unresolved {r h : Nat} : CertifiedParameterCover r h
  | closed {r h : Nat} (k : Nat)
      (proof : ∀ u, OrdinaryExit (familySource r h u)
        (iter shortcut k (familySource r h u))) : CertifiedParameterCover r h
  | split {r h : Nat}
      (left : CertifiedParameterCover r (h + 1))
      (right : CertifiedParameterCover (r + 2 ^ h) (h + 1)) :
      CertifiedParameterCover r h

def parameterCoverResidual {r h : Nat}
    (tree : CertifiedParameterCover r h) (u : Nat) : Bool :=
  match tree with
  | .unresolved => true
  | .closed _ _ => false
  | .split left right =>
      if u % 2 = 0 then parameterCoverResidual left (u / 2)
      else parameterCoverResidual right (u / 2)

/-- Exact backwards bridge from compiled closed leaves to actual exits.
There is no claim that the unresolved leaves are empty. -/
theorem ordinary_exit_of_certified_parameter_cover
    {r h : Nat} (tree : CertifiedParameterCover r h) (u : Nat)
    (hclosed : parameterCoverResidual tree u = false) :
    ∃ k, OrdinaryExit (familySource r h u)
      (iter shortcut k (familySource r h u)) := by
  induction tree generalizing u with
  | unresolved => simp [parameterCoverResidual] at hclosed
  | closed k proof => exact ⟨k, proof u⟩
  | @split r h left right ihLeft ihRight =>
      by_cases hp : u % 2 = 0
      · have hc : parameterCoverResidual left (u / 2) = false := by
          simpa [parameterCoverResidual, hp] using hclosed
        obtain ⟨k, hk⟩ := ihLeft (u / 2) hc
        refine ⟨k, ?_⟩
        rw [familySource_even_parameter hp]
        exact hk
      · have hp1 : u % 2 = 1 := by omega
        have hc : parameterCoverResidual right (u / 2) = false := by
          simpa [parameterCoverResidual, hp] using hclosed
        obtain ⟨k, hk⟩ := ihRight (u / 2) hc
        refine ⟨k, ?_⟩
        rw [familySource_odd_parameter hp1]
        exact hk

def parameterCoverResidualLeaves {r h : Nat}
    (tree : CertifiedParameterCover r h) : Nat :=
  match tree with
  | .unresolved => 1
  | .closed _ _ => 0
  | .split left right => parameterCoverResidualLeaves left + parameterCoverResidualLeaves right

def parameterCoverClosedLeaves {r h : Nat}
    (tree : CertifiedParameterCover r h) : Nat :=
  match tree with
  | .unresolved => 0
  | .closed _ _ => 1
  | .split left right => parameterCoverClosedLeaves left + parameterCoverClosedLeaves right

def parameterCoverClosedSlots {r h : Nat}
    (tree : CertifiedParameterCover r h) (depth : Nat) : Nat :=
  match tree with
  | .unresolved => 0
  | .closed _ _ => 2 ^ (depth - h)
  | .split left right => parameterCoverClosedSlots left depth + parameterCoverClosedSlots right depth

#print axioms familySource_even_parameter
#print axioms familySource_odd_parameter
#print axioms ordinary_exit_of_certified_parameter_cover

end CollatzFinal.SourceProduct
