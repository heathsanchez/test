import Collatz.SourceThreeReverseRoot
import Collatz.CylinderCoalescence

namespace CollatzFinal

/-!
V126. Source-normalize the protected future coalescence relation to
positive multiples of three, with a finite <=6 *actual shortcut clock*
from the chosen source to an arbitrary positive target.

Critical epistemic distinction:
  root -> n is future-class IDENTITY, not a strictly-smaller-source
  certificate. The chosen 3-root can be MUCH LARGER than n.

Do not insert this normalization as a lower-source merger into the
V124 typed research controller. Universal Collatz remains UNKNOWN.
-/

/-- One minimum semantic constructor, all-offset sound: if a base
has one odd shortcut step in the first k positions and T^k(base)=r,
then its lift by 3*2^k*t lands at r+9*t. -/
private theorem root_consequence_affine
    (base k r t : Nat)
    (ht : iter shortcut k base = r)
    (ho : SourceProduct.oddCount base k = 1) :
    iter shortcut k (base + 3 * 2 ^ k * t) = r + 9 * t := by
  have h := SourceProduct.parity_cylinder_shift base k (3 * t)
  rw [ht, ho] at h
  have heq : base + 3 * 2 ^ k * t = base + 2 ^ k * (3 * t) := by
    simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
  calc
    iter shortcut k (base + 3 * 2 ^ k * t) =
      iter shortcut k (base + 2 ^ k * (3 * t)) := by rw [heq]
    _ = r + 3 * (3 * t) := by simpa only [pow_one] using h
    _ = r + 9 * t := by omega

/-- Residue 1 modulo 9. -/
theorem root_represents_mod9_one (t : Nat) :
    iter shortcut 6 (21 + 192 * t) = 9 * t + 1 := by
  have h := root_consequence_affine 21 6 1 t (by decide) (by decide)
  have hp : (2 : Nat) ^ 6 = 64 := by decide
  rw [hp] at h
  have hs : 21 + 3 * 64 * t = 21 + 192 * t := by omega
  calc
    iter shortcut 6 (21 + 192 * t) =
      iter shortcut 6 (21 + 3 * 64 * t) := by rw [hs]
    _ = 1 + 9 * t := h
    _ = 9 * t + 1 := by omega

/-- Residue 2 modulo 9. -/
theorem root_represents_mod9_two (t : Nat) :
    iter shortcut 5 (21 + 96 * t) = 9 * t + 2 := by
  have h := root_consequence_affine 21 5 2 t (by decide) (by decide)
  have hp : (2 : Nat) ^ 5 = 32 := by decide
  rw [hp] at h
  have hs : 21 + 3 * 32 * t = 21 + 96 * t := by omega
  calc
    iter shortcut 5 (21 + 96 * t) =
      iter shortcut 5 (21 + 3 * 32 * t) := by rw [hs]
    _ = 2 + 9 * t := h
    _ = 9 * t + 2 := by omega

/-- Residue 4 modulo 9. -/
theorem root_represents_mod9_four (t : Nat) :
    iter shortcut 4 (21 + 48 * t) = 9 * t + 4 := by
  have h := root_consequence_affine 21 4 4 t (by decide) (by decide)
  have hp : (2 : Nat) ^ 4 = 16 := by decide
  rw [hp] at h
  have hs : 21 + 3 * 16 * t = 21 + 48 * t := by omega
  calc
    iter shortcut 4 (21 + 48 * t) =
      iter shortcut 4 (21 + 3 * 16 * t) := by rw [hs]
    _ = 4 + 9 * t := h
    _ = 9 * t + 4 := by omega

/-- Residue 5 modulo 9. -/
theorem root_represents_mod9_five (t : Nat) :
    iter shortcut 1 (3 + 6 * t) = 9 * t + 5 := by
  have h := root_consequence_affine 3 1 5 t (by decide) (by decide)
  have hp : (2 : Nat) ^ 1 = 2 := by decide
  rw [hp] at h
  have hs : 3 + 3 * 2 * t = 3 + 6 * t := by omega
  calc
    iter shortcut 1 (3 + 6 * t) =
      iter shortcut 1 (3 + 3 * 2 * t) := by rw [hs]
    _ = 5 + 9 * t := h
    _ = 9 * t + 5 := by omega

/-- Residue 7 modulo 9. -/
theorem root_represents_mod9_seven (t : Nat) :
    iter shortcut 2 (9 + 12 * t) = 9 * t + 7 := by
  have h := root_consequence_affine 9 2 7 t (by decide) (by decide)
  have hp : (2 : Nat) ^ 2 = 4 := by decide
  rw [hp] at h
  have hs : 9 + 3 * 4 * t = 9 + 12 * t := by omega
  calc
    iter shortcut 2 (9 + 12 * t) =
      iter shortcut 2 (9 + 3 * 4 * t) := by rw [hs]
    _ = 7 + 9 * t := h
    _ = 9 * t + 7 := by omega

