import Collatz.SourceProductAffine

namespace CollatzFinal
namespace SourceProduct

def CoefficientCrossingAt (n k : Nat) : Prop :=
  3 ^ oddCount n k < 2 ^ k

def FirstCoefficientCrossingAt (n k : Nat) : Prop :=
  CoefficientCrossingAt n k /\
    (forall i, i < k -> Not (CoefficientCrossingAt n i))

theorem first_coefficient_crossing_unique
    {n j k : Nat}
    (hj : FirstCoefficientCrossingAt n j)
    (hk : FirstCoefficientCrossingAt n k) :
    j = k := by
  apply Nat.le_antisymm
  · by_contra h
    have hlt : k < j := Nat.lt_of_not_ge h
    exact (hj.2 k hlt) hk.1
  · by_contra h
    have hlt : j < k := Nat.lt_of_not_ge h
    exact (hk.2 j hlt) hj.1

theorem no_later_first_coefficient_crossing_same_source
    {n j k : Nat}
    (hj : FirstCoefficientCrossingAt n j)
    (hjk : j < k) :
    Not (FirstCoefficientCrossingAt n k) := by
  intro hk
  have heq := first_coefficient_crossing_unique hj hk
  omega

#print axioms first_coefficient_crossing_unique
#print axioms no_later_first_coefficient_crossing_same_source

end SourceProduct
end CollatzFinal
