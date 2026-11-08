import Init

/-!
C81 proof boundary for source-owned arithmetic-result sharing.

Conditional: this formalises *why* independently established numeral
arguments and a checked source operation determine one reusable result.
It DOES NOT prove Rust BigNat implementation/refinement, source-primitive
registry integrity, actual cache key authentication or n7 ACCEPT.
-/

namespace C81NatCache

inductive NatOperation where
  | mul
  | add
  | mod
deriving DecidableEq

def evaluate : NatOperation → Nat → Nat → Nat
  | .mul, a, b => a * b
  | .add, a, b => a + b
  | .mod, a, b => a % b

structure CompleteValue where
  sourceOwner : Nat
  op : NatOperation
  lhs : Nat
  rhs : Nat
  result : Nat
  completed : evaluate op lhs rhs = result

theorem reuse_only_under_exact_operands
    (receipt : CompleteValue) (source : Nat) (op : NatOperation)
    (lhs rhs : Nat)
    (_sameOwner : source = receipt.sourceOwner)
    (sameOperation : op = receipt.op)
    (sameLeft : lhs = receipt.lhs)
    (sameRight : rhs = receipt.rhs) :
    evaluate op lhs rhs = receipt.result := by
  cases sameOperation
  cases sameLeft
  cases sameRight
  exact receipt.completed

-- If a source primitive's operation mapping changes, an identical pair of
-- concrete numerals cannot license transferring the cached result.
theorem operation_identity_matters :
    evaluate .mul 0 1 ≠ evaluate .add 0 1 := by
  decide

-- A different proved numeral is not safely identified by an unrelated
-- expression's source shape or by the cache key's previous left value.
theorem numeric_operand_identity_matters :
    evaluate .add 0 1 ≠ evaluate .add 1 1 := by
  decide

-- This is a proper *completed* source computation certificate. The two
-- numerals are identical in the new closure because they are established
-- values, not because their original binder allocation IDs coincide.
theorem exact_native_mul_replay (a b : Nat)
    (receipt : CompleteValue)
    (hop : receipt.op = .mul)
    (ha : receipt.lhs = a) (hb : receipt.rhs = b)
    (hr : receipt.result = a * b) :
    evaluate .mul a b = receipt.result := by
  cases hop
  cases ha
  cases hb
  exact receipt.completed

#print axioms C81NatCache.reuse_only_under_exact_operands
#print axioms C81NatCache.operation_identity_matters
#print axioms C81NatCache.numeric_operand_identity_matters
#print axioms C81NatCache.exact_native_mul_replay
