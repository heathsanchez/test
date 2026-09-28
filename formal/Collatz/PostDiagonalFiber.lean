import Collatz.QuarterSplice

namespace CollatzFinal
namespace SourceProduct

/-- Beyond the source/odd-count diagonal, the source-relative band is tiny
compared with the exact 3-adic endpoint modulus. -/
theorem four_mul_lt_three_pow_of_three_le
    (q : Nat) (hq : 3 ≤ q) :
    4 * q < 3 ^ q := by
  induction q with
  | zero => omega
  | succ q ih =>
      by_cases hprev : 3 ≤ q
      · have hmain : 4 * q < 3 ^ q := ih hprev
        have hpow : 3 ≤ 3 ^ q := by
          have hq1 : 1 ≤ q := by omega
          have hp := Nat.pow_le_pow_right (by decide : 0 < 3) hq1
          simpa using hp
        have htail : 4 < 2 * 3 ^ q := by omega
        calc
          4 * (q + 1) = 4 * q + 4 := by omega
          _ < 3 ^ q + 2 * 3 ^ q := Nat.add_lt_add hmain htail
          _ = 3 ^ (q + 1) := by
            rw [Nat.pow_succ]
            omega
      · have hqeq : q = 2 := by omega
        subst q
        decide

/-- Exact post-diagonal band bound.

If q has already reached the positive odd source n, then any endpoint still in
the quarter-splice band is strictly smaller than the modulus 3^q.  This is the
arithmetic reason the source-affine congruence becomes an ordinary small
endpoint representative rather than merely a residue class. -/
theorem post_diagonal_band_lt_three_pow
    {n q y : Nat}
    (hn : 3 ≤ n)
    (hnq : n ≤ q)
    (hband : y ≤ 4 * n) :
    y < 3 ^ q := by
  have hscale : 4 * n ≤ 4 * q :=
    Nat.mul_le_mul_left 4 hnq
  have hmod : 4 * q < 3 ^ q :=
    four_mul_lt_three_pow_of_three_le q (by omega)
  omega

/-- Source-fiber form with the exact affine prefix identity retained. -/
theorem post_diagonal_band_source_fiber
    {n q D y B : Nat}
    (hn : 3 ≤ n)
    (hnq : n ≤ q)
    (hband : y ≤ 4 * n)
    (haff : 2 ^ D * y = 3 ^ q * n + B) :
    y < 3 ^ q ∧
      2 ^ D * y = B + 3 ^ q * n := by
  refine ⟨post_diagonal_band_lt_three_pow hn hnq hband, ?_⟩
  simpa [Nat.add_comm] using haff

#print axioms four_mul_lt_three_pow_of_three_le
#print axioms post_diagonal_band_lt_three_pow
#print axioms post_diagonal_band_source_fiber

end SourceProduct
end CollatzFinal
