import Collatz.SourceProductAffine
import Collatz.ActualEpisode
import Collatz.ZeroTailTernarySieve

namespace CollatzFinal
namespace SourceProduct

/-!
V160: REAL SOURCE-ATTACHED DYADIC CYLINDER TARGET LIFTS.

This is a first-principles theorem about the ACTUAL odd affine law.
For all n,k,q, the first k parity decisions are unchanged by
adding 2^k*q to the ORIGINAL source, and the endpoint shifts
by exactly 3^oddCount(n,k)*q.

If a natural-number target 2^L*b lies on that endpoint progression,
then the constructed original source n=r+2^k*q reaches b at
ACTUAL clock k+L, with no virtual 2-adic source.

For all 3-coprime b and endpoint residues the required power
congruence is solvable by the elementary number theory that
2 is a primitive root of 3^a. That power-surjectivity theorem
has NOT been reified in this Lean module: its power-hit witness
remains a visible explicit input, and CI will check only its
sound consumption.

Crucially, source-existence in every dyadic cylinder alone gives
NO density, growth or convergence theorem; Mersenne cylinders
can make one-chart power-of-two target certificates exponentially
large in their bit depth. GLOBAL COLLATZ UNKNOWN.
-/

/-- Independently source-typed, ALL-SOURCE/ALL-DEPTH actual affine lift.
    No assumptions about future convergence, periodicity or bad sets. -/
theorem v160_exact_cylinder_affine :
    ∀ k n q : Nat,
      iter shortcut k (n + 2^k*q) =
        iter shortcut k n + 3^(oddCount n k)*q := by
  intro k
  induction k with
  | zero =>
      intro n q
      simp [iter,oddCount]
  | succ k ih =>
      intro n q
      have hPow :
          2^(k+1)*q = 2^k*(2*q) := by
        simp [Nat.pow_succ,Nat.mul_assoc,Nat.mul_comm,Nat.mul_left_comm]
      have hPre :
          iter shortcut k (n+2^(k+1)*q) =
            iter shortcut k n+2*(3^oddCount n k*q) := by
        rw [hPow,ih n (2*q)]
        congr 1
        ac_rfl
      calc
        iter shortcut (k+1) (n+2^(k+1)*q) =
            shortcut (iter shortcut k (n+2^(k+1)*q)) :=
          iter_succ_last _ _
        _ = shortcut (iter shortcut k n+2*(3^oddCount n k*q)) := by
          rw [hPre]
        _ = shortcut (iter shortcut k n) +
            (if iter shortcut k n%2=0
              then 3^oddCount n k*q else 3*(3^oddCount n k*q)) :=
          shortcut_shift _ _
        _ = iter shortcut (k+1) n +
            3^oddCount n (k+1)*q := by
          rw [iter_succ_last]
          by_cases hEven : iter shortcut k n%2=0
          · simp [oddCount,hEven]
          · simp [oddCount,hEven,Nat.pow_succ,
              Nat.mul_assoc,Nat.mul_comm,Nat.mul_left_comm]

theorem v160_zero_orbit (k : Nat) :
    iter shortcut k 0 = 0 := by
  induction k with
  | zero => rfl
  | succ k ih =>
      rw [iter_succ_last,ih]
      decide

/-- A REAL power target on a parity-cylinder affine chart
    gives a REAL positive source in that residue class, and
    a real future join after two independently meaningful clocks.
    Neither source convergence nor modulus surjectivity is assumed. -/
theorem v160_power_target_is_actual_two_clock_join
    (r k b L q : Nat)
    (hr : r<2^k)
    (hb : 0<b)
    (hPower : iter shortcut k r + 3^oddCount r k*q = 2^L*b) :
    ∃ n : Nat,
      0<n ∧ n%2^k=r ∧ iter shortcut (k+L) n=b := by
  let n := r+2^k*q
  have hEndpoint : iter shortcut k n = 2^L*b := by
    dsimp [n]
    rw [v160_exact_cylinder_affine]
    exact hPower
  have hn : 0<n := by
    by_cases he : n=0
    · have hz := v160_zero_orbit k
      rw [he,hz] at hEndpoint
      have hPos : 0<2^L*b :=
        Nat.mul_pos (Nat.pow_pos (by decide)) hb
      omega
    · exact Nat.pos_of_ne_zero he
  have hResidue : n%2^k=r := by
    dsimp [n]
    have hm : r%2^k=r := Nat.mod_eq_of_lt hr
    simp [Nat.add_mod,Nat.mul_mod,hm]
  refine ⟨n,hn,hResidue,?_⟩
  calc
    iter shortcut (k+L) n =
        iter shortcut L (iter shortcut k n) := iter_add _ _ _ _
    _ = iter shortcut L (2^L*b) := by rw [hEndpoint]
    _ = b := iter_pow_two_mul L b

/-- A visible NUMBER-THEORY witness interface, not a hidden
    global Collatz hypothesis: arbitrarily large exact power-of-two
    multiples of a prescribed target lie in the affine endpoint
    congruence class. The primitive-root fact supplies it for
    b and g coprime with 3, but that lemma is not built here. -/
def V160UnboundedPowerChartHits (a b g : Nat) : Prop :=
  ∀ H : Nat, ∃ L q : Nat,
    H≤L ∧ g+3^a*q=2^L*b

/-- Under the explicitly supplied primitive-root-type number theory,
    one can construct genuinely source-attached ancestors in EVERY
    fixed parity cylinder, at arbitrarily late TARGET CLOCKS.
    This is a non-circular construction (it never assumes b converges),
    and it does not bound the constructed source size. -/
theorem v160_all_prefix_real_future_ancestors_of_power_hits
    (r k b : Nat) (hr : r<2^k) (hb : 0<b)
    (hHits : V160UnboundedPowerChartHits
      (oddCount r k) b (iter shortcut k r)) :
    ∀ H : Nat,
      ∃ n L : Nat,
        H≤L ∧ 0<n ∧ n%2^k=r ∧
        iter shortcut (k+L) n=b := by
  intro H
  obtain ⟨L,q,hL,hPower⟩ := hHits H
  obtain ⟨n,hn,hres,hJoin⟩ :=
    v160_power_target_is_actual_two_clock_join
      r k b L q hr hb hPower
  exact ⟨n,L,hL,hn,hres,hJoin⟩

/-- Every positive genuine prefix r<2^k has a non-3-divisible
    kth endpoint; no extra target-divisibility hypothesis is needed
    on the PARITY-CYLINDER SIDE of the primitive-root bridge. -/
theorem v160_every_positive_short_prefix_three_unit
    (r k : Nat) (hrPos : 0<r) (hr : r<2^k) :
    (iter shortcut k r)%3≠0 :=
  v158_after_source_bits_nondivisible_three hrPos hr

#print axioms v160_exact_cylinder_affine
#print axioms v160_zero_orbit
#print axioms v160_power_target_is_actual_two_clock_join
#print axioms v160_all_prefix_real_future_ancestors_of_power_hits
#print axioms v160_every_positive_short_prefix_three_unit

end SourceProduct
end CollatzFinal
