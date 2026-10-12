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
    (hBase : 0 < base)
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

#check packed_digit_mod
#check packed_digit_div
#check packed_quotient_digit
#print axioms packed_digit_mod
#print axioms packed_digit_div
#print axioms packed_quotient_digit

end Submission
