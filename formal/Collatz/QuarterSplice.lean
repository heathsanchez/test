import Collatz.PrefixHighOddCloseout

namespace CollatzFinal
namespace SourceProduct

/-- Crystal's V3 valuation pullback collapses to one universal local law.
Every odd value in the 5 mod 8 class has a quarter-sized odd sibling whose
orbit coalesces after three shortcut steps versus one. -/
theorem quarter_splice_of_mod8_five
    {x : Nat}
    (hx : x % 8 = 5) :
    let p := (x - 1) / 4
    0 < p ∧ p % 2 = 1 ∧
      iter shortcut 3 x = iter shortcut 1 p := by
  let a := x / 8
  have hx' : x = 8 * a + 5 := by
    dsimp [a]
    omega
  have hp : (x - 1) / 4 = 2 * a + 1 := by
    rw [hx']
    omega
  rw [hp, hx']
  constructor
  · omega
  constructor
  · omega
  · have h1 : shortcut (8 * a + 5) = 12 * a + 8 := by
      unfold shortcut
      have ho : (8 * a + 5) % 2 ≠ 0 := by omega
      simp only [ho, ite_false]
      omega
    have h2 : shortcut (12 * a + 8) = 6 * a + 4 := by
      unfold shortcut
      have he : (12 * a + 8) % 2 = 0 := by omega
      simp only [he, ite_true]
      omega
    have h3 : shortcut (6 * a + 4) = 3 * a + 2 := by
      unfold shortcut
      have he : (6 * a + 4) % 2 = 0 := by omega
      simp only [he, ite_true]
      omega
    have hp1 : shortcut (2 * a + 1) = 3 * a + 2 := by
      unfold shortcut
      have ho : (2 * a + 1) % 2 ≠ 0 := by omega
      simp only [ho, ite_false]
      omega
    simp [iter, h1, h2, h3, hp1]

/-- Source-relative form: a 5 mod 8 endpoint at height at most 4*n
supplies an exact lower-source coalescence exit three steps later. -/
theorem ordinary_exit_after_quarter_splice
    {n x : Nat}
    (hx : x % 8 = 5)
    (hband : x ≤ 4 * n) :
    OrdinaryExit n (iter shortcut 3 x) := by
  let p := (x - 1) / 4
  have hs := quarter_splice_of_mod8_five hx
  have hp : 0 < p := by
    simpa [p] using hs.1
  have hlt : p < n := by
    let a := x / 8
    have hx' : x = 8 * a + 5 := by
      dsimp [a]
      omega
    have hp' : p = 2 * a + 1 := by
      dsimp [p]
      rw [hx']
      omega
    rw [hp']
    rw [hx'] at hband
    omega
  have heq : iter shortcut 1 p = iter shortcut 3 x := by
    simpa [p] using hs.2.2.symm
  exact Or.inr (Or.inr ⟨p, 1, hp, hlt, heq⟩)

/-- The exact future event sufficient for the large branch:
hit a 5 mod 8 value before exceeding 3*y+1. -/
def QuarterSpliceFuture7 : Prop :=
  ∀ y, 0 < y → y % 12 = 7 →
    ∃ r, let x := iter shortcut r y
      x % 8 = 5 ∧ x ≤ 3 * y + 1

/-- A single quarter-splice future event implies the consequence-pruned
three-quarter coalescence capability. -/
theorem three_quarter_coalescence7_of_quarter_splice_future7
    (hQ : QuarterSpliceFuture7) :
    ThreeQuarterCoalescence7 := by
  intro y hy hmod
  obtain ⟨r, hxmod, hxband⟩ := hQ y hy hmod
  let x := iter shortcut r y
  let p := (x - 1) / 4
  have hs : 0 < p ∧ p % 2 = 1 ∧
      iter shortcut 3 x = iter shortcut 1 p := by
    exact quarter_splice_of_mod8_five (by simpa [x] using hxmod)
  have h4p : 4 * p ≤ 3 * y := by
    let a := x / 8
    have hx' : x = 8 * a + 5 := by
      dsimp [a, x]
      have hm : x % 8 = 5 := by simpa [x] using hxmod
      omega
    have hp' : p = 2 * a + 1 := by
      dsimp [p]
      rw [hx']
      omega
    have hb : x ≤ 3 * y + 1 := by simpa [x] using hxband
    rw [hp']
    rw [hx'] at hb
    omega
  refine ⟨p, r + 3, 1, hs.1, h4p, ?_⟩
  calc
    iter shortcut (r + 3) y =
        iter shortcut 3 (iter shortcut r y) := iter_add shortcut r 3 y
    _ = iter shortcut 3 x := by rfl
    _ = iter shortcut 1 p := hs.2.2

/-- Final closeout after both consequence-pruning steps. -/
theorem reaches_one_of_prefix_high_odd_and_quarter_splice_future7
    (hHigh : PrefixHighOddConstructorCoverage)
    (hQ : QuarterSpliceFuture7) :
    ∀ n, 0 < n → ∃ t, iter shortcut t n = 1 := by
  exact reaches_one_of_prefix_high_odd_and_three_quarter_coalescence7
    hHigh (three_quarter_coalescence7_of_quarter_splice_future7 hQ)

/-- Unified Crystal target: every odd source above one eventually reaches a
5 mod 8 value before exceeding four times the original source. -/
def OddQuarterSpliceCoverage : Prop :=
  ∀ n, 1 < n → n % 2 = 1 →
    ∃ r, let x := iter shortcut r n
      x % 8 = 5 ∧ x ≤ 4 * n

/-- One-premise source-order closeout.  The quarter-splice event constructs
p=(x-1)/4<n with a common future, contradicting minimal badness. -/
theorem reaches_one_of_odd_quarter_splice_coverage
    (hQ : OddQuarterSpliceCoverage) :
    ∀ n, 0 < n → ∃ t, iter shortcut t n = 1 := by
  have hnone : ∀ n, ¬ PositiveBad n := by
    apply no_bad_of_no_minimal PositiveBad
    intro n hmin
    have hgt : 1 < n := by
      have hn : 0 < n := hmin.1.1
      have hne : n ≠ 1 := by
        intro heq
        apply hmin.1.2
        subst n
        exact ⟨0, by simp [iter, Terminal]⟩
      omega
    have hodd : n % 2 = 1 := positive_minimal_bad_odd hmin
    obtain ⟨r, hxmod, hxband⟩ := hQ n hgt hodd
    have hexit : OrdinaryExit n (iter shortcut (r + 3) n) := by
      rw [iter_add]
      exact ordinary_exit_after_quarter_splice hxmod hxband
    exact minimal_bad_has_no_ordinary_exit hmin (r + 3) hexit
  intro n hn
  have hgood : CollatzGood n := by
    apply Classical.byContradiction
    intro hbad
    exact hnone n ⟨hn, hbad⟩
  exact collatzGood_eventually_one hgood

/-- Consequence-pruned fixed-origin target.  A source need not itself
realize the quarter splice if it has already descended below its starting
source: either event contradicts minimal badness. -/
def DescentOrQuarterSpliceCoverage : Prop :=
  ∀ n, 1 < n → n % 2 = 1 →
    ∃ r, let x := iter shortcut r n
      (0 < x ∧ x < n) ∨ (x % 8 = 5 ∧ x ≤ 4 * n)

/-- The fixed-origin consequence quotient is sufficient for Collatz.
This is strictly weaker as an interface than requiring every source itself
to realize a quarter splice before any descent. -/
theorem reaches_one_of_descent_or_quarter_splice_coverage
    (hQ : DescentOrQuarterSpliceCoverage) :
    ∀ n, 0 < n → ∃ t, iter shortcut t n = 1 := by
  have hnone : ∀ n, ¬ PositiveBad n := by
    apply no_bad_of_no_minimal PositiveBad
    intro n hmin
    have hgt : 1 < n := by
      have hn : 0 < n := hmin.1.1
      have hne : n ≠ 1 := by
        intro heq
        apply hmin.1.2
        subst n
        exact ⟨0, by simp [iter, Terminal]⟩
      omega
    have hodd : n % 2 = 1 := positive_minimal_bad_odd hmin
    obtain ⟨r, hdesc | hsplice⟩ := hQ n hgt hodd
    · have hexit : OrdinaryExit n (iter shortcut r n) :=
        Or.inr (Or.inl hdesc)
      exact minimal_bad_has_no_ordinary_exit hmin r hexit
    · have hexit : OrdinaryExit n (iter shortcut (r + 3) n) := by
        rw [iter_add]
        exact ordinary_exit_after_quarter_splice hsplice.1 hsplice.2
      exact minimal_bad_has_no_ordinary_exit hmin (r + 3) hexit
  intro n hn
  have hgood : CollatzGood n := by
    apply Classical.byContradiction
    intro hbad
    exact hnone n ⟨hn, hbad⟩
  exact collatzGood_eventually_one hgood

#print axioms reaches_one_of_descent_or_quarter_splice_coverage

#print axioms quarter_splice_of_mod8_five
#print axioms ordinary_exit_after_quarter_splice
#print axioms three_quarter_coalescence7_of_quarter_splice_future7
#print axioms reaches_one_of_prefix_high_odd_and_quarter_splice_future7
#print axioms reaches_one_of_odd_quarter_splice_coverage

end SourceProduct
end CollatzFinal
