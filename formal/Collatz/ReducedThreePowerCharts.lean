import Collatz.CanonicalCrossPowerChart

namespace CollatzFinal

/-!
V136 — remove redundant 3-power coordinates from V135.

For α=oddCount(a,i) and β=oddCount(p,j), V135 used
  u=3^β, v=3^α
to make 3^α*u=3^β*v. The same identity already holds for
  u=3^(β-α), v=3^(α-β),
where subtraction is NATURAL truncated subtraction.

This is a smaller EXACT integer chart pair. The weighted source guard
still must be separately warranted. No universal source-event theorem.

Protected-future insight: root RECOGNITION is not the same as preserving
root typing on every auxiliary predecessor. Reduced affine charts can
preserve a source n ≡ 3 mod 6 while their earlier positive witnesses
move out of that residue class. Such witnesses are still lawful
source-relative two-clock exits and must not be erased by a root-only
proof-grammar choice.

At t=1, source n=45 gets p=7 from the reduced root21 chart,
where V129's 21+72t family has no corresponding parameter.
This is strict mathematical family enlargement, not finite sample
coverage or a proof of Collatz.
-/

/-- The automatic endpoint-slope identity holds after removing all
redundant cross-powers from the two chart multipliers. -/
theorem reduced_odd_power_endpoint_balance (alpha beta : Nat) :
    3 ^ alpha * 3 ^ (beta - alpha) =
    3 ^ beta * 3 ^ (alpha - beta) := by
  calc
    3 ^ alpha * 3 ^ (beta - alpha) =
        3 ^ (alpha + (beta - alpha)) :=
      (Nat.pow_add 3 alpha (beta - alpha)).symm
    _ = 3 ^ (beta + (alpha - beta)) := by
      congr 1
      omega
    _ = 3 ^ beta * 3 ^ (alpha - beta) :=
      Nat.pow_add 3 beta (alpha - beta)

/-- A source-preserving future join constructed from a TRUE base
two-clock collision and ONE exact weighted clock guard, no additional
free coefficient search. No claim that suitable clocks exist for
every source. -/
def reducedCrossPowerJoin (a p i j : Nat)
    (hp : 0 < p)
    (hearlier : p < a)
    (hmeet : iter shortcut i a = iter shortcut j p)
    (hguard :
        2 ^ j * 3 ^ (SourceProduct.oddCount a i -
                       SourceProduct.oddCount p j) <=
        2 ^ i * 3 ^ (SourceProduct.oddCount p j -
                       SourceProduct.oddCount a i))
    (t : Nat) : LawfulFutureJoin :=
  chartOverlapJoin a p i j
    (3 ^ (SourceProduct.oddCount p j - SourceProduct.oddCount a i))
    (3 ^ (SourceProduct.oddCount a i - SourceProduct.oddCount p j))
    hp hearlier hguard hmeet
    (reduced_odd_power_endpoint_balance
       (SourceProduct.oddCount a i) (SourceProduct.oddCount p j))
    t

theorem reduced_chart_compiles_lower_source
    (a p i j : Nat) (hp : 0 < p) (hearlier : p < a)
    (hmeet : iter shortcut i a = iter shortcut j p)
    (hguard :
        2 ^ j * 3 ^ (SourceProduct.oddCount a i -
                       SourceProduct.oddCount p j) <=
        2 ^ i * 3 ^ (SourceProduct.oddCount p j -
                       SourceProduct.oddCount a i))
    (t : Nat) :
    LowerMerge shortcut
      (a + 2 ^ i *
        (3 ^ (SourceProduct.oddCount p j -
               SourceProduct.oddCount a i) * t))
      (p + 2 ^ j *
        (3 ^ (SourceProduct.oddCount a i -
               SourceProduct.oddCount p j) * t)) :=
  (reducedCrossPowerJoin a p i j hp hearlier hmeet hguard t).toLowerMerge

