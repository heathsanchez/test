import Collatz.DensityAmplificationClosure
import Collatz.ActualEpisode
import Collatz.SourceProductZeroTail

namespace CollatzFinal
namespace SourceProduct

/-!
V158 — EXACT TERNARY SIEVE AFTER SOURCE BIT EXHAUSTION.

This is a genuinely arithmetic and noncircular statement about the
ACTUAL shortcut map, not the empty-kernel or convergence criterion.

For every Nat n and every k:
    3 | T^k(n)  IFF  3*2^k | n.

Proof (backward): an odd shortcut successor is always 2 mod 3.
So any divisible-by-3 endpoint has ONLY an even predecessor, forcing
k consecutive exact halvings and n=2^k*T^k(n).

Thus for ALL positive n<2^k the true endpoint is NOT divisible by 3.
Every source-attached reachable zero-tail state (not every abstract
Valid state!) is inside Mazur's 3-nondivisible target domain.

This discharges the TARGET GUARD for every such state, strengthening
the V150 minimal-bad-successor special case. However Mazur's density
amplifier remains an EXPLICIT external hypothesis, and the all-scale
sparse exceptional terminal-mass premise remains UNKNOWN.

No Collatz QED is asserted or silently inferred.
-/

/-- The genuine 3n+1 odd equation forbids a multiple-of-three
    successor. The only predecessor of an endpoint divisible by 3
    is the exact even doubling of that endpoint. -/
theorem v158_three_target_only_even_predecessor
    (n : Nat) (h : shortcut n % 3 = 0) :
    n = 2 * shortcut n := by
  by_cases he : n % 2 = 0
  · have hs : shortcut n = n / 2 := by simp [shortcut, he]
    rw [hs]
    omega
  · have hs : 2 * shortcut n = 3*n+1 := by
      unfold shortcut
      simp only [he, ite_false]
      omega
    omega

/-- All actual k-step predecessors of a 3-divisible endpoint
    are PURE EVEN. No branch search or statistical assumption. -/
theorem v158_three_target_pure_even_ancestry (k : Nat) :
    ∀ n : Nat, (iter shortcut k n) % 3 = 0 →
      n = 2^k * iter shortcut k n := by
  induction k with
  | zero =>
      intro n _
      simp [iter]
  | succ k ih =>
      intro n hDiv
      have hDivTail :
          (iter shortcut k (shortcut n)) % 3 = 0 := by
        simpa only [iter] using hDiv
      have hRec := ih (shortcut n) hDivTail
      have hDivStep : shortcut n % 3 = 0 := by
        rw [hRec]
        simp [Nat.mul_mod, hDivTail]
      have hEven :=
        v158_three_target_only_even_predecessor n hDivStep
      calc
        n = 2 * shortcut n := hEven
        _ = 2 * (2^k * iter shortcut k (shortcut n)) :=
          congrArg (fun z : Nat => 2*z) hRec
        _ = 2^(k+1) * iter shortcut (k+1) n := by
          simp [Nat.pow_succ, iter, Nat.mul_assoc,
            Nat.mul_comm, Nat.mul_left_comm]

/-- Exact source-level modular preimage sieve. This is
    UNCONDITIONAL for every positive or zero natural. -/
theorem v158_divisible_three_endpoint_iff_source
    (n k : Nat) :
    (iter shortcut k n) % 3 = 0 ↔
      n % (3 * 2^k) = 0 := by
  constructor
  · intro hdiv
    have hh := v158_three_target_pure_even_ancestry k n hdiv
    have hd : 3 ∣ iter shortcut k n :=
      Nat.dvd_of_mod_eq_zero hdiv
    obtain ⟨q, hq⟩ := hd
    apply Nat.mod_eq_zero_of_dvd
    refine ⟨q, ?_⟩
    calc
      n = 2^k * iter shortcut k n := hh
      _ = 2^k * (3*q) := by rw [hq]
      _ = (3 * 2^k) * q := by
        ac_rfl
  · intro hdiv
    have hd : 3*2^k ∣ n :=
      Nat.dvd_of_mod_eq_zero hdiv
    obtain ⟨q,hq⟩ := hd
    have hRep : n = 2^k * (3*q) := by
      calc
        n = (3*2^k)*q := hq
        _ = 2^k*(3*q) := by ac_rfl
    rw [hRep]
    rw [iter_pow_two_mul]
    simp

