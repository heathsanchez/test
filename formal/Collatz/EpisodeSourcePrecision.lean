import Collatz.SourceProductAffine
import Collatz.GuardedDyadicSwitch

namespace CollatzFinal
namespace SourceProduct

/-- Exact dyadic episode anchor at a SourceProduct state.
The endpoint is written as x = 2^r * m - 1 with odd owner m. -/
def EpisodeAnchor (s : State) (r m : Nat) : Prop :=
  endpoint s + 1 = 2 ^ r * m ∧ m % 2 = 1

/-- Every state has an exact dyadic decomposition of endpoint+1. -/
theorem episodeAnchor_exists (s : State) :
    ∃ r m, EpisodeAnchor s r m := by
  obtain ⟨r, m, hm, hodd⟩ :=
    nat_dyadic_decomposition (endpoint s + 1) (by omega)
  exact ⟨r, m, hm, hodd⟩

/-- Reachability transports the exact affine source/orbit equation from
stateAt to an arbitrary SourceProduct state. -/
theorem reachable_exact_affine
    {s : State} (hs : Reachable s) :
    2 ^ s.depth * endpoint s =
      3 ^ s.odds * s.source + bias s.source s.depth := by
  obtain ⟨n, k, hn, rfl⟩ := hs
  simpa only [at_depth, at_endpoint, at_odds, at_source] using
    exact_affine n k

/-- An episode anchor at depth k is an exact source-congruence certificate at
dyadic precision k+r.

If endpoint+1 = 2^r*m, multiplying by the already exposed source depth 2^k
and using the all-depth affine orbit identity gives:
  2^(k+r) * m = 3^q * source + bias(source,k) + 2^k.

Thus an episode anchor is not merely local trajectory syntax: it constrains the
original source modulo a strictly deeper dyadic modulus. -/
theorem episode_anchor_source_equation
    {s : State} {r m : Nat}
    (hs : Reachable s)
    (ha : EpisodeAnchor s r m) :
    2 ^ (s.depth + r) * m =
      3 ^ s.odds * s.source + bias s.source s.depth + 2 ^ s.depth := by
  have hAff := reachable_exact_affine hs
  calc
    2 ^ (s.depth + r) * m
        = 2 ^ s.depth * (2 ^ r * m) := by
            simp [Nat.pow_add, Nat.mul_assoc]
    _ = 2 ^ s.depth * (endpoint s + 1) := by
          rw [← ha.1]
    _ = 2 ^ s.depth * endpoint s + 2 ^ s.depth := by
          simp [Nat.mul_add]
    _ = 3 ^ s.odds * s.source + bias s.source s.depth + 2 ^ s.depth := by
          rw [hAff]

/-- The corresponding modulus divides the source-side affine numerator.
This is the source-precision fact consumed by later refinement machinery. -/
theorem episode_anchor_source_mod_zero
    {s : State} {r m : Nat}
    (hs : Reachable s)
    (ha : EpisodeAnchor s r m) :
    (3 ^ s.odds * s.source + bias s.source s.depth + 2 ^ s.depth) %
        2 ^ (s.depth + r) = 0 := by
  rw [← episode_anchor_source_equation hs ha]
  simp

/-- Name the certified dyadic precision carried by an episode anchor. -/
def episodePrecision (s : State) (r : Nat) : Nat :=
  s.depth + r

/-- The exact equation can be stated directly at the named precision. -/
theorem episode_precision_source_equation
    {s : State} {r m : Nat}
    (hs : Reachable s)
    (ha : EpisodeAnchor s r m) :
    2 ^ episodePrecision s r * m =
      3 ^ s.odds * s.source + bias s.source s.depth + 2 ^ s.depth := by
  exact episode_anchor_source_equation hs ha

#print axioms episodeAnchor_exists
#print axioms reachable_exact_affine
#print axioms episode_anchor_source_equation
#print axioms episode_anchor_source_mod_zero
#print axioms episode_precision_source_equation

end SourceProduct
end CollatzFinal