/-- The V129 source21 relation now has smaller legal source and
predecessor slopes (24,4), compared with (72,12). -/
def reducedRoot21 (t : Nat) : LawfulFutureJoin := by
  have hm : iter shortcut 3 21 = iter shortcut 2 3 := by decide
  have hg :
      2 ^ 2 * 3 ^ (SourceProduct.oddCount 21 3 -
                   SourceProduct.oddCount 3 2) <=
      2 ^ 3 * 3 ^ (SourceProduct.oddCount 3 2 -
                   SourceProduct.oddCount 21 3) := by decide
  exact reducedCrossPowerJoin 21 3 3 2
    (by decide) (by decide) hm hg t

theorem reducedRoot21_source (t : Nat) :
    (reducedRoot21 t).source = 21 + 24 * t := by
  change
    21 + 2 ^ 3 *
      (3 ^ (SourceProduct.oddCount 3 2 -
             SourceProduct.oddCount 21 3) * t) =
      21 + 24 * t
  have hslope :
      2 ^ 3 * 3 ^ (SourceProduct.oddCount 3 2 -
                     SourceProduct.oddCount 21 3) = 24 := by decide
  calc
    21 + 2 ^ 3 *
      (3 ^ (SourceProduct.oddCount 3 2 -
             SourceProduct.oddCount 21 3) * t) =
      21 + (2 ^ 3 * 3 ^ (SourceProduct.oddCount 3 2 -
             SourceProduct.oddCount 21 3)) * t := by
        simp [Nat.mul_assoc]
    _ = 21 + 24 * t := by rw [hslope]

theorem reducedRoot21_earlier (t : Nat) :
    (reducedRoot21 t).earlier = 3 + 4 * t := by
  change
    3 + 2 ^ 2 *
      (3 ^ (SourceProduct.oddCount 21 3 -
             SourceProduct.oddCount 3 2) * t) =
      3 + 4 * t
  have hslope :
      2 ^ 2 * 3 ^ (SourceProduct.oddCount 21 3 -
                     SourceProduct.oddCount 3 2) = 4 := by decide
  calc
    3 + 2 ^ 2 *
      (3 ^ (SourceProduct.oddCount 21 3 -
             SourceProduct.oddCount 3 2) * t) =
      3 + (2 ^ 2 * 3 ^ (SourceProduct.oddCount 21 3 -
             SourceProduct.oddCount 3 2)) * t := by
        simp [Nat.mul_assoc]
    _ = 3 + 4 * t := by rw [hslope]

/-- Exact all-offset STRICT lower-source coalescence. Note: the
original source stays an odd 3-root, but the earlier source need not
be divisible by 3. The protected coalescence relation allows this. -/
theorem reducedRoot21_all_offsets (t : Nat) :
    0 < 3 + 4 * t ∧
    3 + 4 * t < 21 + 24 * t ∧
    (21 + 24 * t) % 6 = 3 ∧
    iter shortcut 3 (21 + 24 * t) =
      iter shortcut 2 (3 + 4 * t) := by
  let w := reducedRoot21 t
  have hn : w.source = 21 + 24 * t := reducedRoot21_source t
  have hp : w.earlier = 3 + 4 * t := reducedRoot21_earlier t
  have hc : iter shortcut 3 (21 + 24 * t) =
      iter shortcut 2 (3 + 4 * t) := by
    have h := w.common
    rw [hn, hp] at h
    exact h
  exact ⟨by omega, by omega, by omega, hc⟩

/-- Strictly new instance outside V129's prior source lattice.
45 is a positive 3-root and its warranted predecessor 7 is not
divisible by 3. No artificial root-type requirement may discard it. -/
theorem reducedRoot21_new_source45 :
    iter shortcut 3 45 = iter shortcut 2 7 ∧
    7 < 45 ∧ 45 % 6 = 3 ∧ 7 % 3 ≠ 0 := by
  decide

/-- The pre-existing V129 all-offset family is exactly the subfamily
obtained by restricting the NEW reduced parameter to 3*t. -/
theorem old_root21_is_reduced_subfamily (t : Nat) :
    (reducedRoot21 (3 * t)).source = 21 + 72 * t ∧
    (reducedRoot21 (3 * t)).earlier = 3 + 12 * t := by
  rw [reducedRoot21_source, reducedRoot21_earlier]
  constructor <;> omega

