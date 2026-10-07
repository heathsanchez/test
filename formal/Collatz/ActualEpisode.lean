import Collatz.EpisodeDeterminism

namespace CollatzFinal
namespace SourceProduct

/-- One odd shortcut step from a number of the form 2*z-1. -/
theorem shortcut_two_mul_sub_one
    {z : Nat} (hz : 0 < z) :
    shortcut (2 * z - 1) = 3 * z - 1 := by
  unfold shortcut
  have ho : (2 * z - 1) % 2 ≠ 0 := by omega
  simp only [ho, ite_false]
  omega

/-- Stripping one exposed factor of two. -/
theorem shortcut_two_mul (z : Nat) :
    shortcut (2 * z) = z := by
  unfold shortcut
  have he : (2 * z) % 2 = 0 := by omega
  simp [he]

/-- Exact odd-run identity underlying the executable episode parser.

If x+1 = 2^r*m, then after r consecutive odd shortcut steps the endpoint is
3^r*m-1.  The proof is source-independent and uses no bounded grammar. -/
theorem iter_anchor_owner
    (r m : Nat) (hm : 0 < m) :
    iter shortcut r (2 ^ r * m - 1) = 3 ^ r * m - 1 := by
  induction r generalizing m with
  | zero =>
      simp [iter]
  | succ r ih =>
      have hz : 0 < 2 ^ r * m :=
        Nat.mul_pos (Nat.pow_pos (by decide)) hm
      have hstart :
          2 ^ (r + 1) * m - 1 =
            2 * (2 ^ r * m) - 1 := by
        simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
      rw [hstart]
      simp only [iter]
      rw [shortcut_two_mul_sub_one hz]
      have ih3 := ih (3 * m) (by omega)
      simpa [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm,
        Nat.mul_left_comm] using ih3

/-- An exposed 2^s factor is stripped in exactly s shortcut steps. -/
theorem iter_pow_two_mul
    (s y : Nat) :
    iter shortcut s (2 ^ s * y) = y := by
  induction s generalizing y with
  | zero =>
      simp [iter]
  | succ s ih =>
      have hstart :
          2 ^ (s + 1) * y = 2 * (2 ^ s * y) := by
        simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
      rw [hstart]
      simp only [iter]
      rw [shortcut_two_mul]
      exact ih y

/-- Natural-number form of the exact episode relation.

It is deliberately equivalent in arithmetic content to V90's
AlgebraicEpisode, but avoids integer casts while establishing existence from
an actual positive odd anchor-owner pair. -/
def NaturalEpisode
    (r m s r' m' : Nat) : Prop :=
  0 < r ∧ 0 < m ∧ m % 2 = 1 ∧
  0 < s ∧ 0 < r' ∧ 0 < m' ∧ m' % 2 = 1 ∧
  ∃ y : Nat,
    0 < y ∧ y % 2 = 1 ∧
    3 ^ r * m = 2 ^ s * y + 1 ∧
    y + 1 = 2 ^ r' * m'

theorem three_pow_mod_two (r : Nat) :
    3 ^ r % 2 = 1 := by
  induction r with
  | zero => decide
  | succ r ih =>
      rw [Nat.pow_succ, Nat.mul_mod, ih]

/-- Every positive odd anchor-owner pair has a next natural episode.

