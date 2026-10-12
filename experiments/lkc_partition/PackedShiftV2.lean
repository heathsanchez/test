import Spec
import Init.Data.Nat.Div.Basic
import Init.Data.Nat.Div.Lemmas

namespace Submission

/-!
# Positional coefficient packing into a natural number
This is the no-carry half of a future proof relating exact generating
polynomials to SAIR partitionSpec. It contains NO partition answers.

The arithmetic lemmas are universal in B, f and n. Their next application
will take f to be the coefficient function of the product of geometric factors.
The generating-function identity is NOT assumed or proved in this file.
-/

/-- A polynomial prefix in base B, represented directly as natural arithmetic.
The source recurrence is deliberately independent of partitionSpec. -/
def packRow (B : Nat) (f : Nat → Nat) : Nat → Nat
  | 0 => f 0
  | n + 1 => packRow B f n + B ^ (n + 1) * f (n + 1)

/-- A packed prefix with digits below B fits into its allocated radix width. -/
theorem packRow_lt_pow (B : Nat) (f : Nat → Nat) (n : Nat)
    (_hB : 0 < B)
    (hdigits : ∀ i, i ≤ n → f i < B) :
    packRow B f n < B ^ (n + 1) := by
  induction n with
  | zero =>
      simpa [packRow] using hdigits 0 (by omega)
  | succ n ih =>
      have hPrev : packRow B f n < B ^ (n + 1) :=
        ih (fun i hi => hdigits i (by omega))
      have hLast : f (n + 1) < B := hdigits (n + 1) (by omega)
      have hStep : f (n + 1) + 1 ≤ B := by omega
      calc
        packRow B f (n + 1) =
            packRow B f n + B ^ (n + 1) * f (n + 1) := rfl
        _ < B ^ (n + 1) + B ^ (n + 1) * f (n + 1) :=
              Nat.add_lt_add_right hPrev _
        _ = B ^ (n + 1) * (f (n + 1) + 1) := by
              simp only [Nat.mul_add, Nat.mul_one]
              omega
        _ ≤ B ^ (n + 1) * B := Nat.mul_le_mul_left _ hStep
        _ = B ^ (n + 1 + 1) :=
              (Nat.pow_add_one B (n + 1)).symm

/-- The topmost coefficient can be extracted by division and modulus.
This follows from radix digit boundedness; no evaluation shortcuts are used. -/
theorem packRow_digit_top (B : Nat) (f : Nat → Nat) (n : Nat)
    (hB : 0 < B)
    (hdigits : ∀ i, i ≤ n → f i < B) :
    (packRow B f n / B ^ n) % B = f n := by
  cases n with
  | zero =>
      simpa [packRow] using Nat.mod_eq_of_lt (hdigits 0 (by omega))
  | succ n =>
      have hp : 0 < B ^ (n + 1) := Nat.pow_pos hB
      have hPrefix : packRow B f n < B ^ (n + 1) :=
        packRow_lt_pow B f n hB (fun i hi => hdigits i (by omega))
      have hLast : f (n + 1) < B := hdigits (n + 1) (by omega)
      change
        ((packRow B f n + B ^ (n + 1) * f (n + 1)) / B ^ (n + 1)) % B =
          f (n + 1)
      rw [Nat.add_mul_div_left _ _ hp]
      rw [Nat.div_eq_of_lt hPrefix]
      simp only [Nat.zero_add]
      exact Nat.mod_eq_of_lt hLast

#print axioms packRow_lt_pow
#print axioms packRow_digit_top


/-- Universal additive homomorphism for evaluated finite coefficient rows. -/
theorem packRow_add (B : Nat) (f g : Nat → Nat) :
    ∀ n, packRow B (fun i => f i + g i) n =
      packRow B f n + packRow B g n
  | 0 => rfl
  | n + 1 => by
      change
        packRow B (fun i => f i + g i) n +
          B ^ (n + 1) * (f (n + 1) + g (n + 1)) =
        (packRow B f n + B ^ (n + 1) * f (n + 1)) +
          (packRow B g n + B ^ (n + 1) * g (n + 1))
      rw [packRow_add B f g n, Nat.mul_add]
      ac_rfl

