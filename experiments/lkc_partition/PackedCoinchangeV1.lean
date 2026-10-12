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




/-!
# Universal additive partition recurrence, from locked SAIR partAux

No generating-function assumption, no input-specific answer data, no holes.
This is the missing source-side recurrence needed for proving that a
formal product of geometric factors supplies the same coefficient family.

It is NOT an impl_correct proof for the Euler packed solver.
-/

def sumFold (q : Nat) (f : Nat → Nat) : Nat :=
  Nat.fold q (fun i _ acc => acc + f i) 0

theorem sumFold_succ (q : Nat) (f : Nat → Nat) :
    sumFold (q + 1) f = sumFold q f + f q := by
  rfl

theorem sumFold_shift :
    ∀ q (f : Nat → Nat),
      sumFold (q + 1) f = f 0 + sumFold q (fun j => f (j + 1))
  | 0, f => by
      simp [sumFold, Nat.fold]
  | q + 1, f => by
      rw [sumFold_succ, sumFold_shift q f, sumFold_succ]
      simp [Nat.add_assoc]

theorem sumFold_congr :
    ∀ q (f g : Nat → Nat),
      (∀ i, i < q → f i = g i) →
      sumFold q f = sumFold q g
  | 0, f, g, _ => rfl
  | q + 1, f, g, h => by
      rw [sumFold_succ, sumFold_succ]
      rw [sumFold_congr q f g (fun i hi => h i (by omega))]
      rw [h q (by omega)]

theorem natFold_sum_eq_list (f : Nat → Nat) :
    ∀ q, Nat.fold q (fun i _ acc => acc + f i) 0 =
      ((List.range q).map f).foldl (· + ·) 0
  | 0 => rfl
  | q + 1 => by
      rw [Nat.fold_succ, List.range_succ, List.map_append, List.foldl_append]
      simp only [List.map, List.foldl_cons, List.foldl_nil]
      rw [natFold_sum_eq_list f q]

theorem sumFold_eq_list (q : Nat) (f : Nat → Nat) :
    sumFold q f = ((List.range q).map f).foldl (· + ·) 0 := by
  exact natFold_sum_eq_list f q

/-- One formal geometric-factor action on an arbitrary sequence of values. -/
def geometricStep (step : Nat) (prev : Nat → Nat) (m : Nat) : Nat :=
  sumFold (m / step + 1)
    (fun j => prev (m - j * step))

/-- A finite geometric factor obeys the in-place coin-change recurrence. -/
theorem geometricStep_recurrence
    (step : Nat) (prev : Nat → Nat) (m : Nat) (hs : 0 < step) :
    geometricStep step prev m =
      prev m + (if step ≤ m then geometricStep step prev (m - step) else 0) := by
  by_cases hle : step ≤ m
  · rw [if_pos hle]
    unfold geometricStep
    rw [sumFold_shift]
    simp only [Nat.zero_mul, Nat.sub_zero]
    have hdiv : m / step = (m - step) / step + 1 := by
      conv => lhs
              rw [show m = (m - step) + step by omega]
      rw [Nat.add_div_right _ hs]
    rw [hdiv]
    apply congrArg (fun x => prev m + x)
    apply sumFold_congr
    intro j hj
    simp only [Nat.add_mul, Nat.one_mul, Nat.sub_sub]
    congr 1
    omega
  · rw [if_neg hle]
    have hlt : m < step := by omega
    unfold geometricStep
    rw [Nat.div_eq_of_lt hlt]
    simp [sumFold, Nat.fold]

theorem partAux_as_geometricStep (k n : Nat) :
    partAux (k + 1) n = geometricStep (k + 1) (partAux k) n := by
  change
    ((List.range (n / (k + 1) + 1)).map
      (fun j => partAux k (n - j * (k + 1)))).foldl (· + ·) 0 =
    sumFold (n / (k + 1) + 1)
      (fun j => partAux k (n - j * (k + 1)))
  exact (sumFold_eq_list _ _).symm