/-- No positive source with fewer than k bits can have a
    3-divisible endpoint at time k. -/
theorem v158_after_source_bits_nondivisible_three
    {n k : Nat} (hPos : 0<n) (hSmall : n<2^k) :
    (iter shortcut k n) % 3 ≠ 0 := by
  intro hDiv
  have hSource :=
    v158_three_target_pure_even_ancestry k n hDiv
  have hEndPos :=
    iter_positive shortcut shortcut_positive k n hPos
  have hOne : 1 ≤ iter shortcut k n := by omega
  have hLE : 2^k ≤ 2^k * iter shortcut k n := by
    have hh := Nat.mul_le_mul_left (2^k) hOne
    simpa using hh
  omega

/-- SourceProduct proves all reachable states are faithfully
    attached to their ORIGINAL source. Zero tail gives n<2^k,
    which triggers the unconditional ternary sieve above. -/
theorem v158_reachable_zero_tail_nondivisible_three
    (s : State) (hReach : Reachable s) (hTail : s.tail=0) :
    (endpoint s) % 3 ≠ 0 := by
  obtain ⟨n,k,hn,rfl⟩ := hReach
  have hv := at_valid hn k
  have hEq : n = (stateAt n k).sourceResidue := by
    have hsource := hv.2.2.2
    simpa [at_source,at_depth,hTail] using hsource
  have hBound : (stateAt n k).sourceResidue < 2^k := by
    simpa [at_depth] using hv.2.1
  have hSmall : n < 2^k := by omega
  simpa only [at_endpoint] using
    (v158_after_source_bits_nondivisible_three hn hSmall)

theorem v158_zero_tail_live_nondivisible_three
    (s : State) (hs : ZeroTailLive s) :
    (endpoint s) % 3 ≠ 0 :=
  v158_reachable_zero_tail_nondivisible_three s hs.1.1 hs.2

/-- Upgrade V150's least-bad 3-nondivisible bridge to any
    genuine zero-tail LIVE bad endpoint. The mathematical density
    amplifier is still an EXPLICIT unrebuilt premise, and the
    conclusion is ONLY positive lower density of bad starts. -/
theorem v158_amplify_any_zero_tail_live_bad
    (hAmp : V150PredecessorAmplifier)
    (s : State) (hs : ZeroTailLive s)
    (hBad : PositiveBad (endpoint s)) :
    ∃ q X0 : Nat, 0<q ∧
      ∀ X : Nat, X0≤X → X≤q*v150BadCount X := by
  obtain ⟨q,X0,hq,hLower⟩ :=
    hAmp (endpoint s) hBad.1
      (v158_zero_tail_live_nondivisible_three s hs)
  refine ⟨q,X0,hq,?_⟩
  intro X hx
  have hSub :=
    v150_bad_target_predecessors_counted_as_bad
      (endpoint s) X hBad
  exact Nat.le_trans (hLower X hx)
    (Nat.mul_le_mul_left q hSub)

#print axioms v158_three_target_only_even_predecessor
#print axioms v158_three_target_pure_even_ancestry
#print axioms v158_divisible_three_endpoint_iff_source
#print axioms v158_after_source_bits_nondivisible_three
#print axioms v158_reachable_zero_tail_nondivisible_three
#print axioms v158_zero_tail_live_nondivisible_three
#print axioms v158_amplify_any_zero_tail_live_bad

end SourceProduct
end CollatzFinal
