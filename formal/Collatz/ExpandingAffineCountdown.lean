import Collatz.Owner110Countdown

namespace CollatzFinal
namespace SourceProduct

/-- A generic expanding affine return:
    P * m' = (P + C) * m + B.
Here C>0 is the coefficient surplus. -/
def ExpandingAffineNext (C B P m m' : Nat) : Prop :=
  P * m' = (P + C) * m + B

/-- Positive integer defect from the negative real fixed centre of an expanding
affine law.  For P*m'=(P+C)m+B, the fixed centre is -B/C and the numerator
of m-(-B/C) is C*m+B. -/
def expandingDefect (C B m : Nat) : Nat :=
  C * m + B

theorem expanding_defect_transport
    {C B P m m' : Nat}
    (h : ExpandingAffineNext C B P m m') :
    P * expandingDefect C B m' =
      (P + C) * expandingDefect C B m := by
  unfold ExpandingAffineNext at h
  unfold expandingDefect
  calc
    P * (C * m' + B)
        = C * (P * m') + P * B := by
            simp [Nat.mul_add, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
    _ = C * ((P + C) * m + B) + P * B := by rw [h]
    _ = (P + C) * (C * m + B) := by
            simp [Nat.mul_add, Nat.add_mul, Nat.mul_assoc,
              Nat.mul_comm, Nat.mul_left_comm]

/-- A chain of repeated uses of one exact expanding affine law. -/
inductive ExpandingAffineChain (C B P : Nat) : Nat → Nat → Prop
  | zero (m : Nat) : ExpandingAffineChain C B P 0 m
  | succ {k m m' : Nat} :
      ExpandingAffineNext C B P m m' →
      ExpandingAffineChain C B P k m' →
      ExpandingAffineChain C B P (k + 1) m

/-- Repeating one exact expanding law t times forces P^t to divide the
starting fixed-centre defect.  This is the generic version of V57's
2^(3t) | (m+1) countdown. -/
theorem expanding_affine_chain_pow_dvd
    {C B P t m : Nat}
    (hcop : Nat.Coprime P (P + C))
    (h : ExpandingAffineChain C B P t m) :
    P ^ t ∣ expandingDefect C B m := by
  induction h with
  | zero m =>
      simp
  | @succ k m m' hstep htail ih =>
      rcases ih with ⟨c, hc⟩
      have htransport :
          P * expandingDefect C B m' =
            (P + C) * expandingDefect C B m :=
        expanding_defect_transport hstep
      have hpow :
          P ^ (k + 1) = P * P ^ k := by
        rw [Nat.pow_succ]
        rw [Nat.mul_comm]
      have hd :
          P ^ (k + 1) ∣
            (P + C) * expandingDefect C B m := by
        refine ⟨c, ?_⟩
        calc
          (P + C) * expandingDefect C B m =
              P * expandingDefect C B m' := htransport.symm
          _ = P * (P ^ k * c) := by rw [hc]
          _ = (P * P ^ k) * c := by
                simp [Nat.mul_assoc]
          _ = P ^ (k + 1) * c := by rw [hpow]
      have hcopPow :
          Nat.Coprime (P ^ (k + 1)) (P + C) :=
        hcop.pow_left (k + 1)
      exact hcopPow.dvd_of_dvd_mul_left hd

/-- If P>=2, one fixed natural owner cannot execute the same expanding affine
law more than its initial defect value many times.  This is deliberately a
very coarse finite bound; only finiteness matters. -/
theorem expanding_affine_no_chain_self_bound
    {C B P m : Nat}
    (hP : 2 ≤ P)
    (hcop : Nat.Coprime P (P + C)) :
    ¬ ExpandingAffineChain C B P (expandingDefect C B m + 1) m := by
  intro h
  let z := expandingDefect C B m
  have hd :
      P ^ (z + 1) ∣ z := by
    simpa [z] using expanding_affine_chain_pow_dvd hcop h
  have hzpow :
      P ^ (z + 1) ≤ z := by
    exact Nat.le_of_dvd (by positivity) hd
  have hbase :
      2 ^ (z + 1) ≤ P ^ (z + 1) := by
    exact Nat.pow_le_pow_left hP (z + 1)
  have hlt :
      z < 2 ^ (z + 1) := by
    have hs : z + 1 < 2 ^ (z + 1) := (z + 1).lt_two_pow_self
    omega
  omega

/-- Collatz specialization: P is a power of two and the expanding coefficient
is an odd power of three.  Coprimality is therefore automatic. -/
theorem collatz_expanding_affine_no_chain
    {q D B m : Nat}
    (hD : 1 ≤ D)
    (hExpand : 2 ^ D < 3 ^ q)
    (hLaw :
      ∀ {x y : Nat},
        ExpandingAffineNext (3 ^ q - 2 ^ D) B (2 ^ D) x y ↔
          2 ^ D * y = 3 ^ q * x + B) :
    ¬ ExpandingAffineChain
      (3 ^ q - 2 ^ D) B (2 ^ D)
      (expandingDefect (3 ^ q - 2 ^ D) B m + 1) m := by
  have hP : 2 ≤ 2 ^ D := by
    have hp := Nat.pow_le_pow_right (by decide : 1 ≤ (2 : Nat)) hD
    simpa using hp
  have hsum :
      2 ^ D + (3 ^ q - 2 ^ D) = 3 ^ q := by
    omega
  have hcopBase : Nat.Coprime (2 ^ D) (3 ^ q) := by
    have h23 : Nat.Coprime 2 3 := by decide
    exact h23.pow D q
  have hcop :
      Nat.Coprime (2 ^ D) (2 ^ D + (3 ^ q - 2 ^ D)) := by
    simpa [hsum] using hcopBase
  exact expanding_affine_no_chain_self_bound hP hcop

#print axioms expanding_defect_transport
#print axioms expanding_affine_chain_pow_dvd
#print axioms expanding_affine_no_chain_self_bound

end SourceProduct
end CollatzFinal
