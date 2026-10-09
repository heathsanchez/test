import Collatz.EpisodeBridge

namespace CollatzFinal
namespace SourceProduct

/-- Exact natural-owner affine law of one actual episode:
    2^(s+r') * m' = 3^r * m + (2^s - 1).
No solver, corpus, or law bank is involved. -/
theorem natural_episode_affine_law
    {r m s r' m' : Nat}
    (he : NaturalEpisode r m s r' m') :
    2 ^ (s + r') * m' = 3 ^ r * m + (2 ^ s - 1) := by
  rcases he with
    ⟨hr, hm, hodd, hs, hr', hm', hm'odd, y,
      hy, hyodd, hmid, hend⟩
  have hEq :
      2 ^ (s + r') * m' = 2 ^ s * y + 2 ^ s := by
    calc
      2 ^ (s + r') * m'
          = 2 ^ s * (2 ^ r' * m') := by
              simp [Nat.pow_add, Nat.mul_assoc]
      _ = 2 ^ s * (y + 1) := by rw [← hend]
      _ = 2 ^ s * y + 2 ^ s := by
            simp [Nat.mul_add]
  have hPos : 0 < 2 ^ s := Nat.pow_pos (by decide)
  omega

/-- A finite source-admitted actual episode word with its compiled affine
certificate (A,B,P) and exact shortcut time t.
Indices retain the initial and final anchor/owner pairs. -/
inductive ActualEpisodeChain :
    Nat → Nat → Nat → Nat → Nat → Nat → Nat → Nat → Prop where
  | empty (r m : Nat) :
      ActualEpisodeChain r m r m 0 1 0 1
  | append {r0 m0 r m t A B P s r' m' : Nat}
      (hchain : ActualEpisodeChain r0 m0 r m t A B P)
      (he : NaturalEpisode r m s r' m') :
      ActualEpisodeChain r0 m0 r' m'
        (t + r + s)
        (3 ^ r * A)
        (3 ^ r * B + (2 ^ s - 1) * P)
        (2 ^ (s + r') * P)

/-- Every finite actual episode chain compiles exactly to the executable
affine owner certificate P*m_end = A*m_start + B. -/
theorem actual_episode_chain_affine
    {r0 m0 r m t A B P : Nat}
    (hc : ActualEpisodeChain r0 m0 r m t A B P) :
    P * m = A * m0 + B := by
  induction hc generalizing r0 m0 with
  | empty r m =>
      simp
  | @append r0 m0 r m t A B P s r' m' hchain he ih =>
      have hOne := natural_episode_affine_law he
      calc
        (2 ^ (s + r') * P) * m'
            = P * (2 ^ (s + r') * m') := by
                simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
        _ = P * (3 ^ r * m + (2 ^ s - 1)) := by rw [hOne]
        _ = 3 ^ r * (P * m) + (2 ^ s - 1) * P := by
              simp [Nat.mul_add, Nat.mul_assoc,
                Nat.mul_comm, Nat.mul_left_comm]
        _ = 3 ^ r * (A * m0 + B) + (2 ^ s - 1) * P := by
              rw [ih]
        _ = (3 ^ r * A) * m0 +
              (3 ^ r * B + (2 ^ s - 1) * P) := by
              simp [Nat.mul_add, Nat.mul_assoc]

/-- The same compiled chain is an *actual* shortcut trace from the
original anchored number to the final anchored number. -/
theorem actual_episode_chain_shortcut
    {r0 m0 r m t A B P : Nat}
    (hc : ActualEpisodeChain r0 m0 r m t A B P) :
    iter shortcut t (2 ^ r0 * m0 - 1) = 2 ^ r * m - 1 := by
  induction hc generalizing r0 m0 with
  | empty r m =>
      simp [iter]
  | @append r0 m0 r m t A B P s r' m' hchain he ih =>
      calc
        iter shortcut (t + r + s) (2 ^ r0 * m0 - 1)
            = iter shortcut (r + s)
                (iter shortcut t (2 ^ r0 * m0 - 1)) := by
                  rw [show t + r + s = t + (r + s) by omega, iter_add]
        _ = iter shortcut (r + s) (2 ^ r * m - 1) := by
              rw [ih]
        _ = 2 ^ r' * m' - 1 := naturalEpisode_actual he

/-- If the final episode anchor is the original anchor, this arbitrary
finite actual word provides a source-admitted affine first-return law.
The positive-time guard excludes the vacuous zero-length word. -/
theorem actual_same_anchor_return_certificate
    {r m0 m1 t A B P : Nat}
    (hc : ActualEpisodeChain r m0 r m1 t A B P)
    (_hpositive : 0 < t) :
    P * m1 = A * m0 + B ∧
    iter shortcut t (2 ^ r * m0 - 1) = 2 ^ r * m1 - 1 := by
  exact ⟨actual_episode_chain_affine hc,
    actual_episode_chain_shortcut hc⟩

#print axioms natural_episode_affine_law
#print axioms actual_episode_chain_affine
#print axioms actual_episode_chain_shortcut
#print axioms actual_same_anchor_return_certificate

end SourceProduct
end CollatzFinal
