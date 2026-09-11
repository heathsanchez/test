structure Geometry where
  dependencyDepth : Nat
  persistence : Nat
  reuseRadius : Nat
  causalBreadth : Nat
  amortizedValue : Int

def moveDepth (g : Geometry) (n : Nat) : Geometry := { g with dependencyDepth := n }
def moveRadius (g : Geometry) (n : Nat) : Geometry := { g with reuseRadius := n }

theorem depthInterventionPreservesRadius (g : Geometry) (n : Nat) :
    (moveDepth g n).reuseRadius = g.reuseRadius := rfl

theorem radiusInterventionPreservesDepth (g : Geometry) (n : Nat) :
    (moveRadius g n).dependencyDepth = g.dependencyDepth := rfl
