import NucleusDecide

-- The last point of Fin 3 violates k < 2.
-- The claimed all-true certificate must be rejected by Lean.
example :
    Nat.allLTTR 3 (fun k _ => decide (k < 2)) = true := by
  rfl
