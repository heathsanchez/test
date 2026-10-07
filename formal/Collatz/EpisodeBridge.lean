import Collatz.ActualEpisode

namespace CollatzFinal
namespace SourceProduct

/-- Casting a positive natural to Int preserves strict positivity. -/
theorem nat_pos_int {n : Nat} (h : 0 < n) : (0 : Int) < (n : Int) := by
  omega

/-- Casting an odd natural to Int preserves the mod-2 witness. -/
theorem nat_odd_int {n : Nat} (h : n % 2 = 1) :
    (n : Int) % 2 = 1 := by
  have hf : n = 2 * (n / 2) + 1 := by
    have hd := Nat.mod_add_div n 2
    omega
  rw [hf]
  simp

/-- V91's natural episode is exactly V90's integer algebraic episode. -/
theorem naturalEpisode_to_algebraic
    {r m s r' m' : Nat}
    (h : NaturalEpisode r m s r' m') :
    AlgebraicEpisode r (m : Int) s r' (m' : Int) := by
  rcases h with
    ⟨hr, hm, hmodd, hs, hr', hm', hm'odd, y,
      hy, hyodd, hmid, hend⟩
  refine ⟨hr, nat_pos_int hm, nat_odd_int hmodd,
    hs, hr', nat_pos_int hm', nat_odd_int hm'odd,
    (y : Int), nat_pos_int hy, nat_odd_int hyodd, ?_, ?_⟩
  · have hc := congrArg (fun z : Nat => (z : Int)) hmid
    simp at hc
    omega
  · have hc := congrArg (fun z : Nat => (z : Int)) hend
    simpa using hc

/-- Every actual positive odd anchor-owner pair therefore produces an actual
V90 algebraic episode whose endpoint is reached by the shortcut orbit. -/
theorem actual_algebraic_episode_exists
    {r m : Nat}
    (hr : 0 < r) (hm : 0 < m) (hmodd : m % 2 = 1) :
    ∃ s r' m',
      AlgebraicEpisode r (m : Int) s r' (m' : Int) ∧
      iter shortcut (r + s) (2 ^ r * m - 1) =
        2 ^ r' * m' - 1 := by
  obtain ⟨s, r', m', hnat, hactual⟩ :=
    actual_next_episode_exists hr hm hmodd
  exact ⟨s, r', m', naturalEpisode_to_algebraic hnat, hactual⟩

/-- The algebraic successor produced from an actual anchor-owner pair is unique.
This joins V91 existence/soundness with V90 functionality. -/
theorem actual_algebraic_episode_unique
    {r m s₁ s₂ r₁ r₂ : Nat}
    {m₁ m₂ : Nat}
    (h₁ : AlgebraicEpisode r (m : Int) s₁ r₁ (m₁ : Int))
    (h₂ : AlgebraicEpisode r (m : Int) s₂ r₂ (m₂ : Int)) :
    s₁ = s₂ ∧ r₁ = r₂ ∧ m₁ = m₂ := by
  have h := algebraicEpisode_functional h₁ h₂
  rcases h with ⟨hs, hr, hm⟩
  have hmnat : m₁ = m₂ := by
    exact Int.ofNat_inj.mp hm
  exact ⟨hs, hr, hmnat⟩

#print axioms nat_odd_int
#print axioms naturalEpisode_to_algebraic
#print axioms actual_algebraic_episode_exists
#print axioms actual_algebraic_episode_unique

end SourceProduct
end CollatzFinal
