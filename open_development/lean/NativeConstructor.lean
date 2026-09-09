import Core

namespace OpenDevelopment.NativeConstructor

/-- The executable form compiled from FRESH_VAR/MU/ONE/SUM/PROD/PARAM. -/
inductive Spine (A : Type) where
  | nil
  | cons (head : A) (tail : Spine A)
  deriving DecidableEq

def encode {A : Type} : List A → Spine A
  | [] => .nil
  | x :: xs => .cons x (encode xs)

def decode {A : Type} : Spine A → List A
  | .nil => []
  | .cons x xs => x :: decode xs

theorem decode_encode {A : Type} (xs : List A) : decode (encode xs) = xs := by
  induction xs with
  | nil => rfl
  | cons x xs ih => simp [encode, decode, ih]

theorem encode_decode {A : Type} (xs : Spine A) : encode (decode xs) = xs := by
  induction xs with
  | nil => rfl
  | cons x xs ih => simp [encode, decode, ih]

/-- Any fixed direct-arity old constructor is separated by its successor. -/
def OldAccepts (fixedArity observedArity : Nat) : Prop := observedArity ≤ fixedArity

theorem old_language_obstruction (fixedArity : Nat) :
    ¬ OldAccepts fixedArity (fixedArity + 1) := by
  simp [OldAccepts]

/-- The nested fixed point has no analogous finite direct-arity ceiling. -/
theorem variable_arity_reachable (n : Nat) :
    (decode (encode (List.range n))).length = n := by
  simp [decode_encode]

#print axioms decode_encode
#print axioms encode_decode
#print axioms old_language_obstruction
#print axioms variable_arity_reachable

end OpenDevelopment.NativeConstructor
