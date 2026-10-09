import Collatz.SourceProductAffine

namespace CollatzFinal
namespace SourceProduct

/-- Exact shift of all offsets in a dyadic parity cylinder, not sampled offsets. -/
theorem parity_cylinder_shift (r k q : Nat) :
    iter shortcut k (r + 2 ^ k * q) =
      iter shortcut k r + 3 ^ oddCount r k * q := by
  induction k generalizing q with
  | zero => simp [iter, oddCount]
  | succ k ih =>
      have hpow : 2 ^ (k + 1) * q = 2 ^ k * (2 * q) := by
        simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
      calc
        iter shortcut (k + 1) (r + 2 ^ (k + 1) * q) =
            shortcut (iter shortcut k (r + 2 ^ k * (2 * q))) := by
              rw [iter_succ_last, hpow]
        _ = shortcut (iter shortcut k r + 3 ^ oddCount r k * (2 * q)) := by
              rw [ih]
        _ = shortcut (iter shortcut k r + 2 * (3 ^ oddCount r k * q)) := by
              congr 1
              simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
        _ = shortcut (iter shortcut k r) +
            (if iter shortcut k r % 2 = 0 then 3 ^ oddCount r k * q
             else 3 * (3 ^ oddCount r k * q)) := shortcut_shift _ _
        _ = iter shortcut (k + 1) r + 3 ^ oddCount r (k + 1) * q := by
              rw [iter_succ_last]
              by_cases h : iter shortcut k r % 2 = 0
              · simp [oddCount, h]
              · simp [oddCount, h, Nat.pow_succ, Nat.mul_assoc,
                  Nat.mul_comm, Nat.mul_left_comm]

/-- A descending base point and nonexpanding exact cylinder coefficient
    yield a source-relative coalescence for *every* nonnegative offset. -/
theorem cylinder_direct_all_offsets (r k q : Nat)
    (hbase : iter shortcut k r < r)
    (hcoef : 3 ^ oddCount r k ≤ 2 ^ k) :
    LowerMerge shortcut (r + 2 ^ k * q)
      (iter shortcut k (r + 2 ^ k * q)) := by
  have hslope := Nat.mul_le_mul_right q hcoef
  have hdrop :
      iter shortcut k (r + 2 ^ k * q) < r + 2 ^ k * q := by
    rw [parity_cylinder_shift]
    omega
  exact ⟨hdrop, k, 0, rfl⟩

/-- An exact odd predecessor: 3*p+1=2*y forces p odd and shortcut p=y. -/
theorem exact_inverse_odd_step (y p : Nat)
    (h : 2 * y = 3 * p + 1) : shortcut p = y := by
  have hodd : p % 2 = 1 := by omega
  simp [shortcut, hodd]
  omega

/-- Inverse-odd merger compiled uniformly over a dyadic cylinder.
    The affine predecessor changes by c for each dyadic source offset. -/
theorem cylinder_inverse_odd_all_offsets (r k q p0 c : Nat)
    (hbase : 2 * iter shortcut k r = 3 * p0 + 1)
    (hcoef : 2 * 3 ^ oddCount r k = 3 * c)
    (hbelow : p0 < r)
    (hbound : c ≤ 2 ^ k) :
    LowerMerge shortcut (r + 2 ^ k * q) (p0 + c * q) := by
  have hslope := Nat.mul_le_mul_right q hbound
  have hlt : p0 + c * q < r + 2 ^ k * q := by omega
  have hcoefq := congrArg (fun z : Nat => z * q) hcoef
  have hinverse :
      2 * iter shortcut k (r + 2 ^ k * q) =
        3 * (p0 + c * q) + 1 := by
    rw [parity_cylinder_shift]
    simp only [Nat.mul_add]
    have hscaled : 2 * (3 ^ oddCount r k * q) = 3 * (c * q) := by
      simpa [Nat.mul_assoc] using hcoefq
    omega
  refine ⟨hlt, k, 1, ?_⟩
  simpa [iter] using (exact_inverse_odd_step _ _ hinverse).symm

/-- An arbitrary shorter prefix of a deeper dyadic cylinder retains its
    exact affine slope. This is the form V109's compiler actually uses:
    the source modulus is 2^(j+h), not necessarily 2^j. -/
theorem parity_prefix_shift (r j h q : Nat) :
    iter shortcut j (r + 2 ^ (j + h) * q) =
      iter shortcut j r +
        (2 ^ h * 3 ^ oddCount r j) * q := by
  have hfactor : 2 ^ (j + h) * q = 2 ^ j * (2 ^ h * q) := by
    simp [Nat.pow_add, Nat.mul_assoc]
  calc
    iter shortcut j (r + 2 ^ (j + h) * q) =
        iter shortcut j (r + 2 ^ j * (2 ^ h * q)) := by rw [hfactor]
    _ = iter shortcut j r + 3 ^ oddCount r j * (2 ^ h * q) :=
      parity_cylinder_shift r j (2 ^ h * q)
    _ = _ := by
      simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]

#print axioms parity_prefix_shift

#print axioms parity_cylinder_shift
#print axioms cylinder_direct_all_offsets
#print axioms exact_inverse_odd_step
#print axioms cylinder_inverse_odd_all_offsets

end SourceProduct
end CollatzFinal