The construction is exactly the executable parser: factor
3^r*m-1 into 2^s*y, then factor y+1 into 2^r'*m'. -/
theorem naturalEpisode_exists
    {r m : Nat}
    (hr : 0 < r) (hm : 0 < m) (hmodd : m % 2 = 1) :
    ∃ s r' m', NaturalEpisode r m s r' m' := by
  let N := 3 ^ r * m
  have hNpos : 0 < N := by
    dsimp [N]
    exact Nat.mul_pos (Nat.pow_pos (by decide)) hm
  have hNodd : N % 2 = 1 := by
    dsimp [N]
    rw [Nat.mul_mod, three_pow_mod_two r, hmodd]
  have hNgt : 1 < N := by
    cases r with
    | zero => omega
    | succ k =>
        have hkpos : 0 < 3 ^ k * m :=
          Nat.mul_pos (Nat.pow_pos (by decide)) hm
        have hEq : N = 3 * (3 ^ k * m) := by
          dsimp [N]
          simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
        rw [hEq]
        omega
  have hNform : N = 2 * (N / 2) + 1 := by
    have hd := Nat.mod_add_div N 2
    omega
  have hhalf : 0 < N / 2 := by omega
  obtain ⟨k, y, hky, hyodd⟩ :=
    nat_dyadic_decomposition (N / 2) hhalf
  have hypos : 0 < y := by
    have hyne : y ≠ 0 := by
      intro hy0
      subst y
      simp at hky
      omega
    exact Nat.pos_of_ne_zero hyne
  let s := k + 1
  have hspos : 0 < s := by dsimp [s]; omega
  have hNy : N = 2 ^ s * y + 1 := by
    calc
      N = 2 * (N / 2) + 1 := hNform
      _ = 2 * (2 ^ k * y) + 1 := by rw [hky]
      _ = 2 ^ (k + 1) * y + 1 := by
        simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
      _ = 2 ^ s * y + 1 := by rfl
  have hy1even : (y + 1) % 2 = 0 := by
    omega
  have hy1form : y + 1 = 2 * ((y + 1) / 2) := by
    have hd := Nat.mod_add_div (y + 1) 2
    omega
  have hyhalf : 0 < (y + 1) / 2 := by omega
  obtain ⟨k', m', hkm, hm'odd⟩ :=
    nat_dyadic_decomposition ((y + 1) / 2) hyhalf
  have hm'pos : 0 < m' := by
    have hmne : m' ≠ 0 := by
      intro hm0
      subst m'
      simp at hkm
      omega
    exact Nat.pos_of_ne_zero hmne
  let r' := k' + 1
  have hr'pos : 0 < r' := by dsimp [r']; omega
  have hym : y + 1 = 2 ^ r' * m' := by
    calc
      y + 1 = 2 * ((y + 1) / 2) := hy1form
      _ = 2 * (2 ^ k' * m') := by rw [hkm]
      _ = 2 ^ (k' + 1) * m' := by
        simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
      _ = 2 ^ r' * m' := by rfl
  refine ⟨s, r', m', hr, hm, hmodd, hspos, hr'pos, hm'pos, hm'odd, y,
    hypos, hyodd, ?_, hym⟩
  simpa [N] using hNy

/-- A natural episode is the actual Collatz episode: beginning at
x=2^r*m-1, the orbit reaches the next odd start 2^r'*m'-1 after exactly r+s
shortcut steps. -/
theorem naturalEpisode_actual
    {r m s r' m' : Nat}
    (h : NaturalEpisode r m s r' m') :
    iter shortcut (r + s) (2 ^ r * m - 1) =
      2 ^ r' * m' - 1 := by
  rcases h with
    ⟨hr, hm, hmodd, hs, hr', hm', hm'odd, y,
      hy, hyodd, hmid, hend⟩
  rw [iter_add, iter_anchor_owner r m hm]
  have heven : 3 ^ r * m - 1 = 2 ^ s * y := by omega
  rw [heven, iter_pow_two_mul]
  omega

/-- Existence of an actual next episode from every positive odd anchor-owner
pair. -/
theorem actual_next_episode_exists
    {r m : Nat}
    (hr : 0 < r) (hm : 0 < m) (hmodd : m % 2 = 1) :
    ∃ s r' m',
      NaturalEpisode r m s r' m' ∧
      iter shortcut (r + s) (2 ^ r * m - 1) =
        2 ^ r' * m' - 1 := by
  obtain ⟨s, r', m', h⟩ := naturalEpisode_exists hr hm hmodd
  exact ⟨s, r', m', h, naturalEpisode_actual h⟩

#print axioms shortcut_two_mul_sub_one
#print axioms iter_anchor_owner
#print axioms iter_pow_two_mul
#print axioms naturalEpisode_exists
#print axioms naturalEpisode_actual
#print axioms actual_next_episode_exists

end SourceProduct
end CollatzFinal