/-- The universal additive coin-change law derived from the locked spec.
Unlike the multiplicity-sum recurrence, this form can be realized by
multiplication by a formal geometric factor without separate summation. -/
theorem partAux_coinchange (k n : Nat) :
    partAux (k + 1) n =
      partAux k n +
        (if k + 1 ≤ n then
           partAux (k + 1) (n - (k + 1))
         else 0) := by
  calc
    partAux (k + 1) n =
        geometricStep (k + 1) (partAux k) n :=
          partAux_as_geometricStep k n
    _ = partAux k n +
          (if k + 1 ≤ n then
            geometricStep (k + 1) (partAux k) (n - (k + 1))
          else 0) :=
            geometricStep_recurrence (k + 1) (partAux k) n (by omega)
    _ = partAux k n +
          (if k + 1 ≤ n then
             partAux (k + 1) (n - (k + 1))
           else 0) := by
             rw [partAux_as_geometricStep k (n - (k + 1))]

#print axioms geometricStep_recurrence
#print axioms partAux_as_geometricStep
#print axioms partAux_coinchange


/-- Formal coefficient family of a finite product of geometric factors.
A coefficient row is constructed by repeatedly adding one allowed part size. -/
def geometricProductCoeff : Nat → Nat → Nat
  | 0, 0 => 1
  | 0, _ + 1 => 0
  | k + 1, n => geometricStep (k + 1) (geometricProductCoeff k) n

/-- Exact agreement of the factor-coefficient grammar with locked SAIR partAux,
for all part limits and all target degrees. This theorem does not yet assert
that evaluating the product numerically in radix B recovers these coefficients. -/
theorem geometricProductCoeff_eq_partAux :
    ∀ k n, geometricProductCoeff k n = partAux k n := by
  intro k
  induction k with
  | zero =>
      intro n
      cases n with
      | zero => rfl
      | succ n => rfl
  | succ k ih =>
      intro n
      change geometricStep (k + 1) (geometricProductCoeff k) n =
        partAux (k + 1) n
      rw [partAux_as_geometricStep]
      unfold geometricStep
      apply sumFold_congr
      intro j hj
      exact ih (n - j * (k + 1))

theorem geometricProductCoeff_diagonal (n : Nat) :
    geometricProductCoeff n n = partitionSpec n := by
  exact geometricProductCoeff_eq_partAux n n

#print axioms geometricProductCoeff_eq_partAux
#print axioms geometricProductCoeff_diagonal



/-- The original locked partition recurrence becomes one exact equality
of integer-encoded coefficient rows, with no coefficient bounds required.
This is a generic identity, NOT a proof of the sparse Euler quotient. -/
theorem packRow_partAux_coinchange (B k n : Nat) :
    packRow B (partAux (k + 1)) n =
      packRow B (partAux k) n +
        packRow B (shiftMany (k + 1) (partAux (k + 1))) n := by
  have hfun :
      (fun m => partAux (k + 1) m) =
        (fun m => partAux k m +
          shiftMany (k + 1) (partAux (k + 1)) m) := by
    funext m
    rw [shiftMany_spec]
    exact partAux_coinchange k m
  calc
    packRow B (partAux (k + 1)) n =
      packRow B (fun m => partAux k m +
        shiftMany (k + 1) (partAux (k + 1)) m) n :=
          congrArg (fun f : Nat → Nat => packRow B f n) hfun
    _ = packRow B (partAux k) n +
      packRow B (shiftMany (k + 1) (partAux (k + 1))) n :=
        packRow_add B (partAux k)
          (shiftMany (k + 1) (partAux (k + 1))) n

/-- Once n is at least the part size, the original recurrence is an
algebraic base-B identity: no lists or sparse Euler algorithm involved. -/
theorem packRow_partAux_factor (B k n : Nat) (hkn : k + 1 ≤ n) :
    packRow B (partAux (k + 1)) n =
      packRow B (partAux k) n +
        B ^ (k + 1) *
          packRow B (partAux (k + 1)) (n - (k + 1)) := by
  calc
    packRow B (partAux (k + 1)) n =
      packRow B (partAux k) n +
        packRow B (shiftMany (k + 1) (partAux (k + 1))) n :=
          packRow_partAux_coinchange B k n
    _ = packRow B (partAux k) n +
        B ^ (k + 1) *
          packRow B (partAux (k + 1)) (n - (k + 1)) := by
            rw [packRow_shiftMany_le B (partAux (k + 1)) (k + 1) n hkn]

#print axioms packRow_partAux_coinchange
#print axioms packRow_partAux_factor

end Submission
