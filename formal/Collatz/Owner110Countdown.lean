import Collatz.ReturnFixedPointDescent

-- V57 rebased on the green V51 affine-budget authority.
namespace CollatzFinal
namespace SourceProduct

/-- The exact owner return behind the V55 maximal residual stratum:
    m' = (9*m+1)/8. -/
def Owner110Next (m m' : Nat) : Prop :=
  8 * m' = 9 * m + 1

/-- A finite chain of exact 110 owner returns, indexed by its length. -/
inductive Owner110Chain : Nat → Nat → Prop
  | zero (m : Nat) : Owner110Chain 0 m
  | succ {k m m' : Nat} :
      Owner110Next m m' →
      Owner110Chain k m' →
      Owner110Chain (k + 1) m

theorem owner110_plus_one {m m' : Nat}
    (h : Owner110Next m m') :
    8 * (m' + 1) = 9 * (m + 1) := by
  unfold Owner110Next at h
  omega

/-- Every exact 110 return consumes three powers of two from m+1.
After t returns, the starting owner therefore satisfies
    2^(3*t) ∣ m+1.
This is independent of any finite chamber/centre bank. -/
theorem owner110_chain_pow_two_dvd
    {t m : Nat}
    (h : Owner110Chain t m) :
    2 ^ (3 * t) ∣ m + 1 := by
  induction h with
  | zero m =>
      simp
  | @succ k m m' hstep htail ih =>
      rcases ih with ⟨c, hc⟩
      have hplus : 8 * (m' + 1) = 9 * (m + 1) :=
        owner110_plus_one hstep
      have hpow :
          2 ^ (3 * (k + 1)) = 8 * 2 ^ (3 * k) := by
        have he : 3 * (k + 1) = 3 * k + 3 := by omega
        rw [he, Nat.pow_add]
        have h8 : (2 : Nat) ^ 3 = 8 := by decide
        rw [h8, Nat.mul_comm]
      have hd : 2 ^ (3 * (k + 1)) ∣ 9 * (m + 1) := by
        refine ⟨c, ?_⟩
        calc
          9 * (m + 1) = 8 * (m' + 1) := hplus.symm
          _ = 8 * (2 ^ (3 * k) * c) := by rw [hc]
          _ = (8 * 2 ^ (3 * k)) * c := by
            simp [Nat.mul_assoc]
          _ = 2 ^ (3 * (k + 1)) * c := by rw [hpow]
      have hcop2 : Nat.Coprime 2 9 := by decide
      have hcop :
          Nat.Coprime (2 ^ (3 * (k + 1))) 9 :=
        hcop2.pow_left (3 * (k + 1))
      exact hcop.dvd_of_dvd_mul_left hd

/-- An explicit finite-residence bound: a natural owner m cannot execute
m+1 consecutive exact 110 returns.  Thus no infinite natural-owner execution
can remain forever in the V55 maximal mechanism. -/
theorem owner110_no_chain_self_bound (m : Nat) :
    ¬ Owner110Chain (m + 1) m := by
  intro h
  have hd : 2 ^ (3 * (m + 1)) ∣ m + 1 :=
    owner110_chain_pow_two_dvd h
  have hle : 2 ^ (3 * (m + 1)) ≤ m + 1 :=
    Nat.le_of_dvd (by omega) hd
  have hexp : m + 1 ≤ 3 * (m + 1) := by omega
  have hp :
      2 ^ (m + 1) ≤ 2 ^ (3 * (m + 1)) :=
    Nat.pow_le_pow_of_le (by decide) hexp
  have hlt : m + 1 < 2 ^ (m + 1) :=
    (m + 1).lt_two_pow_self
  omega

#print axioms owner110_plus_one
#print axioms owner110_chain_pow_two_dvd
#print axioms owner110_no_chain_self_bound

end SourceProduct
end CollatzFinal
