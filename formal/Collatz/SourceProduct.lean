import Collatz.Shortcut

namespace CollatzFinal
namespace SourceProduct

structure State where
  source : Nat
  depth : Nat
  odds : Nat
  tail : Nat
  sourceResidue : Nat
  endpointResidue : Nat
  deriving DecidableEq, Repr

def endpoint (s : State) : Nat :=
  s.endpointResidue + 3 ^ s.odds * s.tail

def Valid (s : State) : Prop :=
  0 < s.source ∧
  s.sourceResidue < 2 ^ s.depth ∧
  s.endpointResidue < 3 ^ s.odds ∧
  s.source = s.sourceResidue + 2 ^ s.depth * s.tail

def start (n : Nat) : State := ⟨n, 0, 0, n, 0, 0⟩

def step (s : State) : State :=
  let v := s.endpointResidue + 3 ^ s.odds * (s.tail % 2)
  { source := s.source
    depth := s.depth + 1
    odds := if v % 2 = 0 then s.odds else s.odds + 1
    tail := s.tail / 2
    sourceResidue := s.sourceResidue + 2 ^ s.depth * (s.tail % 2)
    endpointResidue := shortcut v }

def stateAt (n : Nat) : Nat → State
  | 0 => start n
  | k + 1 => step (stateAt n k)

theorem split_mul (a u : Nat) :
    a * u = a * (u % 2) + 2 * (a * (u / 2)) := by
  calc
    a * u = a * (u % 2 + 2 * (u / 2)) :=
      congrArg (fun x => a * x) (Nat.mod_add_div u 2).symm
    _ = _ := by simp [Nat.mul_add, Nat.mul_left_comm]

theorem shortcut_shift (x z : Nat) :
    shortcut (x + 2 * z) =
      shortcut x + (if x % 2 = 0 then z else 3 * z) := by
  by_cases hx : x % 2 = 0
  · have hp : (x + 2 * z) % 2 = 0 := by omega
    simp only [shortcut, hx, hp, ite_true]
    omega
  · have hp : ¬ (x + 2 * z) % 2 = 0 := by omega
    simp only [shortcut, hx, hp, ite_false]
    omega

theorem step_endpoint (s : State) :
    endpoint (step s) = shortcut (endpoint s) := by
  let v := s.endpointResidue + 3 ^ s.odds * (s.tail % 2)
  have hy : endpoint s = v + 2 * (3 ^ s.odds * (s.tail / 2)) := by
    dsimp [endpoint, v]
    rw [split_mul (3 ^ s.odds) s.tail]
    simp [Nat.add_assoc]
  change shortcut v +
    3 ^ (if v % 2 = 0 then s.odds else s.odds + 1) * (s.tail / 2) = _
  rw [hy, shortcut_shift]
  by_cases h : v % 2 = 0 <;>
    simp [h, Nat.pow_succ, Nat.mul_left_comm, Nat.mul_comm]

theorem start_valid {n : Nat} (hn : 0 < n) : Valid (start n) := by
  simpa [Valid, start] using hn

theorem step_valid {s : State} (hs : Valid s) : Valid (step s) := by
  rcases hs with ⟨hn, hr, hd, he⟩
  let v := s.endpointResidue + 3 ^ s.odds * (s.tail % 2)
  have hb : s.tail % 2 = 0 ∨ s.tail % 2 = 1 := by omega
  have hv : v < 2 * 3 ^ s.odds := by
    rcases hb with hb | hb
    · dsimp [v]
      simp only [hb, Nat.mul_zero, Nat.add_zero]
      omega
    · dsimp [v]
      simp only [hb, Nat.mul_one]
      omega
  change 0 < s.source ∧
    s.sourceResidue + 2 ^ s.depth * (s.tail % 2) < 2 ^ (s.depth + 1) ∧
    shortcut v < 3 ^ (if v % 2 = 0 then s.odds else s.odds + 1) ∧
    s.source = s.sourceResidue + 2 ^ s.depth * (s.tail % 2) +
      2 ^ (s.depth + 1) * (s.tail / 2)
  refine ⟨hn, ?_, ?_, ?_⟩
  · rcases hb with hb | hb <;>
      simp only [hb, Nat.mul_zero, Nat.mul_one, Nat.add_zero, Nat.pow_succ] <;>
      omega
  · by_cases h : v % 2 = 0
    · simp only [h, ite_true, shortcut]
      omega
    · simp only [h, ite_false, shortcut, Nat.pow_succ]
      omega
  · calc
      s.source = s.sourceResidue + 2 ^ s.depth * s.tail := he
      _ = _ := by
        rw [split_mul (2 ^ s.depth) s.tail]
        simp [Nat.pow_succ, Nat.add_assoc, Nat.mul_assoc, Nat.mul_left_comm]

