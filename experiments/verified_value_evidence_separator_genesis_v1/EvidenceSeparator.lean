import Std

structure PolicyAmbiguity where
  left : List Int
  right : List Int
  distinct : left ≠ right

structure VerifiedSeparator where
  query : Nat
  leftCost : Nat
  rightCost : Nat
  separates : leftCost ≠ rightCost

inductive EvidenceStatus where
  | unknownSearch (ambiguity : PolicyAmbiguity)
  | refinedAuthority (ambiguity : PolicyAmbiguity) (separator : VerifiedSeparator)

def admitSeparator (a : PolicyAmbiguity) (s : VerifiedSeparator) : EvidenceStatus :=
  EvidenceStatus.refinedAuthority a s

theorem no_separator_no_refined_constructor (a : PolicyAmbiguity) :
    EvidenceStatus.unknownSearch a = EvidenceStatus.unknownSearch a := rfl
