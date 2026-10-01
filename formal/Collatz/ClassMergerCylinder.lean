import Collatz.SourceCylinderExit
import Collatz.EarlierSourceCollision

namespace CollatzFinal.SourceProduct

/-- A verified coalescence at one affine base point lifts to the whole admitted
pair of dyadic cylinders.  The protected source remains the original source:
the lower cylinder is used only as the strictly earlier coalescing witness. -/
theorem earlier_source_collision_of_coalescent_cylinders
    {n k x q p b r sourceUnit lowerUnit : Nat}
    (hntrace : sourceOrbit n k = (x, q))
    (hptrace : sourceOrbit p b = (x, r))
    (hp : 0 < p)
    (hbelow : p < n)
    (hslope : 2 ^ b * lowerUnit ≤ 2 ^ k * sourceUnit)
    (hendpoint : 3 ^ r * lowerUnit = 3 ^ q * sourceUnit)
    (u : Nat) :
    EarlierSourceCollision
      (n + 2 ^ k * (sourceUnit * u))
      (iter shortcut k (n + 2 ^ k * (sourceUnit * u))) := by
  have hnPair := (sourceOrbit_correct n k).symm.trans hntrace
  have hnY : iter shortcut k n = x := congrArg Prod.fst hnPair
  have hnQ : oddCount n k = q := congrArg Prod.snd hnPair
  have hpPair := (sourceOrbit_correct p b).symm.trans hptrace
  have hpY : iter shortcut b p = x := congrArg Prod.fst hpPair
  have hpQ : oddCount p b = r := congrArg Prod.snd hpPair
  let lower := p + 2 ^ b * (lowerUnit * u)
  refine ⟨lower, b, ?_, ?_, ?_⟩
  · dsimp [lower]
    omega
  · have hmul := Nat.mul_le_mul_right u hslope
    dsimp [lower]
    simp only [Nat.mul_assoc] at hmul ⊢
    omega
  · have hs :
        iter shortcut k (n + 2 ^ k * (sourceUnit * u)) =
          x + 3 ^ q * (sourceUnit * u) := by
      rw [shortcut_iter_source_lift, hnY, hnQ]
    have hl :
        iter shortcut b lower =
          x + 3 ^ r * (lowerUnit * u) := by
      dsimp [lower]
      rw [shortcut_iter_source_lift, hpY, hpQ]
    rw [hl, hs]
    calc
      x + 3 ^ r * (lowerUnit * u)
          = x + (3 ^ r * lowerUnit) * u := by
              simp [Nat.mul_assoc]
      _ = x + (3 ^ q * sourceUnit) * u := by rw [hendpoint]
      _ = x + 3 ^ q * (sourceUnit * u) := by
              simp [Nat.mul_assoc]

#print axioms earlier_source_collision_of_coalescent_cylinders

end CollatzFinal.SourceProduct