theorem at_valid {n : Nat} (hn : 0 < n) (k : Nat) : Valid (stateAt n k) := by
  induction k with
  | zero => exact start_valid hn
  | succ k ih => exact step_valid ih

theorem at_source (n k : Nat) : (stateAt n k).source = n := by
  induction k with
  | zero => rfl
  | succ k ih => exact ih

theorem at_depth (n k : Nat) : (stateAt n k).depth = k := by
  induction k with
  | zero => rfl
  | succ k ih => simpa only [stateAt, step] using congrArg Nat.succ ih

theorem iter_succ_last (n k : Nat) :
    iter shortcut (k + 1) n = shortcut (iter shortcut k n) := by
  simpa [iter] using iter_add shortcut k 1 n

theorem at_endpoint (n k : Nat) :
    endpoint (stateAt n k) = iter shortcut k n := by
  induction k with
  | zero => simp [stateAt, start, endpoint, iter]
  | succ k ih =>
      rw [stateAt, step_endpoint, ih, iter_succ_last]

/-- Every positive source and every depth has the same exact product form. -/
theorem universal_normalization {n : Nat} (hn : 0 < n) (k : Nat) :
    ∃ q r d u : Nat,
      r < 2 ^ k ∧ d < 3 ^ q ∧
      n = r + 2 ^ k * u ∧
      iter shortcut k n = d + 3 ^ q * u := by
  let s := stateAt n k
  have hs := at_valid hn k
  refine ⟨s.odds, s.sourceResidue, s.endpointResidue, s.tail, ?_, hs.2.2.1, ?_, ?_⟩
  · simpa [s, at_depth] using hs.2.1
  · simpa [s, at_source, at_depth] using hs.2.2.2
  · exact (at_endpoint n k).symm

theorem common_tail {s : State} (hs : Valid s) :
    s.source / 2 ^ s.depth = s.tail ∧
    endpoint s / 3 ^ s.odds = s.tail := by
  rcases hs with ⟨_, hr, hd, he⟩
  constructor
  · rw [he, Nat.add_mul_div_left _ _ (by omega), Nat.div_eq_of_lt hr]
    simp
  · change (s.endpointResidue + 3 ^ s.odds * s.tail) / 3 ^ s.odds = s.tail
    rw [Nat.add_mul_div_left _ _ (by omega), Nat.div_eq_of_lt hd]
    simp

theorem all_depth_common_tail {n : Nat} (hn : 0 < n) (k : Nat) :
    iter shortcut k n / 3 ^ (stateAt n k).odds = n / 2 ^ k := by
  have h := common_tail (at_valid hn k)
  have e := h.2.trans h.1.symm
  simpa only [at_endpoint, at_source, at_depth] using e

theorem tail_strict_until_zero (s : State) (h : 0 < s.tail) :
    (step s).tail < s.tail := by
  change s.tail / 2 < s.tail
  omega

theorem tail_zero_persists (s : State) (h : s.tail = 0) :
    (step s).tail = 0 := by
  simp [step, h]

/-- This presentation quotient is exact but still has an unbounded state space. -/
def projection (s : State) : Nat × Nat := (s.source, endpoint s)

theorem projection_step (s : State) :
    projection (step s) = (s.source, shortcut (endpoint s)) := by
  change ((step s).source, endpoint (step s)) = (s.source, shortcut (endpoint s))
  rw [step_endpoint]
  rfl

/-- Zero is excluded from the counterexample domain. -/
def PositiveBad (n : Nat) : Prop := 0 < n ∧ ¬ CollatzGood n

theorem zero_not_positive_bad : ¬ PositiveBad 0 := by
  simp [PositiveBad]

theorem shortcut_positive (n : Nat) (hn : 0 < n) : 0 < shortcut n := by
  unfold shortcut
  split <;> omega

theorem positive_minimal_no_lower_merge {n : Nat}
    (hmin : MinimalBad PositiveBad n) :
    ∀ p, 0 < p → ¬ LowerMerge shortcut n p := by
  intro p hp hm
  have hpGood : CollatzGood p := by
    apply Classical.byContradiction
    intro hb
    exact hmin.2 p hm.1 ⟨hp, hb⟩
  exact hmin.1.2
    (lower_merge_preserves_eventual shortcut Terminal terminal_forward_invariant hm hpGood)

/-- Exit candidates; a minimal positive bad source excludes all three. -/
def Exit (s : State) : Prop :=
  Terminal (endpoint s) ∨
  (0 < endpoint s ∧ endpoint s < s.source) ∨
  ∃ p b, 0 < p ∧ p < s.source ∧ iter shortcut b p = endpoint s

def Reachable (s : State) : Prop :=
  ∃ n k, 0 < n ∧ s = stateAt n k

def Live (s : State) : Prop := Reachable s ∧ ¬ Exit s

def Next (s t : State) : Prop := t = step s

