import Collatz.ActualReturnAdmission

namespace CollatzFinal
namespace SourceProduct

/-- A valid starting episode remains in the domain of V91's deterministic
next-episode constructor after every finite actual episode word. This
eliminates the need to supply an independent parity witness for the final
owner of an actual chain. -/
theorem actual_chain_endpoint_valid
    {r0 m0 r m t A B P : Nat}
    (hc : ActualEpisodeChain r0 m0 r m t A B P)
    (hr0 : 0 < r0) (hm0 : 0 < m0) (hodd0 : m0 % 2 = 1) :
    0 < r ∧ 0 < m ∧ m % 2 = 1 := by
  cases hc with
  | empty =>
      exact ⟨hr0, hm0, hodd0⟩
  | append hchain he =>
      rcases he with
        ⟨_, _, _, _, hr', hm', hodd', y, _, _, _, _⟩
      exact ⟨hr', hm', hodd'⟩

/-- Every valid starting anchor-owner pair has actual episode chains
at every requested finite horizon. The certified shortcut time is at least
the number of appended episodes (each genuine episode consumes positive
time). No finite-termination claim is inferred from this totality. -/
theorem actual_chains_exist_at_all_finite_horizons
    (r0 m0 : Nat)
    (hr0 : 0 < r0) (hm0 : 0 < m0) (hodd0 : m0 % 2 = 1) :
    ∀ k, ∃ r m t A B P : Nat,
      ActualEpisodeChain r0 m0 r m t A B P ∧
      0 < r ∧ 0 < m ∧ m % 2 = 1 ∧ k ≤ t := by
  intro k
  induction k with
  | zero =>
      exact ⟨r0, m0, 0, 1, 0, 1,
        ActualEpisodeChain.empty r0 m0,
        hr0, hm0, hodd0, by decide⟩
  | succ k ih =>
      obtain ⟨r, m, t, A, B, P, hc, hr, hm, hodd, ht⟩ := ih
      obtain ⟨s, r', m', he⟩ := naturalEpisode_exists hr hm hodd
      rcases he with
        ⟨hrIn, hmIn, hoddIn, hs, hr', hm', hodd',
         y, hy, hyodd, hmid, hend⟩
      have he : NaturalEpisode r m s r' m' :=
        ⟨hrIn, hmIn, hoddIn, hs, hr', hm', hodd',
          y, hy, hyodd, hmid, hend⟩
      refine ⟨r', m', t + r + s, 3 ^ r * A,
        3 ^ r * B + (2 ^ s - 1) * P,
        2 ^ (s + r') * P,
        ActualEpisodeChain.append hc he,
        hr', hm', hodd', ?_⟩
      omega

/-- All finite-horizon witnesses are accompanied by the exact compiled
affine law and exact shortcut trace. No Python episode simulator is involved
in either proof. -/
theorem all_finite_episode_horizons_certified
    (r0 m0 : Nat)
    (hr0 : 0 < r0) (hm0 : 0 < m0) (hodd0 : m0 % 2 = 1) :
    ∀ k, ∃ r m t A B P : Nat,
      ActualEpisodeChain r0 m0 r m t A B P ∧
      0 < r ∧ 0 < m ∧ m % 2 = 1 ∧ k ≤ t ∧
      P * m = A * m0 + B ∧
      iter shortcut t (2 ^ r0 * m0 - 1) = 2 ^ r * m - 1 := by
  intro k
  obtain ⟨r, m, t, A, B, P, hc, hr, hm, hodd, ht⟩ :=
    actual_chains_exist_at_all_finite_horizons
      r0 m0 hr0 hm0 hodd0 k
  exact ⟨r, m, t, A, B, P,
    hc, hr, hm, hodd, ht,
    actual_episode_chain_affine hc,
    actual_episode_chain_shortcut hc⟩

/-- In any actual finite episode continuation, a repeated starting anchor
automatically earns V98's admission-or-zero return certificate. The final
owner's oddness is established by the actual episode chain, not assumed. -/
theorem repeated_initial_anchor_yields_admitted_return
    {r0 m0 r m t A B P : Nat}
    (hc : ActualEpisodeChain r0 m0 r m t A B P)
    (hr0 : 0 < r0) (hm0 : 0 < m0) (hodd0 : m0 % 2 = 1)
    (ht : 0 < t)
    (hsame : r = r0) :
    ∃ q D : Nat,
      A = 3 ^ q ∧ P = 2 ^ D ∧
      (returnDefect (A : Int) (B : Int)
          ((2 : Int) ^ D) (m0 : Int) = 0 ∨
        ReturnCylinderAdmissible
          (A : Int) (B : Int) D (m0 : Int)) ∧
      P * m = A * m0 + B ∧
      iter shortcut t (2 ^ r0 * m0 - 1) =
        2 ^ r0 * m - 1 := by
  have hvalid :=
    actual_chain_endpoint_valid hc hr0 hm0 hodd0
  rcases hvalid with ⟨_, _, hodd⟩
  subst r
  exact actual_same_anchor_return_admission hc ht hodd0 hodd

/-- Exact-zero defect of a genuine same-anchor return is an actual
periodic orbit, not merely an abstract fixed point of a symbolic
return law. Importantly, it may be the legitimate terminal 1-cycle. -/
theorem actual_same_anchor_zero_defect_periodic
    {r m0 m t A B P D : Nat}
    (hc : ActualEpisodeChain r m0 r m t A B P)
    (hP : P = 2 ^ D)
    (hzero :
      returnDefect (A : Int) (B : Int)
        ((2 : Int) ^ D) (m0 : Int) = 0) :
    iter shortcut t (2 ^ r * m0 - 1) =
      2 ^ r * m0 - 1 := by
  have hAff := actual_episode_chain_affine hc
  have hEq :
      (2 : Int) ^ D * (m : Int) =
        (A : Int) * (m0 : Int) + (B : Int) := by
    have hc := congrArg (fun z : Nat => (z : Int)) hAff
    simpa [hP] using hc
  have hPne : (2 : Int) ^ D ≠ 0 :=
    Int.pow_ne_zero (by decide)
  have hmEq : (m : Int) = (m0 : Int) :=
    return_zero_defect_fixed_point
      (A : Int) (B : Int) ((2 : Int) ^ D)
      (m0 : Int) (m : Int) hPne hEq hzero
  have hmNat : m = m0 := Int.ofNat_inj.mp hmEq
  simpa [hmNat] using actual_episode_chain_shortcut hc

#print axioms actual_chain_endpoint_valid
#print axioms actual_chains_exist_at_all_finite_horizons
#print axioms all_finite_episode_horizons_certified
#print axioms repeated_initial_anchor_yields_admitted_return
#print axioms actual_same_anchor_zero_defect_periodic

end SourceProduct
end CollatzFinal