/-- Scaling coefficients commutes with the integer positional encoding. -/
theorem packRow_scale (B c : Nat) (f : Nat → Nat) :
    ∀ n, packRow B (fun i => c * f i) n = c * packRow B f n
  | 0 => rfl
  | n + 1 => by
      change
        packRow B (fun i => c * f i) n + B ^ (n + 1) * (c * f (n + 1)) =
          c * (packRow B f n + B ^ (n + 1) * f (n + 1))
      rw [packRow_scale B c f n, Nat.mul_add]
      ac_rfl

def shiftOne (f : Nat → Nat) : Nat → Nat
  | 0 => 0
  | n + 1 => f n

/-- Exact coefficient shift by one degree is multiplication by the base,
before truncation. It is an equality of natural numbers, not a heuristic. -/
theorem packRow_shiftOne (B : Nat) (f : Nat → Nat) :
    ∀ n, packRow B (shiftOne f) (n + 1) = B * packRow B f n
  | 0 => by
      simp [packRow, shiftOne]
  | n + 1 => by
      change
        packRow B (shiftOne f) (n + 1) +
          B ^ ((n + 1) + 1) * f (n + 1) =
        B * (packRow B f n + B ^ (n + 1) * f (n + 1))
      rw [packRow_shiftOne B f n, Nat.mul_add]
      have he : B ^ ((n + 1) + 1) = B * B ^ (n + 1) := by
        rw [Nat.pow_add_one]
        ac_rfl
      rw [he]
      ac_rfl

#print axioms packRow_add
#print axioms packRow_scale
#print axioms packRow_shiftOne


/-- Mathematical shift by k degrees, independent of any particular polynomial. -/
def shiftMany : Nat → (Nat → Nat) → Nat → Nat
  | 0, f => f
  | k + 1, f => shiftOne (shiftMany k f)

/-- A shifted coefficient is identically zero below the shift degree. -/
theorem shiftMany_spec (f : Nat → Nat) :
    ∀ k n, shiftMany k f n =
      if k ≤ n then f (n - k) else 0 := by
  intro k
  induction k with
  | zero =>
      intro n
      simp [shiftMany]
  | succ k ih =>
      intro n
      cases n with
      | zero =>
          simp [shiftMany, shiftOne]
      | succ n =>
          change shiftMany k f n =
            if k + 1 ≤ n + 1 then f (n + 1 - (k + 1)) else 0
          rw [ih n]
          by_cases h : k ≤ n
          · have h' : k + 1 ≤ n + 1 := by omega
            simp only [if_pos h, if_pos h']
            congr 1
            omega
          · have h' : ¬ k + 1 ≤ n + 1 := by omega
            simp only [if_neg h, if_neg h']

/-- A universal k-degree shift is exact radix multiplication on complete
coefficient-prefix rows; no coefficient bound is required for this equality. -/
theorem packRow_shiftMany (B : Nat) (f : Nat → Nat) :
    ∀ k n, packRow B (shiftMany k f) (n + k) =
      B ^ k * packRow B f n := by
  intro k
  induction k with
  | zero =>
      intro n
      simp [shiftMany]
  | succ k ih =>
      intro n
      have h := packRow_shiftOne B (shiftMany k f) (n + k)
      change
        packRow B (shiftOne (shiftMany k f)) (n + k + 1) =
          B ^ (k + 1) * packRow B f n
      rw [h, ih n]
      rw [Nat.pow_add_one]
      ac_rfl

/-- For a prefix n beyond the shift degree, the full shifted row is obtained
by multiplying the truncated unshifted row by an exact power of the radix. -/
theorem packRow_shiftMany_le (B : Nat) (f : Nat → Nat)
    (k n : Nat) (hk : k ≤ n) :
    packRow B (shiftMany k f) n =
      B ^ k * packRow B f (n - k) := by
  have h := packRow_shiftMany B f k (n - k)
  have he : n - k + k = n := by omega
  simpa only [he] using h

#print axioms shiftMany_spec
#print axioms packRow_shiftMany
#print axioms packRow_shiftMany_le

end Submission
