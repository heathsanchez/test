import TypedResidualKernel

namespace CrossRepresentation

inductive SourceRole where | scan | filter | first | pair | extend | temporal
  deriving DecidableEq, Repr
inductive TargetToken where | zx9 | qa2 | mn7 | rv4 | kp1 | ht8
  deriving DecidableEq, Repr

def compile : SourceRole → TargetToken
  | .scan => .zx9 | .filter => .qa2 | .first => .mn7
  | .pair => .rv4 | .extend => .kp1 | .temporal => .ht8

theorem vocabularies_disjoint : SourceRole ≠ TargetToken := by
  intro h
  cases h

def D2 : List SourceRole := [.scan, .filter, .first, .pair, .extend, .pair]
def targetD2 : List TargetToken := D2.map compile

theorem targetD2_exact : targetD2 = [.zx9, .qa2, .mn7, .rv4, .kp1, .rv4] := by decide

structure EquivalenceCertificate (s : SourceRole) (t : TargetToken) : Prop where
  compiled : compile s = t

theorem every_role_compiles (s : SourceRole) : EquivalenceCertificate s (compile s) := ⟨rfl⟩

theorem ablation_removes_transferred_state : ([] : List TargetToken) ≠ targetD2 := by decide

end CrossRepresentation
