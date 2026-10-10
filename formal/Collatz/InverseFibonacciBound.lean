import Collatz.SourceRelativeReverseComparison

namespace CollatzFinal
namespace SourceProduct

/-!
V152 — exact reverse-word geometry and a Fibonacci ceiling on direct
terminal-path certification.

This is a bounded structural theorem, NOT Collatz closure. It
identifies a necessary scale-dependent horizon for any certifier
whose accepted evidence is a raw path to Terminal = {1,2}.

The proof keeps branch arithmetic exact: an inverse from y is 2*y,
and optionally (2*y-1)/3, only when y % 3 = 2.
-/

/-- All ordinary one-step shortcut predecessors (including zero)
    are exhausted by the even and odd inverse equations. -/
theorem v152_one_step_reverse_complete (n y : Nat) :
    shortcut n = y ↔ n = 2*y ∨ 3*n+1 = 2*y := by
  constructor
  · intro h
    by_cases he : n % 2 = 0
    · left
      unfold shortcut at h
      simp [he] at h
      omega
    · right
      have ho : n % 2 = 1 := by omega
      unfold shortcut at h
      simp [ho] at h
      omega
  · intro h
    rcases h with h | h
    · subst n
      exact v149_even_inverse_shortcut y
    · exact v149_odd_inverse_shortcut y n h

theorem v152_odd_source_unique (n y : Nat)
    (h : 3*n+1 = 2*y) :
    y % 3 = 2 ∧ n = (2*y-1)/3 := by
  omega

theorem v152_odd_source_exists (y : Nat)
    (h : y % 3 = 2) :
    3*((2*y-1)/3)+1 = 2*y := by
  omega

/-- Complete list of start values at EXACT reverse depth t.
    Duplicates are intentionally retained: length counts paths,
    not distinct sources, making it an unconditional upper bound. -/
def v152InverseSources : Nat → Nat → List Nat
  | 0, y => [y]
  | t+1, y =>
      v152InverseSources t (2*y) ++
        (if y%3=2 then
          v152InverseSources t ((2*y-1)/3)
         else [])

/-- The structural reverse-word recurrence, with multiplicity. -/
def v152InverseWords : Nat → Nat → Nat
  | 0, _ => 1
  | t+1, y =>
      if y%3=2 then
        v152InverseWords t (2*y) +
          v152InverseWords t ((2*y-1)/3)
      else v152InverseWords t (2*y)

theorem v152_inverse_sources_length (t : Nat) :
    ∀ y, (v152InverseSources t y).length =
      v152InverseWords t y := by
  induction t with
  | zero =>
      intro y
      simp [v152InverseSources,v152InverseWords]
  | succ t ih =>
      intro y
      by_cases h : y%3=2
      · simp [v152InverseSources,v152InverseWords,h,ih]
      · simp [v152InverseSources,v152InverseWords,h,ih]

/-- All enumerated reverse words are REAL paths of the shortcut. -/
theorem v152_reverse_sources_sound (t : Nat) :
    ∀ y n, n ∈ v152InverseSources t y →
      iter shortcut t n = y := by
  induction t with
  | zero =>
      intro y n h
      simpa [v152InverseSources,iter] using h
  | succ t ih =>
      intro y n h
      have hm :
          n ∈ v152InverseSources t (2*y) ∨
          n ∈ (if y%3=2 then
              v152InverseSources t ((2*y-1)/3) else []) := by
        simpa only [v152InverseSources,List.mem_append] using h
      rcases hm with he | ho
      · have hh := ih (2*y) n he
        calc
          iter shortcut (t+1) n =
              shortcut (iter shortcut t n) := by
                rw [iter_add]
                rfl
          _ = y := by rw [hh,v149_even_inverse_shortcut]
      · have htwo : y%3=2 := by
          by_cases hy : y%3=2
          · exact hy
          · simp [hy] at ho
        have hhh : n ∈ v152InverseSources t ((2*y-1)/3) := by
          simpa [htwo] using ho
        have hh := ih ((2*y-1)/3) n hhh
        have hinv := v152_odd_source_exists y htwo
        calc
          iter shortcut (t+1) n =
              shortcut (iter shortcut t n) := by
                rw [iter_add]
                rfl
          _ = y := by
                rw [hh]
                exact v149_odd_inverse_shortcut y ((2*y-1)/3) hinv

/-- No actual terminal path can be missing from the list. -/
theorem v152_reverse_sources_complete (t : Nat) :
    ∀ y n, iter shortcut t n = y →
      n ∈ v152InverseSources t y := by
  induction t with
  | zero =>
      intro y n h
      have he : n = y := by simpa [iter] using h
      simp [v152InverseSources,he]
  | succ t ih =>
      intro y n h
      have hh : shortcut (iter shortcut t n) = y := by
        have ha : iter shortcut (t+1) n =
            shortcut (iter shortcut t n) := by
          rw [iter_add]
          rfl
        omega
      rcases (v152_one_step_reverse_complete
        (iter shortcut t n) y).mp hh with he | ho
      · have hm : n ∈ v152InverseSources t (2*y) :=
          ih (2*y) n he
        change n ∈ (v152InverseSources t (2*y) ++
          (if y%3=2 then
            v152InverseSources t ((2*y-1)/3) else []))
        exact List.mem_append.mpr (Or.inl hm)
      · obtain ⟨htwo,he⟩ :=
          v152_odd_source_unique (iter shortcut t n) y ho
        have hm : n ∈ v152InverseSources t ((2*y-1)/3) :=
          ih ((2*y-1)/3) n he
        change n ∈ (v152InverseSources t (2*y) ++
          (if y%3=2 then
            v152InverseSources t ((2*y-1)/3) else []))
        apply List.mem_append.mpr
        right
        simpa [htwo] using hm