/-- Residue 8 modulo 9. -/
theorem root_represents_mod9_eight (t : Nat) :
    iter shortcut 3 (21 + 24 * t) = 9 * t + 8 := by
  have h := root_consequence_affine 21 3 8 t (by decide) (by decide)
  have hp : (2 : Nat) ^ 3 = 8 := by decide
  rw [hp] at h
  have hs : 21 + 3 * 8 * t = 21 + 24 * t := by omega
  calc
    iter shortcut 3 (21 + 24 * t) =
      iter shortcut 3 (21 + 3 * 8 * t) := by rw [hs]
    _ = 8 + 9 * t := h
    _ = 9 * t + 8 := by omega

/-- Every positive natural has a positive 3-divisible ancestor
whose REAL forward trajectory reaches it in at most six shortcut steps.

This gives all positive future-coalescence classes a root representative,
but DOES NOT assert the root is smaller or yields Collatz convergence.
-/
theorem every_positive_has_bounded_three_root
    (n : Nat) (hn : 0 < n) :
    ∃ root clock : Nat, 0 < root ∧ root % 3 = 0 ∧
       clock ≤ 6 ∧ iter shortcut clock root = n := by
  have hlt : n % 9 < 9 := Nat.mod_lt n (by decide)
  have cases9 :
      n % 9 = 0 ∨ n % 9 = 1 ∨ n % 9 = 2 ∨
      n % 9 = 3 ∨ n % 9 = 4 ∨ n % 9 = 5 ∨
      n % 9 = 6 ∨ n % 9 = 7 ∨ n % 9 = 8 := by omega
  rcases cases9 with h0 | h1 | h2 | h3 | h4 | h5 | h6 | h7 | h8
  · exact ⟨n, 0, hn, by omega, by decide, rfl⟩
  · refine ⟨21 + 192 * (n / 9), 6, by omega, by omega, by decide, ?_⟩
    calc
      iter shortcut 6 (21 + 192 * (n / 9)) = 9 * (n / 9) + 1 :=
        root_represents_mod9_one _
      _ = n := by omega
  · refine ⟨21 + 96 * (n / 9), 5, by omega, by omega, by decide, ?_⟩
    calc
      iter shortcut 5 (21 + 96 * (n / 9)) = 9 * (n / 9) + 2 :=
        root_represents_mod9_two _
      _ = n := by omega
  · exact ⟨n, 0, hn, by omega, by decide, rfl⟩
  · refine ⟨21 + 48 * (n / 9), 4, by omega, by omega, by decide, ?_⟩
    calc
      iter shortcut 4 (21 + 48 * (n / 9)) = 9 * (n / 9) + 4 :=
        root_represents_mod9_four _
      _ = n := by omega
  · refine ⟨3 + 6 * (n / 9), 1, by omega, by omega, by decide, ?_⟩
    calc
      iter shortcut 1 (3 + 6 * (n / 9)) = 9 * (n / 9) + 5 :=
        root_represents_mod9_five _
      _ = n := by omega
  · exact ⟨n, 0, hn, by omega, by decide, rfl⟩
  · refine ⟨9 + 12 * (n / 9), 2, by omega, by omega, by decide, ?_⟩
    calc
      iter shortcut 2 (9 + 12 * (n / 9)) = 9 * (n / 9) + 7 :=
        root_represents_mod9_seven _
      _ = n := by omega
  · refine ⟨21 + 24 * (n / 9), 3, by omega, by omega, by decide, ?_⟩
    calc
      iter shortcut 3 (21 + 24 * (n / 9)) = 9 * (n / 9) + 8 :=
        root_represents_mod9_eight _
      _ = n := by omega

/-- An exact equivalence between the general Collatz goal and the
goal restricted to positive multiples of three. The forward direction
is trivial; the reverse uses the bounded root section and ordinary
forward invariance of the verified terminal observation.

This is a new domain-normalization result, NOT a proof of either side.
-/
theorem collatz_iff_terminates_on_three_roots :
    (∀ n : Nat, 0 < n → CollatzGood n) ↔
    (∀ m : Nat, 0 < m → CollatzGood (3 * m)) := by
  constructor
  · intro hall m hm
    exact hall (3 * m) (by omega)
  · intro hall n hn
    obtain ⟨root, clock, hp, hdiv, _hbound, hreach⟩ :=
      every_positive_has_bounded_three_root n hn
    have hroot : root = 3 * (root / 3) := by
      omega
    have hparam : 0 < root / 3 := by omega
    have hgood : CollatzGood root := by
      rw [hroot]
      exact hall (root / 3) hparam
    have hfuture : CollatzGood (iter shortcut clock root) :=
      eventually_iter_forward shortcut Terminal
        terminal_forward_invariant hgood clock
    simpa [hreach] using hfuture

#print axioms root_represents_mod9_one
#print axioms root_represents_mod9_two
#print axioms root_represents_mod9_four
#print axioms root_represents_mod9_five
#print axioms root_represents_mod9_seven
#print axioms root_represents_mod9_eight
#print axioms every_positive_has_bounded_three_root
#print axioms collatz_iff_terminates_on_three_roots

end CollatzFinal
