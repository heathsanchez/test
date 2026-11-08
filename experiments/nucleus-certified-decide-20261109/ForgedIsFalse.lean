import NucleusDecide

-- Deliberate negative: a refutation cannot be an isTrue proof.
-- Lean must refuse this file.
example : @decide False (Decidable.isFalse (fun h => h)) = true := by
  rfl
