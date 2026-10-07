import Collatz.GuardedDyadicSwitch

namespace CollatzFinal
namespace SourceProduct

/-- Exact algebraic episode relation used by the executable return grammar.

An odd episode start is x = 2^r*m - 1 with odd positive owner m.
After r odd shortcut steps, the even value 3^r*m - 1 is stripped by s powers
of two to the next odd episode start y = 2^r'*m' - 1.

The relation stores exactly those two dyadic decompositions and nothing about
a finite corpus or return-law bank. -/
def AlgebraicEpisode
    (r : Nat) (m : Int)
    (s r' : Nat) (m' : Int) : Prop :=
  0 < r ∧ 0 < m ∧ m % 2 = 1 ∧
  0 < s ∧ 0 < r' ∧ 0 < m' ∧ m' % 2 = 1 ∧
  ∃ y : Int,
    0 < y ∧ y % 2 = 1 ∧
    (3 : Int) ^ r * m - 1 = (2 : Int) ^ s * y ∧
    y + 1 = (2 : Int) ^ r' * m'

/-- One algebraic episode is the exact affine owner transition used by the
Python certificate compiler:
  2^(s+r') m' = 3^r m + (2^s - 1).
-/
theorem algebraicEpisode_affine
    {r s r' : Nat} {m m' : Int}
    (h : AlgebraicEpisode r m s r' m') :
    (2 : Int) ^ (s + r') * m' =
      (3 : Int) ^ r * m + ((2 : Int) ^ s - 1) := by
  rcases h with ⟨_, _, _, _, _, _, _, y, _, _, hmid, hend⟩
  calc
    (2 : Int) ^ (s + r') * m'
        = (2 : Int) ^ s * ((2 : Int) ^ r' * m') := by
            rw [Int.pow_add, Int.mul_assoc]
    _ = (2 : Int) ^ s * (y + 1) := by rw [← hend]
    _ = (2 : Int) ^ s * y + (2 : Int) ^ s := by
          simp [Int.mul_add]
    _ = ((3 : Int) ^ r * m - 1) + (2 : Int) ^ s := by
          rw [← hmid]
    _ = (3 : Int) ^ r * m + ((2 : Int) ^ s - 1) := by
          omega

/-- The episode decomposition is functional.

For a fixed incoming anchor/owner (r,m), exact dyadic-order uniqueness first
forces the even-run depth s, then the intermediate odd owner y, then the next
anchor r' and owner m'. -/
theorem algebraicEpisode_functional
    {r s₁ s₂ r₁ r₂ : Nat}
    {m m₁ m₂ : Int}
    (h₁ : AlgebraicEpisode r m s₁ r₁ m₁)
    (h₂ : AlgebraicEpisode r m s₂ r₂ m₂) :
    s₁ = s₂ ∧ r₁ = r₂ ∧ m₁ = m₂ := by
  rcases h₁ with
    ⟨_, _, _, _, _, _, hm₁odd, y₁, _, hy₁odd, hmid₁, hend₁⟩
  rcases h₂ with
    ⟨_, _, _, _, _, _, hm₂odd, y₂, _, hy₂odd, hmid₂, hend₂⟩
  have hsOrd₁ :
      DyadicOrder ((3 : Int) ^ r * m - 1) s₁ :=
    ⟨y₁, hmid₁, hy₁odd⟩
  have hsOrd₂ :
      DyadicOrder ((3 : Int) ^ r * m - 1) s₂ :=
    ⟨y₂, hmid₂, hy₂odd⟩
  have hs : s₁ = s₂ := dyadic_order_unique hsOrd₁ hsOrd₂
  subst s₂
  have hyMul :
      (2 : Int) ^ s₁ * y₁ = (2 : Int) ^ s₁ * y₂ :=
    hmid₁.symm.trans hmid₂
  have hy : y₁ = y₂ := by
    exact Int.eq_of_mul_eq_mul_left
      (Int.pow_ne_zero (by decide)) hyMul
  subst y₂
  have hrOrd₁ : DyadicOrder (y₁ + 1) r₁ :=
    ⟨m₁, hend₁, hm₁odd⟩
  have hrOrd₂ : DyadicOrder (y₁ + 1) r₂ :=
    ⟨m₂, hend₂, hm₂odd⟩
  have hr : r₁ = r₂ := dyadic_order_unique hrOrd₁ hrOrd₂
  subst r₂
  have hmMul :
      (2 : Int) ^ r₁ * m₁ = (2 : Int) ^ r₁ * m₂ :=
    hend₁.symm.trans hend₂
  have hm : m₁ = m₂ := by
    exact Int.eq_of_mul_eq_mul_left
      (Int.pow_ne_zero (by decide)) hmMul
  exact ⟨rfl, rfl, hm⟩

/-- Functional form on the next episode state, hiding the internal even-run
depth. -/
def EpisodeNextRel
    (a b : Nat × Int) : Prop :=
  ∃ s, AlgebraicEpisode a.1 a.2 s b.1 b.2

theorem episodeNextRel_functional
    {a b c : Nat × Int}
    (hab : EpisodeNextRel a b)
    (hac : EpisodeNextRel a c) :
    b = c := by
  rcases hab with ⟨s₁, h₁⟩
  rcases hac with ⟨s₂, h₂⟩
  have h := algebraicEpisode_functional h₁ h₂
  rcases a with ⟨r,m⟩
  rcases b with ⟨rb,mb⟩
  rcases c with ⟨rc,mc⟩
  simp only at h₁ h₂ h
  rcases h with ⟨_, hr, hm⟩
  simp [hr, hm]

#print axioms algebraicEpisode_affine
#print axioms algebraicEpisode_functional
#print axioms episodeNextRel_functional

end SourceProduct
end CollatzFinal