theorem minimal_path_no_exit {n : Nat}
    (hmin : MinimalBad PositiveBad n) (k : Nat) : ¬ Exit (stateAt n k) := by
  intro he
  rcases he with ht | hd | hm
  · exact hmin.1.2 ⟨k, by simpa [at_endpoint] using ht⟩
  · have hp := hd.1
    have hlt : endpoint (stateAt n k) < n := by simpa [at_source] using hd.2
    apply positive_minimal_no_lower_merge hmin (endpoint (stateAt n k)) hp
    exact ⟨hlt, k, 0, by simp [iter, at_endpoint]⟩
  · obtain ⟨p, b, hp, hlt, heq⟩ := hm
    apply positive_minimal_no_lower_merge hmin p hp
    refine ⟨by simpa [at_source] using hlt, k, b, ?_⟩
    simpa [at_endpoint] using heq.symm

/-- The whole path, not arbitrary local no-exit states, is post-fixed. -/
theorem minimal_path_postfixed {n : Nat}
    (_hmin : MinimalBad PositiveBad n) :
    PostFixed Next (fun s => ∃ k, s = stateAt n k) := by
  intro s hs
  obtain ⟨k, rfl⟩ := hs
  exact ⟨stateAt n (k + 1), rfl, k + 1, rfl⟩

theorem minimal_path_live {n : Nat}
    (hmin : MinimalBad PositiveBad n) :
    ∀ s, (∃ k, s = stateAt n k) → Live s := by
  intro s hs
  obtain ⟨k, rfl⟩ := hs
  exact ⟨⟨n, k, hmin.1.1, rfl⟩, minimal_path_no_exit hmin k⟩

/-- This closes Collatz only when the stated kernel-emptiness premise is supplied. -/
theorem collatz_of_product_kernel_empty
    (hempty : KernelEmpty Live Next) :
    ∀ n, 0 < n → CollatzGood n := by
  have hnone : ∀ n, ¬ PositiveBad n := by
    apply no_bad_of_no_minimal PositiveBad
    intro n hmin
    exact hempty (fun s => ∃ k, s = stateAt n k)
      (minimal_path_live hmin) (minimal_path_postfixed hmin)
      (stateAt n 0) ⟨0, rfl⟩
  intro n hn
  apply Classical.byContradiction
  intro hb
  exact hnone n ⟨hn, hb⟩

/-- A quotient must preserve actual residual transitions before rank can be used. -/
theorem collatz_of_ranked_simulation
    {Q : Type} (project : State → Q) (edge : Q → Q → Prop)
    (rank : Q → Nat)
    (hstep : ∀ s t, Live s → Next s t → edge (project s) (project t))
    (hdecrease : ∀ s t, Live s → edge (project s) (project t) →
      rank (project t) < rank (project s)) :
    ∀ n, 0 < n → CollatzGood n := by
  apply collatz_of_product_kernel_empty
  apply kernel_empty_of_rank Live Next (fun s => rank (project s))
  intro s t hs hst
  exact hdecrease s t hs (hstep s t hs hst)

/-- Every minimal positive bad source is odd: an even source immediately merges
    with its smaller positive shortcut successor. -/
theorem positive_minimal_bad_odd {n : Nat}
    (hmin : MinimalBad PositiveBad n) : n % 2 = 1 := by
  have hpar : n % 2 = 0 ∨ n % 2 = 1 := by omega
  rcases hpar with he | ho
  · have hp : 0 < shortcut n := shortcut_positive n hmin.1.1
    apply False.elim
    apply positive_minimal_no_lower_merge hmin (shortcut n) hp
    refine ⟨?_, 1, 0, ?_⟩
    · have hlt : n / 2 < n := Nat.div_lt_self hmin.1.1 (by omega)
      simpa [shortcut, he] using hlt
    · simp [iter]
  · exact ho

theorem odd_difference_even {n y : Nat}
    (hn : n % 2 = 1) (hy : y % 2 = 1) :
    (y - n) % 2 = 0 := by
  omega

-- A zero tail is not a terminal witness and is not a global strict rank.
example : (stateAt 27 5).tail = 0 ∧ (stateAt 27 6).tail = 0 ∧
    endpoint (stateAt 27 5) = 71 ∧ endpoint (stateAt 27 6) = 107 := by
  decide

-- Equal endpoints need not have equal source-relative descent outcomes.
example : endpoint (stateAt 3 1) = endpoint (stateAt 6 2) ∧
    ¬ endpoint (stateAt 3 1) < (stateAt 3 1).source ∧
    endpoint (stateAt 6 2) < (stateAt 6 2).source := by
  decide

#print axioms universal_normalization
#print axioms all_depth_common_tail
#print axioms step_endpoint
#print axioms positive_minimal_bad_odd
#print axioms odd_difference_even
#print axioms minimal_path_live
#print axioms collatz_of_product_kernel_empty
#print axioms collatz_of_ranked_simulation

end SourceProduct
end CollatzFinal

