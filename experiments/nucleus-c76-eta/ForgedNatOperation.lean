import C81NatCache

-- Deliberately wrong transfer: the same numeral arguments under a
-- different registered arithmetic primitive do NOT preserve the value.
example : C81NatCache.evaluate .mul 0 1 =
          C81NatCache.evaluate .add 0 1 := by
  rfl
