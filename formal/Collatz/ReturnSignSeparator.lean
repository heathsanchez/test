import Collatz.SourceCappedReturn

namespace CollatzFinal
namespace SourceProduct

/-- Actual episode from shortcut 5 to shortcut 1:
  5 --odd--> 8 --even--> 4 --even--> 2 --even--> 1.
The canonical anchor is 1 at both ends; its odd owner drops 3 → 1. -/
theorem five_to_one_natural_episode :
    NaturalEpisode 1 3 3 1 1 := by
  unfold NaturalEpisode
  refine ⟨by decide, by decide, by decide, by decide,
    by decide, by decide, by decide, 1,
    by decide, by decide, by decide, by decide⟩

theorem five_to_one_actual_chain :
    ActualEpisodeChain 1 3 1 1 4 3 7 16 := by
  simpa using
    (ActualEpisodeChain.append
      (ActualEpisodeChain.empty 1 3)
      five_to_one_natural_episode)

theorem five_to_one_actual_shortcut :
    iter shortcut 4 5 = 1 := by
  simpa using actual_episode_chain_shortcut five_to_one_actual_chain

/-- Exact 2-adic cylinder admission for the real 5 → 1 return:
Delta(3) = (16 - 3)*3 - 7 = +32 = 2^5. -/
theorem five_to_one_admitted_nonzero :
    ReturnCylinderAdmissible 3 7 4 3 := by
  unfold ReturnCylinderAdmissible DyadicOrder returnDefect
  exact ⟨5, by decide, 1, by decide, by decide⟩

theorem five_to_one_return_descends :
    (1 : Nat) < 3 := by decide

/-- First actual episode of 9:
9 -> 14 -> 7, with anchor 1 / odd owner 5
switching to anchor 3 / odd owner 1. -/
theorem nine_to_seven_natural_episode :
    NaturalEpisode 1 5 1 3 1 := by
  unfold NaturalEpisode
  refine ⟨by decide, by decide, by decide, by decide,
    by decide, by decide, by decide, 7,
    by decide, by decide, by decide, by decide⟩

/-- Second actual episode:
7 -> 11 -> 17 -> 26 -> 13,
switching back to anchor 1 / odd owner 7. -/
theorem seven_to_thirteen_natural_episode_v106 :
    NaturalEpisode 3 1 1 1 7 := by
  unfold NaturalEpisode
  refine ⟨by decide, by decide, by decide, by decide,
    by decide, by decide, by decide, 13,
    by decide, by decide, by decide, by decide⟩

/-- Their real six-shortcut-step composition is the precise first
same-anchor return from x=9 to x=13:
  affine law 64*7 = 81*5 + 43. -/
theorem nine_to_thirteen_actual_chain :
    ActualEpisodeChain 1 5 1 7 6 81 43 64 := by
  have hfirst :
      ActualEpisodeChain 1 5 3 1 2 3 1 16 := by
    simpa using
      (ActualEpisodeChain.append
        (ActualEpisodeChain.empty 1 5)
        nine_to_seven_natural_episode)
  simpa using
    (ActualEpisodeChain.append
      hfirst seven_to_thirteen_natural_episode_v106)

theorem nine_to_thirteen_actual_shortcut :
    iter shortcut 6 9 = 13 := by
  simpa using actual_episode_chain_shortcut nine_to_thirteen_actual_chain

/-- Exact 2-adic cylinder admission for the real 9 → 13 return:
Delta(5) = (64 - 81)*5 - 43 = -128 = 2^7*(-1).
The odd cofactor -1 has residue 1 modulo 2. -/
theorem nine_to_thirteen_admitted_nonzero :
    ReturnCylinderAdmissible 81 43 6 5 := by
  unfold ReturnCylinderAdmissible DyadicOrder returnDefect
  exact ⟨7, by decide, -1, by decide, by decide⟩

theorem nine_to_thirteen_return_ascends :
    (5 : Nat) < 7 := by decide

/-- A monotonic-descent rule on *all genuine, cylinder-admitted,
nonzero, same-anchor actual return words* is mathematically false,
even though V105 proves an appropriately source-capped
minimal-bad return cannot descend. -/
theorem universal_admitted_actual_return_descent_false :
    ¬ (∀ (r m0 m1 t A B P D : Nat),
      0 < t →
      ActualEpisodeChain r m0 r m1 t A B P →
      P = 2 ^ D →
      ReturnCylinderAdmissible
        (A : Int) (B : Int) D (m0 : Int) →
      m1 < m0) := by
  intro hall
  have hcontra := hall 1 5 7 6 81 43 64 6
    (by decide) nine_to_thirteen_actual_chain
    (by decide) nine_to_thirteen_admitted_nonzero
  omega

/-- Conversely, a monotonic-ascent rule on all genuine,
cylinder-admitted actual returns is false as well. The sign of
the affine-return defect remains a consequential distinction. -/
theorem universal_admitted_actual_return_ascent_false :
    ¬ (∀ (r m0 m1 t A B P D : Nat),
      0 < t →
      ActualEpisodeChain r m0 r m1 t A B P →
      P = 2 ^ D →
      ReturnCylinderAdmissible
        (A : Int) (B : Int) D (m0 : Int) →
      m0 < m1) := by
  intro hall
  have hcontra := hall 1 3 1 4 3 7 16 4
    (by decide) five_to_one_actual_chain
    (by decide) five_to_one_admitted_nonzero
  omega

#print axioms five_to_one_actual_chain
#print axioms five_to_one_actual_shortcut
#print axioms five_to_one_admitted_nonzero
#print axioms nine_to_thirteen_actual_chain
#print axioms nine_to_thirteen_actual_shortcut
#print axioms nine_to_thirteen_admitted_nonzero
#print axioms universal_admitted_actual_return_descent_false
#print axioms universal_admitted_actual_return_ascent_false

end SourceProduct
end CollatzFinal
