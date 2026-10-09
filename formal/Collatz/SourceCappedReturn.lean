import Collatz.PositiveSourceThreeWay
import Collatz.OrdinaryExitReduction

namespace CollatzFinal
namespace SourceProduct

/-- Exact signed return defect is simply the scaled change in owner.
For an actually executed affine owner equation P*m1=A*m0+B,
  Δ(m0) = (P-A)*m0 - B = P*(m0-m1).
A defect sign by itself is not a source-relative exit. -/
theorem executed_return_defect_eq_owner_gap
    {A B P m0 m1 : Nat}
    (hAff : P * m1 = A * m0 + B) :
    returnDefect (A : Int) (B : Int) (P : Int) (m0 : Int) =
      (P : Int) * ((m0 : Int) - (m1 : Int)) := by
  have hCast := congrArg (fun z : Nat => (z : Int)) hAff
  have hAffI :
      (P : Int) * (m1 : Int) =
        (A : Int) * (m0 : Int) + (B : Int) := by
    simpa using hCast
  unfold returnDefect
  rw [Int.sub_mul, Int.mul_sub]
  omega

/-- A positive-denominator executed return has zero defect exactly when
its natural owner has not changed. The converse is true only because
the actual affine law is supplied, not for a guessed symbolic return. -/
theorem executed_return_zero_iff_same_owner
    {A B P m0 m1 : Nat}
    (hP : 0 < P) (hAff : P * m1 = A * m0 + B) :
    returnDefect (A : Int) (B : Int) (P : Int) (m0 : Int) = 0 ↔
      m0 = m1 := by
  rw [executed_return_defect_eq_owner_gap hAff]
  constructor
  · intro hzero
    have hPne : (P : Int) ≠ 0 := by omega
    have hdiff :
        (m0 : Int) - (m1 : Int) = 0 :=
      (Int.mul_eq_zero.mp hzero).resolve_left hPne
    omega
  · intro hm
    rw [hm]
    simp

/-- Every admitted nonzero actual return has a strictly ordered owner
pair, with no equality branch hidden inside the finite dyadic order. -/
theorem admitted_executed_return_owner_changes
    {A B m0 m1 D : Nat}
    (hAff : 2 ^ D * m1 = A * m0 + B)
    (hadm :
      ReturnCylinderAdmissible
        (A : Int) (B : Int) D (m0 : Int)) :
    m1 < m0 ∨ m0 < m1 := by
  obtain ⟨v, hv, horder⟩ := hadm
  have hnonzero := dyadic_order_nonzero horder
  have hzero_eq :=
    executed_return_zero_iff_same_owner
      (P := 2 ^ D) (Nat.pow_pos (by decide)) hAff
  have hne : m0 ≠ m1 := by
    intro heq
    exact hnonzero (hzero_eq.mpr heq)
  omega

/-- For two positive owners at the same positive episode anchor,
strict owner descent is an actual numerical endpoint descent. -/
theorem same_anchor_owner_descent_is_endpoint_descent
    {r m0 m1 : Nat}
    (hr : 0 < r) (hm0 : 0 < m0) (hm1 : 0 < m1)
    (hdesc : m1 < m0) :
    2 ^ r * m1 - 1 < 2 ^ r * m0 - 1 := by
  have hp : 0 < 2 ^ r := Nat.pow_pos (by decide)
  have hprod : 2 ^ r * m1 < 2 ^ r * m0 :=
    Nat.mul_lt_mul_of_pos_left hdesc hp
  have hbefore : 0 < 2 ^ r * m0 := Nat.mul_pos hp hm0
  have hafter : 0 < 2 ^ r * m1 := Nat.mul_pos hp hm1
  omega

/-- An actual same-anchor descent beginning below the original source
is an ordinary lower-source exit. The cap on the *old* endpoint is
essential: an arbitrary local descent above n does NOT imply an exit. -/
theorem source_capped_same_anchor_descent_is_ordinary_exit
    (n L t r m0 m1 : Nat)
    (hn : 0 < n) (hr : 0 < r)
    (hm0 : 0 < m0) (hm1 : 0 < m1)
    (hbefore :
      iter shortcut L n = 2 ^ r * m0 - 1)
    (hreturn :
      iter shortcut t (2 ^ r * m0 - 1) = 2 ^ r * m1 - 1)
    (hcap : 2 ^ r * m0 - 1 ≤ n)
    (hdesc : m1 < m0) :
    OrdinaryExit n (iter shortcut (L + t) n) := by
  have hdrop :=
    same_anchor_owner_descent_is_endpoint_descent
      hr hm0 hm1 hdesc
  have hafter :
      iter shortcut (L + t) n = 2 ^ r * m1 - 1 := by
    rw [iter_add, hbefore]
    exact hreturn
  have hpos : 0 < iter shortcut (L + t) n :=
    iter_positive shortcut shortcut_positive (L + t) n hn
  have hlt : iter shortcut (L + t) n < n := by
    rw [hafter]
    omega
  exact Or.inr (Or.inl ⟨hpos, hlt⟩)

