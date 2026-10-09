import Collatz.EpisodePrecisionSeparator
import Collatz.EpisodeSourcePrecision

namespace CollatzFinal
namespace SourceProduct

/-- Multiplying both a modulus and an observed value by the same positive
factor does not change the divisibility observation. -/
theorem scaled_dvd_iff
    (a b x : Nat) (ha : 0 < a) :
    (a * b ∣ a * x) ↔ (b ∣ x) := by
  constructor
  · intro h
    obtain ⟨c, hc⟩ := h
    have heq : a * x = a * (b * c) := by
      calc
        a * x = (a * b) * c := hc
        _ = a * (b * c) := by simp [Nat.mul_assoc]
    exact ⟨c, Nat.eq_of_mul_eq_mul_left ha heq⟩
  · intro h
    obtain ⟨c, hc⟩ := h
    refine ⟨c, ?_⟩
    calc
      a * x = a * (b * c) := by rw [hc]
      _ = (a * b) * c := by simp [Nat.mul_assoc]

/-- V86's purported source-side dyadic congruence at precision H+r
is *logically equivalent*, for an actual reachable state with exact
source/orbit coupling, to the local endpoint anchor divisibility by 2^r.

The algebraically rewritten source observation is genuine but does NOT
introduce any additional protected-future information at this same state.
This theorem does not deny that future certificates may constrain a
prospectively fixed original source when they are composed coherently. -/
theorem source_modulus_iff_endpoint_anchor
    (s : State) (hs : Reachable s) (r : Nat) :
    (3 ^ s.odds * s.source +
       bias s.source s.depth + 2 ^ s.depth) %
        2 ^ (s.depth + r) = 0 ↔
      (endpoint s + 1) % 2 ^ r = 0 := by
  have hAff := reachable_exact_affine hs
  have heq :
      3 ^ s.odds * s.source + bias s.source s.depth +
        2 ^ s.depth =
          2 ^ s.depth * (endpoint s + 1) := by
    calc
      3 ^ s.odds * s.source + bias s.source s.depth +
          2 ^ s.depth =
        2 ^ s.depth * endpoint s + 2 ^ s.depth := by
          rw [hAff]
      _ = 2 ^ s.depth * (endpoint s + 1) := by
          simp [Nat.mul_add]
  rw [heq, Nat.pow_add]
  simp only [Nat.mod_eq_zero]
  exact scaled_dvd_iff (2 ^ s.depth) (2 ^ r)
    (endpoint s + 1) (Nat.pow_pos (by decide))

/-- Both directions of the observation factorization are independently
usable as a compiled capability: source-side modulo alone is not stronger
than the endpoint anchor observation. -/
theorem source_modulus_of_endpoint_anchor
    (s : State) (hs : Reachable s) (r : Nat)
    (h : (endpoint s + 1) % 2 ^ r = 0) :
    (3 ^ s.odds * s.source +
      bias s.source s.depth + 2 ^ s.depth) %
        2 ^ (s.depth + r) = 0 :=
  (source_modulus_iff_endpoint_anchor s hs r).mpr h

theorem endpoint_anchor_of_source_modulus
    (s : State) (hs : Reachable s) (r : Nat)
    (h : (3 ^ s.odds * s.source +
      bias s.source s.depth + 2 ^ s.depth) %
        2 ^ (s.depth + r) = 0) :
    (endpoint s + 1) % 2 ^ r = 0 :=
  (source_modulus_iff_endpoint_anchor s hs r).mp h

#print axioms scaled_dvd_iff
#print axioms source_modulus_iff_endpoint_anchor
#print axioms source_modulus_of_endpoint_anchor
#print axioms endpoint_anchor_of_source_modulus

end SourceProduct
end CollatzFinal
