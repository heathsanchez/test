import Collatz.SourceCappedTernaryBar

namespace CollatzFinal
namespace SourceProduct

/-- A hypothetical least bad source cannot have an actual source-capped
ternary endpoint. This uses the existing lower-merge prohibition. -/
theorem minimal_bad_excludes_capped_ternary
    {n : Nat} (hmin : MinimalBad PositiveBad n) :
    ¬ SourceCappedTernaryReturn n := by
  intro hc
  have hn : 1 < n := by
    have hpos : 0 < n := hmin.1.1
    have hne : n ≠ 1 := by
      intro he
      subst n
      have hone : CollatzGood 1 := ⟨0, Or.inl rfl⟩
      exact hmin.1.2 hone
    omega
  obtain ⟨p, hp, hm⟩ := capped_ternary_return_earns_lower_merge hn hc
  exact positive_minimal_no_lower_merge hmin p hp hm

/-- Source-relative lower barrier, at *every* actual ternary endpoint
of a hypothetical minimal bad source, not a bounded experiment. -/
theorem minimal_bad_ternary_endpoint_lower_bound
    {n : Nat} (hmin : MinimalBad PositiveBad n)
    (k : Nat) (hmod : (iter shortcut k n) % 3 = 2) :
    3 * n ≤ 2 * iter shortcut k n - 1 := by
  apply Classical.byContradiction
  intro hbad
  have hc : SourceCappedTernaryReturn n :=
    ⟨k, hmod, by omega⟩
  exact minimal_bad_excludes_capped_ternary hmin hc

#print axioms minimal_bad_excludes_capped_ternary
#print axioms minimal_bad_ternary_endpoint_lower_bound

end SourceProduct
end CollatzFinal
