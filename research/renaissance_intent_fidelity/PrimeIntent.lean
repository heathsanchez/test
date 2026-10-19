import Mathlib

/-!
Independent mathematical-source inspired controls.
Reference: Euclid's infinitude of primes (Euclid, Elements IX.20).
The finite surrogate below is NOT that theorem and must be rejected
as an adequate formalization despite being Lean-provable.
No NLP-to-Lean automation or equal-information reviewer advantage is claimed.
-/

-- Actual mathematical target (standard mathlib theorem):
example : Set.Infinite {p : ℕ | Nat.Prime p} := by
  exact Nat.infinite_setOf_prime

-- An easily proved but semantically inadequate substitute:
theorem wrongFiniteSurrogate : ∃ p : ℕ, Nat.Prime p := by
  exact ⟨2, Nat.prime_two⟩

-- A finite positive check cannot establish an infinite mathematical claim.
-- Both propositions are true, but they differ in logical strength.
theorem infiniteImpliesExists :
    Set.Infinite {p : ℕ | Nat.Prime p} → ∃ p : ℕ, Nat.Prime p := by
  intro h
  by_contra hn
  have hempty : {p : ℕ | Nat.Prime p} = ∅ := by
    ext p
    simp only [Set.mem_setOf_eq, Set.mem_empty_iff_false, iff_false]
    exact fun hp => hn ⟨p, hp⟩
  rw [hempty] at h
  exact Set.not_infinite_empty h