/-- Coefficient cancellation similarly widens V131 root9 from
9+1536*t → 3+486*t to 9+512*t → 3+162*t. -/
def reducedRoot9 (t : Nat) : LawfulFutureJoin := by
  have hm : iter shortcut 9 9 = iter shortcut 1 3 := by decide
  have hg :
      2 ^ 1 * 3 ^ (SourceProduct.oddCount 9 9 -
                   SourceProduct.oddCount 3 1) <=
      2 ^ 9 * 3 ^ (SourceProduct.oddCount 3 1 -
                   SourceProduct.oddCount 9 9) := by decide
  exact reducedCrossPowerJoin 9 3 9 1
    (by decide) (by decide) hm hg t

theorem reducedRoot9_source (t : Nat) :
    (reducedRoot9 t).source = 9 + 512 * t := by
  change
    9 + 2 ^ 9 *
      (3 ^ (SourceProduct.oddCount 3 1 -
             SourceProduct.oddCount 9 9) * t) =
      9 + 512 * t
  have h :
      2 ^ 9 * 3 ^ (SourceProduct.oddCount 3 1 -
                     SourceProduct.oddCount 9 9) = 512 := by decide
  calc
    9 + 2 ^ 9 *
      (3 ^ (SourceProduct.oddCount 3 1 -
             SourceProduct.oddCount 9 9) * t) =
      9 + (2 ^ 9 * 3 ^ (SourceProduct.oddCount 3 1 -
             SourceProduct.oddCount 9 9)) * t := by
        simp [Nat.mul_assoc]
    _ = 9 + 512 * t := by rw [h]

theorem reducedRoot9_earlier (t : Nat) :
    (reducedRoot9 t).earlier = 3 + 162 * t := by
  change
    3 + 2 ^ 1 *
      (3 ^ (SourceProduct.oddCount 9 9 -
             SourceProduct.oddCount 3 1) * t) =
      3 + 162 * t
  have h :
      2 ^ 1 * 3 ^ (SourceProduct.oddCount 9 9 -
                     SourceProduct.oddCount 3 1) = 162 := by decide
  calc
    3 + 2 ^ 1 *
      (3 ^ (SourceProduct.oddCount 9 9 -
             SourceProduct.oddCount 3 1) * t) =
      3 + (2 ^ 1 * 3 ^ (SourceProduct.oddCount 9 9 -
             SourceProduct.oddCount 3 1)) * t := by
        simp [Nat.mul_assoc]
    _ = 3 + 162 * t := by rw [h]

theorem reducedRoot9_lower_merge (t : Nat) :
    LowerMerge shortcut (9 + 512 * t) (3 + 162 * t) := by
  have h := (reducedRoot9 t).toLowerMerge
  have hn := reducedRoot9_source t
  have hp := reducedRoot9_earlier t
  rw [hn, hp] at h
  exact h

/-- Again, the V131 entire root9 source lattice is a strict
subfamily of this reduced one. -/
theorem old_root9_is_reduced_subfamily (t : Nat) :
    (reducedRoot9 (3 * t)).source = 9 + 1536 * t ∧
    (reducedRoot9 (3 * t)).earlier = 3 + 486 * t := by
  rw [reducedRoot9_source, reducedRoot9_earlier]
  constructor <;> omega

#print axioms reduced_odd_power_endpoint_balance
#print axioms reducedCrossPowerJoin
#print axioms reduced_chart_compiles_lower_source
#print axioms reducedRoot21
#print axioms reducedRoot21_source
#print axioms reducedRoot21_earlier
#print axioms reducedRoot21_all_offsets
#print axioms reducedRoot21_new_source45
#print axioms old_root21_is_reduced_subfamily
#print axioms reducedRoot9
#print axioms reducedRoot9_source
#print axioms reducedRoot9_earlier
#print axioms reducedRoot9_lower_merge
#print axioms old_root9_is_reduced_subfamily

end CollatzFinal
