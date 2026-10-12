import Spec
import Init.Data.Nat.Div.Basic
import Init.Data.Nat.Div.Lemmas

namespace Submission

/-!
# Bounded radix coefficient transport
These small lemmas are the CHECKABLE algebraic interface between a
partition-number coefficient certificate and the kernel-computing
integer quotient. They make NO assumption about Euler's theorem.

The actual coefficient certificate for the partition specification
is a separate, still-unproved obligation. This file neither declares
impl_correct nor authorizes an SAIR submission.
-/

/-- A bounded least-significant digit survives a packed integer sum. -/
theorem packed_digit_mod
    (base digit high : Nat) (hDigit : digit < base) :
    (digit + base * high) % base = digit := by
  rw [Nat.add_mul_mod_self_left]
  exact Nat.mod_eq_of_lt hDigit

/-- A bounded low digit can be stripped by exact integer division. -/
theorem packed_digit_div
    (base digit high : Nat) (hBase : 0 < base) (hDigit : digit < base) :
    (digit + base * high) / base = high := by
  rw [Nat.add_mul_div_left digit high hBase]
  rw [Nat.div_eq_of_lt hDigit]
  simp

/--
If an independently verified numerator identity gives an integer
quotient consisting of high radix digits and one bounded low digit,
then the exact quotient-and-modulus computation returns that low digit.

This theorem does NOT establish the required numerator identity.
-/
theorem packed_quotient_digit
    (base divisor high digit remainder numerator : Nat)
    (_hBase : 0 < base)
    (hDivisor : 0 < divisor)
    (hDigit : digit < base)
    (hRem : remainder < divisor)
    (hCertificate :
      numerator = divisor * (base * high + digit) + remainder) :
    (numerator / divisor) % base = digit := by
  rw [hCertificate]
  rw [Nat.add_comm (divisor * (base * high + digit)) remainder]
  rw [Nat.mul_comm divisor (base * high + digit)]
  rw [Nat.add_mul_div_right remainder (base * high + digit) hDivisor]
  rw [Nat.div_eq_of_lt hRem]
  simp only [Nat.zero_add]
  rw [Nat.add_comm (base * high) digit]
  exact packed_digit_mod base digit high hDigit


/-- Exact geometric expansion with a *natural-number* invariant.
Useful for replacing a denominator 2^k-1 with a finite polynomial
without invoking any infinite-series or analytic axioms. -/
def radixGeometric (base : Nat) : Nat → Nat
  | 0 => 0
  | count + 1 => base * radixGeometric base count + 1

theorem radix_geometric_factor (base count : Nat) (hBase : 0 < base) :
    (base - 1) * radixGeometric base count + 1 = base ^ count := by
  induction count with
  | zero =>
      simp [radixGeometric]
  | succ count ih =>
      change
        (base - 1) * (base * radixGeometric base count + 1) + 1 =
          base ^ (count + 1)
      have hb : base - 1 + 1 = base := by omega
      calc
        (base - 1) * (base * radixGeometric base count + 1) + 1
            = base * ((base - 1) * radixGeometric base count + 1) := by
                calc
                  _ = base * ((base - 1) * radixGeometric base count)
                        + ((base - 1) + 1) := by
                          simp only [Nat.mul_add, Nat.mul_one]
                          ac_rfl
                  _ = base * ((base - 1) * radixGeometric base count)
                        + base := by rw [hb]
                  _ = base * ((base - 1) * radixGeometric base count + 1) := by
                        rw [Nat.mul_add, Nat.mul_one]
        _ = base * base ^ count := by rw [ih]
        _ = base ^ (count + 1) := by rw [Nat.pow_add_one]; ac_rfl


/-- The exact natural geometric quotient: no rationals or infinite sums.
This is a reusable sub-identity in the packed partition product formula. -/
theorem radix_geometric_div (base count : Nat) (hBase : 1 < base) :
    (base ^ count - 1) / (base - 1) = radixGeometric base count := by
  have hPositive : 0 < base - 1 := by omega
  have hFactor := radix_geometric_factor base count (by omega)
  have hMul :
      (base - 1) * radixGeometric base count = base ^ count - 1 := by
    omega
  calc
    (base ^ count - 1) / (base - 1)
        = ((base - 1) * radixGeometric base count) / (base - 1) := by
            rw [hMul]
    _ = radixGeometric base count :=
          Nat.mul_div_cancel_left (radixGeometric base count) hPositive

#check radix_geometric_div
#print axioms radix_geometric_div

#check radix_geometric_factor
#print axioms radix_geometric_factor

#check packed_digit_mod
#check packed_digit_div
#check packed_quotient_digit
#print axioms packed_digit_mod
#print axioms packed_digit_div
#print axioms packed_quotient_digit

end Submission
