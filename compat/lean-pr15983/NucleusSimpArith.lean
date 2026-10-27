import Lean

/-!
Source-pinned Nucleus differential for Lean PR #15983.
Copied theorem statement and tactic from leanprover/lean4:
commit 33c050d0430abeb345e27a4e3f6a261e97e15a16
tests/elab/simp_int_arith.lean (blob 1b59a7cab8758c47d66956c98bc3142a5d2ebabc)
Only named ex₁ is exported; this file's comment is not an authority.
-/
theorem ex₁ (x y z : Int) :
    x + y + 2 + y + z + z ≤ y + 3*z + 1 + 1 + x + y - z := by
  simp +arith only

open Int.Internal.Linear in
#print ex₁
