import Std

namespace CollatzFinal
namespace SourceProduct

/-!
**Source-indexed affine clock rigidity.**

For two actual shortcut parity cylinders of common source modulus 2^D,
the n-branch after i steps has offset slope 2^(D-i)*3^u.
For F(n)=3n+2 the F-branch after j steps has offset slope
2^(D-j)*3^(v+1).  If the two resulting affine functions
coincide for ALL natural offsets, their slopes must agree.
Because powers of two and three have independent prime valuations,
that forces i=j.  Thus NO uniform positive-dimensional dyadic cylinder
supports a fixed unequal-clock F(n) synchronization.

This does NOT exclude isolated numerical asynchronous coalescences,
such as T(3)=T^6(11)=5; nor does it prove Collatz.
-/

private theorem three_pow_odd (u : Nat) : (3 ^ u) % 2 = 1 := by
  induction u with
  | zero => decide
  | succ u ih =>
      simp [Nat.pow_succ, Nat.mul_mod, ih]

/-- Every equality 2^i*3^u = 2^j*3^v preserves the 2-adic exponent. -/
theorem two_power_exponent_rigid :
    ∀ i j u v : Nat, 2 ^ i * 3 ^ u = 2 ^ j * 3 ^ v → i = j := by
  intro i
  induction i with
  | zero =>
      intro j u v h
      cases j with
      | zero => rfl
      | succ j =>
          have hmod := congrArg (fun x : Nat => x % 2) h
          have heven : (3 ^ u) % 2 = 0 := by
            simpa [Nat.pow_succ, Nat.mul_mod, Nat.mul_assoc,
                   Nat.mul_comm, Nat.mul_left_comm] using hmod
          have hodd := three_pow_odd u
          omega
  | succ i ih =>
      intro j u v h
      cases j with
      | zero =>
          have hmod := congrArg (fun x : Nat => x % 2) h.symm
          have heven : (3 ^ v) % 2 = 0 := by
            simpa [Nat.pow_succ, Nat.mul_mod, Nat.mul_assoc,
                   Nat.mul_comm, Nat.mul_left_comm] using hmod
          have hodd := three_pow_odd v
          omega
      | succ j =>
          have hscaled :
              2 * (2 ^ i * 3 ^ u) = 2 * (2 ^ j * 3 ^ v) := by
            simpa [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm,
                   Nat.mul_left_comm] using h
          have heq : 2 ^ i * 3 ^ u = 2 ^ j * 3 ^ v := by omega
          have he := ih j u v heq
          omega

/-- The exact arithmetic obligation for comparing the ordinary and
    F-transformed slopes at two independently chosen shortcut clocks. -/
theorem F_affine_slope_clocks_equal
    (D i j u v : Nat)
    (hi : i ≤ D) (hj : j ≤ D)
    (h : 2 ^ (D - i) * 3 ^ u = 2 ^ (D - j) * 3 ^ (v + 1)) :
    i = j := by
  have he := two_power_exponent_rigid
    (D - i) (D - j) u (v + 1) h
  omega

/-- Uniform exact affine equality for every source offset forces
    equal clocks.  This is the guard missing from an attempted
    asynchronous full-cylinder F-collision constructor. -/
theorem F_uniform_affine_meeting_clocks_equal
    (D i j u v x y : Nat)
    (hi : i ≤ D) (hj : j ≤ D)
    (h : ∀ q : Nat,
      x + (2 ^ (D - i) * 3 ^ u) * q =
      y + (2 ^ (D - j) * 3 ^ (v + 1)) * q) :
    i = j := by
  have h0 := h 0
  have h1 := h 1
  have hslope :
      2 ^ (D - i) * 3 ^ u =
      2 ^ (D - j) * 3 ^ (v + 1) := by
    simp only [Nat.mul_zero, Nat.add_zero] at h0
    simp only [Nat.mul_one] at h1
    omega
  exact F_affine_slope_clocks_equal D i j u v hi hj hslope

#print axioms two_power_exponent_rigid
#print axioms F_affine_slope_clocks_equal
#print axioms F_uniform_affine_meeting_clocks_equal

end SourceProduct
end CollatzFinal
