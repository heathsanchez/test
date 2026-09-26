import Std

namespace CollatzFinal.CoefficientCorridor

/-- Positive remainder in the shifted sixth-power comparison. -/
def remainder (x : Nat) : Nat :=
  243*x^5 + 675*x^4 + 405*x^3 + 117*x^2 + 17*x + 1

def increment (x : Nat) : Nat :=
  1458*x^5 + 1215*x^4 + 540*x^3 + 135*x^2 + 18*x + 1

/-- Subtraction-free identity. The extra d term preserves the actual lower
    bound on the odd value, rather than forgetting its location. -/
theorem factor_identity (u d : Nat) :
    (3*(u+2+d))^6*(u+3) =
      (3*(u+2+d)+1)^6*(u+1) + remainder (u+2+d) +
        d * increment (u+2+d) := by
  unfold remainder increment
  grind

theorem factor_majorant (a x : Nat) (ha : 2 ≤ a) (hx : a ≤ x) :
    (3*x+1)^6*(a-1) < (3*x)^6*(a+1) := by
  let u := a-2
  let d := x-a
  have heA : a = u+2 := by dsimp [u]; omega
  have heX : x = u+2+d := by dsimp [u,d]; omega
  have hp : 0 < remainder (u+2+d) := by unfold remainder; omega
  have hi := factor_identity u d
  rw [heA, heX]
  have he : u+2-1 = u+1 := by omega
  rw [he]
  omega

/-- A sorted list of distinct odd values above n has this packing property.
    The sorting/orbit bridge is not asserted by this definition. -/
def Packed : Nat → List Nat → Prop
  | _, [] => True
  | n, x::xs => n ≤ x ∧ Packed (n+2) xs

def numerator : List Nat → Nat
  | [] => 1
  | x::xs => (3*x+1)^6 * numerator xs

def denominator : List Nat → Nat
  | [] => 1
  | x::xs => (3*x)^6 * denominator xs

theorem numerator_positive (xs : List Nat) : 0 < numerator xs := by
  induction xs with
  | nil => decide
  | cons x xs ih =>
      exact Nat.mul_pos (Nat.pow_pos (by omega)) ih

/-- Exact telescoping product inequality, at arbitrary list length and source.
    Empty lists give equality; nonempty lists give a strict inequality. -/
theorem packed_sixth_power (xs : List Nat) (n : Nat)
    (hn : 2 ≤ n) (hp : Packed n xs) :
    numerator xs * (n-1) ≤ denominator xs * (n+2*xs.length-1) ∧
    (xs ≠ [] → numerator xs * (n-1) <
      denominator xs * (n+2*xs.length-1)) := by
  induction xs generalizing n with
  | nil => simp [numerator, denominator]
  | cons x xs ih =>
      have hpx : n ≤ x := hp.1
      have hpr : Packed (n+2) xs := hp.2
      have hi := (ih (n+2) (by omega) hpr).1
      have hf := factor_majorant n x hn hpx
      have hs := Nat.mul_lt_mul_of_pos_left hf (numerator_positive xs)
      have hi' := Nat.mul_le_mul_left ((3*x)^6) hi
      have hb : n+2-1 = n+1 := by omega
      rw [hb] at hi'
      have hchain : (3*x+1)^6 * numerator xs * (n-1) <
          (3*x)^6 * denominator xs * (n+2+2*xs.length-1) := by
        apply Nat.lt_of_lt_of_le (b := (3*x)^6 * (numerator xs * (n+1)))
        · simpa [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm] using hs
        · simpa [Nat.mul_assoc] using hi'
      have he : n+2*(x::xs).length-1 = n+2+2*xs.length-1 := by
        simp only [List.length_cons]
        omega
      rw [he]
      change (3*x+1)^6 * numerator xs * (n-1) ≤
          (3*x)^6 * denominator xs * (n+2+2*xs.length-1) ∧ _
      exact ⟨Nat.le_of_lt hchain, fun _ => hchain⟩

#print axioms factor_identity
#print axioms factor_majorant
#print axioms packed_sixth_power

end CollatzFinal.CoefficientCorridor
