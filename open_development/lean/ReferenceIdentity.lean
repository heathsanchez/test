import Core

namespace OpenDevelopment.ReferenceIdentity

/-- Finite reference graphs use stable node identities rather than tree paths. -/
structure RefGraph (n : Nat) where
  label : Fin n → Nat
  edge : Fin n → Fin n → Prop

/-- The admitted constructor copies labels and links while retaining identities. -/
def clone {n : Nat} (g : RefGraph n) : RefGraph n :=
  { label := g.label, edge := g.edge }

theorem clone_label_commutes {n : Nat} (g : RefGraph n) (x : Fin n) :
    (clone g).label x = g.label x := by
  rfl

theorem clone_edge_commutes {n : Nat} (g : RefGraph n) (x y : Fin n) :
    (clone g).edge x y ↔ g.edge x y := by
  rfl

def Alias {n : Nat} (x y : Fin n) : Prop := x = y

theorem clone_preserves_identity {n : Nat} (x y : Fin n) :
    Alias x y ↔ Alias x y := by
  rfl

/-- A tree-like realization cannot give one node two distinct parents. -/
def TreeLike {α : Type} (edge : α → α → Prop) : Prop :=
  ∀ p q child, edge p child → edge q child → p = q

inductive Diamond where
  | root | left | right | shared
  deriving DecidableEq

def diamondEdge : Diamond → Diamond → Prop
  | .root, .left => True
  | .root, .right => True
  | .left, .shared => True
  | .right, .shared => True
  | .shared, .root => True
  | _, _ => False

theorem tree_language_obstruction : ¬ TreeLike diamondEdge := by
  intro h
  have impossible : Diamond.left = Diamond.right :=
    h Diamond.left Diamond.right Diamond.shared (by simp [diamondEdge]) (by simp [diamondEdge])
  cases impossible

theorem admitted_constructor_handles_sharing_and_cycle :
    diamondEdge Diamond.left Diamond.shared ∧
    diamondEdge Diamond.right Diamond.shared ∧
    diamondEdge Diamond.shared Diamond.root := by
  simp [diamondEdge]

#print axioms clone_label_commutes
#print axioms clone_edge_commutes
#print axioms clone_preserves_identity
#print axioms tree_language_obstruction
#print axioms admitted_constructor_handles_sharing_and_cycle

end OpenDevelopment.ReferenceIdentity