/-- Pair (A_t, B_t): Fibonacci class ceilings for sources in
    residue classes !=2 and =2 respectively. -/
def v152FibonacciBounds : Nat → Nat × Nat
  | 0 => (1,1)
  | t+1 =>
      let b := v152FibonacciBounds t
      (b.2,b.1+b.2)

theorem v152_fibonacci_bounds_order (t : Nat) :
    1 ≤ (v152FibonacciBounds t).1 ∧
    (v152FibonacciBounds t).1 ≤ (v152FibonacciBounds t).2 := by
  induction t with
  | zero =>
      decide
  | succ t ih =>
      change 1 ≤ (v152FibonacciBounds t).2 ∧
        (v152FibonacciBounds t).2 ≤
          (v152FibonacciBounds t).1+(v152FibonacciBounds t).2
      omega

/-- Even inverse flips residues 1 and 2, and preserves residue 0.
    Thus no node of residue 1 or 0 immediately bifurcates.
    Class-2 inverse words obey a Fibonacci ceiling. -/
theorem v152_inverse_words_mod3_fibonacci (t : Nat) :
    ∀ y, v152InverseWords t y ≤
       (if y%3=2 then
         (v152FibonacciBounds t).2
        else (v152FibonacciBounds t).1) := by
  induction t with
  | zero =>
      intro y
      simp [v152InverseWords,v152FibonacciBounds]
  | succ t ih =>
      intro y
      have hord := v152_fibonacci_bounds_order t
      have heven := ih (2*y)
      by_cases htwo : y%3=2
      · have hemod : (2*y)%3≠2 := by omega
        have hea : v152InverseWords t (2*y) ≤
            (v152FibonacciBounds t).1 := by
          simpa [hemod] using heven
        have ho := ih ((2*y-1)/3)
        have hob : v152InverseWords t ((2*y-1)/3) ≤
            (v152FibonacciBounds t).2 := by
          by_cases hoddmod : ((2*y-1)/3)%3=2
          · simpa [hoddmod] using ho
          · have hsmall : v152InverseWords t ((2*y-1)/3) ≤
                (v152FibonacciBounds t).1 := by
              simpa [hoddmod] using ho
            exact Nat.le_trans hsmall hord.2
        simpa [v152InverseWords,v152FibonacciBounds,htwo] using
          (Nat.add_le_add hea hob)
      · by_cases hone : y%3=1
        · have hemod : (2*y)%3=2 := by omega
          have heb : v152InverseWords t (2*y) ≤
              (v152FibonacciBounds t).2 := by
            simpa [hemod] using heven
          simpa [v152InverseWords,v152FibonacciBounds,htwo] using heb
        · have hemod : (2*y)%3≠2 := by omega
          have hea : v152InverseWords t (2*y) ≤
              (v152FibonacciBounds t).1 := by
            simpa [hemod] using heven
          have heb := Nat.le_trans hea hord.2
          simpa [v152InverseWords,v152FibonacciBounds,htwo] using heb

theorem v152_inverse_words_global_fibonacci (t y : Nat) :
    v152InverseWords t y ≤ (v152FibonacciBounds t).2 := by
  have h := v152_inverse_words_mod3_fibonacci t y
  by_cases htwo : y%3=2
  · simpa [htwo] using h
  · have ha : v152InverseWords t y ≤
        (v152FibonacciBounds t).1 := by
      simpa [htwo] using h
    exact Nat.le_trans ha (v152_fibonacci_bounds_order t).2

/-- Both terminal targets, each exact reverse depth <=t.
    Repeated paths/sources are overcounted (safe for an upper bound). -/
def v152TerminalPathBudget : Nat → Nat
  | 0 => v152InverseWords 0 1+v152InverseWords 0 2
  | t+1 =>
      v152TerminalPathBudget t +
        v152InverseWords (t+1) 1+
        v152InverseWords (t+1) 2

def v152FibonacciPathBudget : Nat → Nat
  | 0 => 2*(v152FibonacciBounds 0).2
  | t+1 =>
      v152FibonacciPathBudget t+
        2*(v152FibonacciBounds (t+1)).2

theorem v152_terminal_path_budget_bounded (t : Nat) :
    v152TerminalPathBudget t ≤ v152FibonacciPathBudget t := by
  induction t with
  | zero =>
      decide
  | succ t ih =>
      have ha := v152_inverse_words_global_fibonacci (t+1) 1
      have hb := v152_inverse_words_global_fibonacci (t+1) 2
      simp only [v152TerminalPathBudget,v152FibonacciPathBudget]
      omega

/-- For EACH FIXED forward horizon and reciprocal precision, some
    dyadic scale dwarfs the total number of terminal paths. This
    proves why a fixed-time terminal search cannot be the missing
    all-scale density certificate. It does NOT deny eventual
    convergence at a source-dependent unbounded horizon. -/
theorem v152_fixed_terminal_horizon_cannot_supply_density
    (t q : Nat) :
    ∃ k : Nat, q*v152TerminalPathBudget t < 2^k := by
  let k := q*v152TerminalPathBudget t
  refine ⟨k, ?_⟩
  exact pow_two_exceeds_its_index k

#print axioms v152_one_step_reverse_complete
#print axioms v152_reverse_sources_sound
#print axioms v152_reverse_sources_complete
#print axioms v152_inverse_sources_length
#print axioms v152_inverse_words_global_fibonacci
#print axioms v152_terminal_path_budget_bounded
#print axioms v152_fixed_terminal_horizon_cannot_supply_density

end SourceProduct
end CollatzFinal
