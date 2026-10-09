import Collatz.CylinderCoalescence

namespace CollatzFinal
namespace SourceProduct

/-- Symbolic reverse words preserve an exact affine family for every offset.
    The constructors are actual shortcut inverse steps, never free words. -/
inductive AffineReverse : Nat → Nat → Nat → Nat → Nat → Prop where
  | seed (x a : Nat) : AffineReverse x a x a 0
  | even {x a p c t : Nat} (h : AffineReverse x a p c t) :
      AffineReverse x a (2 * p) (2 * c) (t + 1)
  | odd {x a p c t : Nat} (h : AffineReverse x a p c t)
      (p' c' : Nat) (hp : 2 * p = 3 * p' + 1)
      (hc : 2 * c = 3 * c') :
      AffineReverse x a p' c' (t + 1)

/-- Doubling gives an actual even predecessor. -/
theorem shortcut_double_predecessor (z : Nat) :
    shortcut (2 * z) = z := by
  simpa [shortcut] using (shortcut_shift 0 z)

/-- Every affine reverse word commutes with every source-family offset. -/
theorem affine_reverse_sound {x a p c t : Nat}
    (h : AffineReverse x a p c t) (q : Nat) :
    iter shortcut t (p + c * q) = x + a * q := by
  induction h with
  | seed => rfl
  | @even p c t h ih =>
      have heq : 2 * p + 2 * c * q = 2 * (p + c * q) := by
        simp [Nat.mul_add, Nat.mul_assoc]
      calc
        iter shortcut (t + 1) (2 * p + 2 * c * q) =
            iter shortcut t (shortcut (2 * (p + c * q))) := by
              rw [heq]
              rfl
        _ = iter shortcut t (p + c * q) := by rw [shortcut_double_predecessor]
        _ = x + a * q := ih
  | @odd p c t h p' c' hp hc ih =>
      have hcq := congrArg (fun z : Nat => z * q) hc
      have hscaled : 2 * (c * q) = 3 * (c' * q) := by
        simpa [Nat.mul_assoc] using hcq
      have heq : 2 * (p + c * q) = 3 * (p' + c' * q) + 1 := by
        simp only [Nat.mul_add]
        omega
      have hstep : shortcut (p' + c' * q) = p + c * q :=
        exact_inverse_odd_step _ _ heq
      calc
        iter shortcut (t + 1) (p' + c' * q) =
            iter shortcut t (shortcut (p' + c' * q)) := rfl
        _ = iter shortcut t (p + c * q) := by rw [hstep]
        _ = x + a * q := ih

/-- If a lawful reverse affine word has a smaller base and no larger slope,
    all dyadic offsets have a strictly smaller-source future coalescence. -/
theorem affine_reverse_lower_merge_all_offsets
    (r j q p c t : Nat)
    (hword : AffineReverse
      (iter shortcut j r) (3 ^ oddCount r j) p c t)
    (hbelow : p < r) (hslope : c ≤ 2 ^ j) :
    LowerMerge shortcut (r + 2 ^ j * q) (p + c * q) := by
  have hmul := Nat.mul_le_mul_right q hslope
  have hlt : p + c * q < r + 2 ^ j * q := by omega
  refine ⟨hlt, j, t, ?_⟩
  calc
    iter shortcut j (r + 2 ^ j * q) =
        iter shortcut j r + 3 ^ oddCount r j * q := parity_cylinder_shift r j q
    _ = iter shortcut t (p + c * q) := (affine_reverse_sound hword q).symm

/-- The source-relative theorem matching the actual V109 bounded compiler:
    a reverse certificate may start from any forward prefix j of a
    deeper cylinder of depth j+h. No forward-prefix bits are discarded. -/
theorem affine_reverse_lower_merge_prefix_all_offsets
    (r j h q p c t : Nat)
    (hword : AffineReverse
      (iter shortcut j r) (2 ^ h * 3 ^ oddCount r j) p c t)
    (hbelow : p < r) (hslope : c ≤ 2 ^ (j + h)) :
    LowerMerge shortcut (r + 2 ^ (j + h) * q) (p + c * q) := by
  have hmul := Nat.mul_le_mul_right q hslope
  have hlt : p + c * q < r + 2 ^ (j + h) * q := by omega
  refine ⟨hlt, j, t, ?_⟩
  calc
    iter shortcut j (r + 2 ^ (j + h) * q) =
      iter shortcut j r + (2 ^ h * 3 ^ oddCount r j) * q :=
        parity_prefix_shift r j h q
    _ = iter shortcut t (p + c * q) := (affine_reverse_sound hword q).symm

#print axioms affine_reverse_lower_merge_prefix_all_offsets

#print axioms shortcut_double_predecessor
#print axioms affine_reverse_sound
#print axioms affine_reverse_lower_merge_all_offsets

end SourceProduct
end CollatzFinal
