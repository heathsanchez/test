import C83Fin7

-- Deliberately forged finite-equality outcome for two distinct Fin values.
example : decide ((0 : Fin 7) = (1 : Fin 7)) = true := by
  rfl
