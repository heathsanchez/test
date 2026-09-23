/-
Lean 4.29.1 reference obligations for G1-001. This file is checked with the
exact toolchain pinned by lean-kernel-arena at f5e1bce6.
-/

universe u v

example : Sort (max u v) = Sort (max v u) := rfl

example : Sort (max u u) = Sort u := rfl

example : Sort (imax u (v + 1)) = Sort (max u (v + 1)) := rfl

-- This concrete branch witnesses why imax u v cannot be replaced by max u v
-- without proving that v is nonzero.
example : Sort (imax 1 0) = Sort 0 := rfl