/-- Such a source-capped descent is forbidden along the actual path of
a minimal positive Collatz counterexample. No global Collatz conclusion
is assumed here; only the existing proved no-ordinary-exit lemma. -/
theorem minimal_bad_excludes_source_capped_return_descent
    {n : Nat}
    (hmin : MinimalBad PositiveBad n)
    (L t r m0 m1 : Nat)
    (hr : 0 < r) (hm0 : 0 < m0) (hm1 : 0 < m1)
    (hbefore :
      iter shortcut L n = 2 ^ r * m0 - 1)
    (hreturn :
      iter shortcut t (2 ^ r * m0 - 1) = 2 ^ r * m1 - 1)
    (hcap : 2 ^ r * m0 - 1 ≤ n) :
    ¬ m1 < m0 := by
  intro hdesc
  have hexit :=
    source_capped_same_anchor_descent_is_ordinary_exit
      n L t r m0 m1 hmin.1.1 hr hm0 hm1
      hbefore hreturn hcap hdesc
  exact minimal_bad_has_no_ordinary_exit hmin (L + t) hexit

/-- All the source-relative coordinates are now bound together:
on an actual coherent episode suffix of a hypothetical minimal bad
source, any repeated-anchor return starting no higher than that source
cannot strictly decrease its owner. -/
theorem minimal_bad_source_capped_coherent_return_non_decrease
    {n : Nat} (hmin : MinimalBad PositiveBad n)
    (initialDepth : Nat) (a : ValidEpisode)
    (hinit :
      iter shortcut initialDepth n =
        2 ^ a.anchor * a.owner - 1)
    (i d : Nat) (hd : 0 < d)
    (hsame :
      (episodeStream a (i + d)).anchor =
        (episodeStream a i).anchor)
    (hcap :
      iter shortcut (initialDepth + episodeStreamTime a i) n ≤ n) :
    (episodeStream a i).owner ≤
      (episodeStream a (i + d)).owner := by
  let before := episodeStream a i
  let after := episodeStream a (i + d)
  have hbefore :
      iter shortcut (initialDepth + episodeStreamTime a i) n =
        2 ^ before.anchor * before.owner - 1 := by
    rw [iter_add, hinit]
    exact episode_stream_matches_actual_shortcut a i
  have hreturn :
      iter shortcut (episodeStreamTime before d)
        (2 ^ before.anchor * before.owner - 1) =
        2 ^ before.anchor * after.owner - 1 := by
    have htrace := episode_stream_matches_actual_shortcut before d
    have hshift := episode_stream_shift a i d
    rw [← hshift] at htrace
    rw [hsame] at htrace
    exact htrace
  have hcapLocal :
      2 ^ before.anchor * before.owner - 1 ≤ n := by
    rw [← hbefore]
    exact hcap
  have hno := minimal_bad_excludes_source_capped_return_descent
    hmin (initialDepth + episodeStreamTime a i)
    (episodeStreamTime before d)
    before.anchor before.owner after.owner
    before.anchor_pos before.owner_pos after.owner_pos
    hbefore hreturn hcapLocal
  omega

/-- For a source-capped actual repeated-anchor return that is
nonzero and cylinder-admitted, equality is also impossible:
the owner must strictly ASCEND. This identifies the surviving
local residual under the minimal-bad hypothesis. -/
theorem minimal_bad_source_capped_admitted_return_strict_ascent
    {n : Nat} (hmin : MinimalBad PositiveBad n)
    (initialDepth : Nat) (a : ValidEpisode)
    (hinit :
      iter shortcut initialDepth n = 2 ^ a.anchor * a.owner - 1)
    (i d A B P D : Nat)
    (hd : 0 < d)
    (hsame :
      (episodeStream a (i + d)).anchor =
        (episodeStream a i).anchor)
    (hcap :
      iter shortcut (initialDepth + episodeStreamTime a i) n ≤ n)
    (hP : P = 2 ^ D)
    (hAff :
      P * (episodeStream a (i + d)).owner =
        A * (episodeStream a i).owner + B)
    (hadm :
      ReturnCylinderAdmissible
        (A : Int) (B : Int) D
          ((episodeStream a i).owner : Int)) :
    (episodeStream a i).owner <
      (episodeStream a (i + d)).owner := by
  have hle :=
    minimal_bad_source_capped_coherent_return_non_decrease
      hmin initialDepth a hinit i d hd hsame hcap
  have hEq :
      2 ^ D * (episodeStream a (i + d)).owner =
        A * (episodeStream a i).owner + B := by
    simpa [hP] using hAff
  rcases admitted_executed_return_owner_changes hEq hadm with
    hdown | hup
  · omega
  · exact hup

#print axioms executed_return_defect_eq_owner_gap
#print axioms executed_return_zero_iff_same_owner
#print axioms admitted_executed_return_owner_changes
#print axioms same_anchor_owner_descent_is_endpoint_descent
#print axioms source_capped_same_anchor_descent_is_ordinary_exit
#print axioms minimal_bad_excludes_source_capped_return_descent
#print axioms minimal_bad_source_capped_coherent_return_non_decrease
#print axioms minimal_bad_source_capped_admitted_return_strict_ascent

end SourceProduct
end CollatzFinal
