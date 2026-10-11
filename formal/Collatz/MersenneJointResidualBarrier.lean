import Collatz.AllScaleHighOddBarrier
import Collatz.ActualEpisode

set_option maxRecDepth 16384

namespace CollatzFinal
namespace SourceProduct

/-!
V182 — REAL MERSENNE SOURCES PASS ALL APPLICABLE V181 HIGH-ODD GUARDS.

For every integer m>0, let n_m=2^(10*m+1)-1.
The first 10*m+1 actual shortcut steps are all odd. In particular,
for EVERY q with 1<=q<=m, the positive source n_m meets the height
threshold n_m>=2^(10*q) and has exactly 5*q odd steps in its first
5*q clocks. It satisfies ALL applicable V181 NECESSARY high-odd
conditions, and is an authentic positive integer, not a 2-adic ghost.

This is an unconditional exact finite-prefix theorem for an
UNBOUNDED family of sources. It neither asserts nor refutes
convergence of the family. Global Collatz UNKNOWN.
-/

/-- Genuine Nat shortcut identity on the initial all-odd corridor
of the positive Mersenne source 2^K-1, for every clock t<=K. -/
theorem v182_mersenne_true_initial_prefix
    (K t : Nat) (ht : t<=K) :
    iter shortcut t (2^K-1) = 3^t*2^(K-t)-1 := by
  have hk : K=t+(K-t) := by omega
  have hfactor : 2^K = 2^t*2^(K-t) := by
    calc
      2^K = 2^(t+(K-t)) := congrArg (fun v : Nat => 2^v) hk
      _ = 2^t*2^(K-t) := Nat.pow_add 2 t (K-t)
  have hpos : 0<2^(K-t) := Nat.pow_pos (by decide)
  rw [hfactor]
  exact iter_anchor_owner t (2^(K-t)) hpos

/-- Every genuine pre-transition endpoint of a Mersenne source
is odd while its finite all-odd corridor remains active. -/
theorem v182_mersenne_odd_at_each_prefix_step
    (K t : Nat) (ht : t<K) :
    iter shortcut t (2^K-1)%2=1 := by
  have hdiff : 0<K-t := by omega
  have hpow : 2^(K-t)%2=0 := by
    have he : K-t=(K-t-1)+1 := by omega
    rw [he,Nat.pow_succ]
    omega
  have hmul : (3^t*2^(K-t))%2=0 := by
    simp [Nat.mul_mod,hpow]
  have hpositive : 0<3^t*2^(K-t) :=
    Nat.mul_pos (Nat.pow_pos (by decide))
      (Nat.pow_pos (by decide))
  rw [v182_mersenne_true_initial_prefix K t (by omega)]
  omega

/-- The actual source-specific odd count equals the true clock
through every prefix of the Mersenne corridor, not only modulo
some 2-adic formal word. -/
theorem v182_mersenne_all_odd_count
    (K : Nat) :
    ∀ t : Nat, t<=K →
      oddCount (2^K-1) t=t := by
  intro t
  induction t with
  | zero =>
      intro _ht
      simp [oddCount]
  | succ t ih =>
      intro ht
      have htlt : t<K := by omega
      have hprev : t<=K := by omega
      have hodd := v182_mersenne_odd_at_each_prefix_step K t htlt
      have hne : iter shortcut t (2^K-1)%2≠0 := by omega
      simp only [oddCount,hne,ite_false]
      exact congrArg Nat.succ (ih hprev)

/-- Elementary non-Mathlib monotonicity of exact powers of two. -/
theorem v182_pow_two_mono (a b : Nat)
    (h : a<=b) : 2^a<=2^b := by
  induction b with
  | zero =>
      have hz : a=0 := by omega
      subst a
      exact Nat.le_refl _
  | succ b ih =>
      by_cases hle : a<=b
      · calc
          2^a<=2^b := ih hle
          _<=2^(b+1) := by
            rw [Nat.pow_succ]
            have hp : 0<2^b := Nat.pow_pos (by decide)
            omega
      · have heq : a=b+1 := by omega
        rw [heq]
        exact Nat.le_refl _

/-- For ALL applicable positive scales q<=m, one exact, positive
Mersenne source simultaneously meets the original-source HEIGHT
premise and its required high-odd CONCLUSION. -/
theorem v182_mersenne_passes_every_applicable_v181_guard
    (m q : Nat) (hm : 0<m)
    (hq : 0<q) (hqm : q<=m) :
    2^(10*q)<=2^(10*m+1)-1 ∧
    3*q+1<=oddCount (2^(10*m+1)-1) (5*q) := by
  have hmono : 2^(10*q)<=2^(10*m) :=
    v182_pow_two_mono (10*q) (10*m) (by omega)
  have hpositive : 0<2^(10*m) := Nat.pow_pos (by decide)
  have hbig : 2^(10*m)<=2^(10*m+1)-1 := by
    rw [Nat.pow_succ]
    omega
  have hclock : 5*q<=10*m+1 := by omega
  have hcount :=
    v182_mersenne_all_odd_count (10*m+1) (5*q) hclock
  constructor
  · omega
  · rw [hcount]
    omega

/-- All applicable V181 guards are nonempty even at unbounded
Mersenne source heights. This is a uniform quantified statement,
not a collection of numerical trajectory samples. -/
theorem v182_each_positive_scale_has_true_high_odd_source
    (m : Nat) (hm : 0<m) :
    ∃ n : Nat, 0<n ∧ 2^(10*m)<=n ∧
       3*m+1<=oddCount n (5*m) := by
  refine ⟨2^(10*m+1)-1, ?_, ?_, ?_⟩
  · have hh := v182_mersenne_passes_every_applicable_v181_guard
      m m hm hm (Nat.le_refl _)
    have hpow : 0<2^(10*m) := Nat.pow_pos (by decide)
    omega
  · exact (v182_mersenne_passes_every_applicable_v181_guard
      m m hm hm (Nat.le_refl _)).1
  · exact (v182_mersenne_passes_every_applicable_v181_guard
      m m hm hm (Nat.le_refl _)).2

/-- The smallest exact original-source grammar-relative survivor
in the V182 periodic Mersenne family nevertheless reaches terminal2
after 193 genuine shortcut steps. This prevents promoting
"irreducible under bank" to "divergent". The bank-residue exclusion
itself is a SEPARATE source-pinned exact modular audit, not a
Lean theorem in this module. -/
theorem v182_smallest_joint_residual_is_actually_good :
    CollatzGood (2^21-1) := by
  refine ⟨193, ?_⟩
  have h : iter shortcut 193 (2^21-1)=2 := by decide
  rw [h]
  simp [Terminal]

#print axioms v182_smallest_joint_residual_is_actually_good

#print axioms v182_mersenne_true_initial_prefix
#print axioms v182_mersenne_odd_at_each_prefix_step
#print axioms v182_mersenne_all_odd_count
#print axioms v182_pow_two_mono
#print axioms v182_mersenne_passes_every_applicable_v181_guard
#print axioms v182_each_positive_scale_has_true_high_odd_source

end SourceProduct
end CollatzFinal
