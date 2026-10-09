import Collatz.ActualEpisodeChain
import Collatz.DistinctCentreSwitch

namespace CollatzFinal
namespace SourceProduct

/-- A finite actual episode word has a pure 3-power multiplicative
coefficient and a pure 2-power return denominator. -/
theorem actual_chain_power_shapes
    {r0 m0 r m t A B P : Nat}
    (hc : ActualEpisodeChain r0 m0 r m t A B P) :
    ∃ q D : Nat, A = 3 ^ q ∧ P = 2 ^ D := by
  induction hc with
  | empty =>
      exact ⟨0, 0, by simp, by simp⟩
  | @append r m t A B P s r' m' hchain he ih =>
      obtain ⟨q, D, hA, hP⟩ := ih
      refine ⟨r + q, s + r' + D, ?_, ?_⟩
      · rw [hA]
        simp [Nat.pow_add, Nat.mul_assoc]
      · rw [hP]
        simp [Nat.pow_add, Nat.mul_assoc]

/-- Odd source and destination owners force two more dyadic facts:
the difference m0-m1 is even, and therefore the affine-return defect
is divisible by 2^(D+1), not merely 2^D.

The proof consumes only the exact affine equation, not a finite bank. -/
theorem odd_owner_return_defect_divisible
    {A B m0 m1 : Nat} {D : Nat}
    (hodd0 : m0 % 2 = 1)
    (hodd1 : m1 % 2 = 1)
    (hEq : 2 ^ D * m1 = A * m0 + B) :
    (2 : Int) ^ (D + 1) ∣
      returnDefect (A : Int) (B : Int) ((2 : Int) ^ D) (m0 : Int) := by
  have hodd0I : (m0 : Int) % 2 = 1 := nat_odd_int hodd0
  have hodd1I : (m1 : Int) % 2 = 1 := nat_odd_int hodd1
  have heven :
      (m0 : Int) - (m1 : Int) =
        2 * (((m0 : Int) - (m1 : Int)) / 2) := by
    omega
  have hCast :=
    congrArg (fun z : Nat => (z : Int)) hEq
  have hEqI :
      (2 : Int) ^ D * (m1 : Int) =
        (A : Int) * (m0 : Int) + (B : Int) := by
    simpa using hCast
  have hDef :
      returnDefect (A : Int) (B : Int)
        ((2 : Int) ^ D) (m0 : Int) =
        (2 : Int) ^ D * ((m0 : Int) - (m1 : Int)) := by
    unfold returnDefect
    rw [Int.sub_mul, Int.mul_sub]
    omega
  refine ⟨(((m0 : Int) - (m1 : Int)) / 2), ?_⟩
  rw [hDef, heven]
  simp [Int.pow_succ, Int.mul_assoc,
    Int.mul_comm, Int.mul_left_comm]

/-- Exact old/new odd owner return is either fixed (zero defect),
or meets the new-return cylinder admission required by V88/V96.
No finite order is attached to the zero branch. -/
theorem odd_owner_return_zero_or_admissible
    {A B m0 m1 : Nat} {D : Nat}
    (hodd0 : m0 % 2 = 1)
    (hodd1 : m1 % 2 = 1)
    (hEq : 2 ^ D * m1 = A * m0 + B) :
    returnDefect (A : Int) (B : Int)
        ((2 : Int) ^ D) (m0 : Int) = 0 ∨
      ReturnCylinderAdmissible (A : Int) (B : Int) D (m0 : Int) := by
  let delta :=
    returnDefect (A : Int) (B : Int) ((2 : Int) ^ D) (m0 : Int)
  by_cases hz : delta = 0
  · exact Or.inl hz
  · right
    obtain ⟨v, hv⟩ := dyadic_order_exists hz
    obtain ⟨z, hzDiv⟩ :=
      odd_owner_return_defect_divisible hodd0 hodd1 hEq
    have hbound := (dyadic_divide hv hzDiv.symm).1
    exact ⟨v, hbound, hv⟩

/-- A positive-length actual same-anchor chain, with its natural odd
endpoint owners, emits the exact 2-power return-law and V88/V96
admission-or-fixed certificate, bound to the actual shortcut orbit.

The only remaining prerequisites for a global proof are obtaining suitable
returns from every no-exit orbit and establishing consequential progress
from their classified continuation, including genuine periodicity. -/
theorem actual_same_anchor_return_admission
    {r m0 m1 t A B P : Nat}
    (hc : ActualEpisodeChain r m0 r m1 t A B P)
    (ht : 0 < t)
    (hodd0 : m0 % 2 = 1)
    (hodd1 : m1 % 2 = 1) :
    ∃ q D : Nat,
      A = 3 ^ q ∧ P = 2 ^ D ∧
      (returnDefect (A : Int) (B : Int)
          ((2 : Int) ^ D) (m0 : Int) = 0 ∨
        ReturnCylinderAdmissible
          (A : Int) (B : Int) D (m0 : Int)) ∧
      P * m1 = A * m0 + B ∧
      iter shortcut t (2 ^ r * m0 - 1) = 2 ^ r * m1 - 1 := by
  obtain ⟨q, D, hA, hP⟩ := actual_chain_power_shapes hc
  have hAff := actual_episode_chain_affine hc
  have hEq : 2 ^ D * m1 = A * m0 + B := by
    simpa [hP] using hAff
  exact ⟨q, D, hA, hP,
    odd_owner_return_zero_or_admissible hodd0 hodd1 hEq,
    hAff, actual_episode_chain_shortcut hc⟩

#print axioms actual_chain_power_shapes
#print axioms odd_owner_return_defect_divisible
#print axioms odd_owner_return_zero_or_admissible
#print axioms actual_same_anchor_return_admission

end SourceProduct
end CollatzFinal
