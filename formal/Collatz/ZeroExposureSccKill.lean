import Collatz.GuardedDyadicSwitch

namespace CollatzFinal.SourceProduct

/-- Exact composition of the sole recurrent zero-exposure return-law pair:
    (9m+7)/32 followed by (9m+1)/8. -/
theorem zeroExposurePair_compose
    {m0 m1 m2 : Int}
    (h0 : 32 * m1 = 9 * m0 + 7)
    (h1 : 8 * m2 = 9 * m1 + 1) :
    256 * m2 = 81 * m0 + 95 := by
  omega

/-- The composite centre is 19/35, so no integer state has zero composite
defect. -/
theorem zeroExposurePair_defect_ne_zero (m : Int) :
    returnDefect 81 95 256 m ≠ 0 := by
  intro h
  simp [returnDefect] at h
  omega

/-- The symbolic two-law SCC cannot be traversed forever by integer states.
Each complete lap is the fixed affine law
    256*m' = 81*m + 95,
whose nonzero defect loses eight dyadic orders per lap. -/
theorem zeroExposurePair_no_infinite_laps
    (m : Nat → Int)
    (hstep : ∀ i, 256 * m (i + 1) = 81 * m i + 95) :
    False := by
  let delta : Nat → Int :=
    fun i => returnDefect 81 95 256 (m i)
  have htransport :
      ∀ i, (2 : Int) ^ 8 * delta (i + 1) = 81 * delta i := by
    intro i
    dsimp [delta]
    have h :=
      returnDefect_self_scale 81 95 256 (m i) (m (i + 1)) (hstep i)
    simpa using h
  have hA : ∀ i, (81 : Int) % 2 = 1 := by
    intro i
    decide
  have hD : ∀ i, 0 < (8 : Nat) := by
    intro i
    omega
  have hnz : ∀ i, delta i ≠ 0 := by
    intro i
    dsimp [delta]
    exact zeroExposurePair_defect_ne_zero (m i)
  exact fixed_centre_exhaustion
    delta (fun _ => 81) (fun _ => 8)
    hA hD htransport hnz

#print axioms zeroExposurePair_compose
#print axioms zeroExposurePair_defect_ne_zero
#print axioms zeroExposurePair_no_infinite_laps

end CollatzFinal.SourceProduct
