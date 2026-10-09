import Collatz.RelationalOddRootInterface

namespace CollatzFinal

/-!
V130 — class-preserving root pump and universal UNBOUNDED odd-3-root
representatives.

For any positive odd three-root r, define P(r)=64r+21.
P(r) is also odd, divisible by 3, and
  T^7(P(r)) = T(r).
Repeated pumping has explicit *actual two-clock* future witnesses:
  T^(6*k+1)(P^k(r)) = T(r).
P^k(r) grows without bound in k.

Because V129 proves that EVERY positive source meets an odd three-root,
EVERY positive future-coalescence class contains arbitrarily large ODD
multiples of three, with a checkable pair of shortcut clocks.

This is a rigorous NEGATIVE control on completeness by finite root support
or by root-magnitude descent: even the terminal class has arbitrarily
large odd-three representatives. Not a Collatz proof.
-/

def rootPump (r : Nat) : Nat := 64 * r + 21

def rootPumpIter (r : Nat) : Nat → Nat
  | 0 => r
  | k+1 => rootPump (rootPumpIter r k)

theorem rootPump_preserves_odd_three
    (r : Nat) (hr : r % 6 = 3) :
    rootPump r % 6 = 3 := by
  unfold rootPump
  omega

theorem rootPump_seven_meets_one
    (r : Nat) (hr : r % 2 = 1) :
    iter shortcut 7 (rootPump r) = iter shortcut 1 r := by
  have hne : r % 2 ≠ 0 := by omega
  have hpodd : (64 * r + 21) % 2 ≠ 0 := by omega
  have hsingle : shortcut r = (3 * r + 1) / 2 := by
    simp only [shortcut, if_neg hne]
  have hpumped : shortcut (rootPump r) = 96 * r + 32 := by
    unfold rootPump
    simp only [shortcut, if_neg hpodd]
    omega
  have hscaled : 64 * shortcut r = 96 * r + 32 := by
    rw [hsingle]
    omega
  have hstep : shortcut (rootPump r) = 64 * shortcut r := by
    rw [hpumped, hscaled]
  have hsix : iter shortcut 6 (64 * shortcut r) = shortcut r := by
    have hpow : (2 : Nat) ^ 6 = 64 := by decide
    simpa only [hpow] using
      (three_reverse_ray_exists 6 (shortcut r))
  calc
    iter shortcut 7 (rootPump r) =
        iter shortcut 6 (shortcut (rootPump r)) := rfl
    _ = iter shortcut 6 (64 * shortcut r) := by rw [hstep]
    _ = shortcut r := hsix
    _ = iter shortcut 1 r := rfl

theorem rootPumpIter_preserves_odd_three
    (r : Nat) (hr : r % 6 = 3) :
    ∀ k : Nat, rootPumpIter r k % 6 = 3 := by
  intro k
  induction k with
  | zero =>
      simpa [rootPumpIter] using hr
  | succ k ih =>
      change rootPump (rootPumpIter r k) % 6 = 3
      exact rootPump_preserves_odd_three _ ih

/-- A source-independent proof of unbounded growth of root coordinates. -/
theorem rootPumpIter_at_least_index (r : Nat) :
    ∀ k : Nat, k ≤ rootPumpIter r k := by
  intro k
  induction k with
  | zero => omega
  | succ k ih =>
      change k+1 ≤ rootPump (rootPumpIter r k)
      unfold rootPump
      omega

/-- The same certified future class after EVERY finite pump iteration.
    Both REAL meeting clocks remain explicit. -/
theorem rootPumpIter_actual_future_join
    (r : Nat) (hr : r % 6 = 3) :
    ∀ k : Nat,
      iter shortcut (6 * k + 1) (rootPumpIter r k) =
      iter shortcut 1 r := by
  intro k
  induction k with
  | zero =>
      rfl
  | succ k ih =>
      have hres := rootPumpIter_preserves_odd_three r hr k
      have hodd : (rootPumpIter r k) % 2 = 1 := by omega
      have hseven := rootPump_seven_meets_one (rootPumpIter r k) hodd
      have heq : 6 * (k + 1) + 1 = 7 + 6 * k := by omega
      change iter shortcut (6 * (k + 1) + 1)
        (rootPump (rootPumpIter r k)) = iter shortcut 1 r
      rw [heq]
      calc
        iter shortcut (7 + 6 * k) (rootPump (rootPumpIter r k)) =
            iter shortcut (6 * k)
              (iter shortcut 7 (rootPump (rootPumpIter r k))) :=
          iter_add shortcut 7 (6 * k) _
        _ = iter shortcut (6 * k) (iter shortcut 1 (rootPumpIter r k)) :=
          congrArg (iter shortcut (6 * k)) hseven
        _ = iter shortcut (1 + 6 * k) (rootPumpIter r k) :=
          (iter_add shortcut 1 (6 * k) _).symm
        _ = iter shortcut (6 * k + 1) (rootPumpIter r k) := by rw [Nat.add_comm]
        _ = iter shortcut 1 r := ih

/-- For EVERY bound, the coalescence class of ANY positive odd-three
    representative contains a STRICTLY LARGER odd-three representative.
    Thus a finite candidate-root universe CANNOT exhaust the actual
    future class. -/
theorem odd_three_class_has_arbitrarily_large_roots
    (r B : Nat) (hr : r % 6 = 3) :
    ∃ s a b : Nat,
      B < s ∧ s % 6 = 3 ∧
      iter shortcut a r = iter shortcut b s := by
  let k := B + 1
  let s := rootPumpIter r k
  have hsroot : s % 6 = 3 :=
    rootPumpIter_preserves_odd_three r hr k
  have hlarge : B < s := by
    have hx := rootPumpIter_at_least_index r (B + 1)
    change B < rootPumpIter r (B + 1)
    omega
  have hmerge :=
    (rootPumpIter_actual_future_join r hr k).symm
  exact ⟨s, 1, 6 * k + 1, hlarge, hsroot, hmerge⟩

/-- A generic, *typed*, two-clock root-class certificate can be
    constructed for any arbitrarily high representative. No
    smaller-source inequality is claimed or implied. -/
theorem every_positive_class_has_unbounded_odd_three_witnesses
    (n B : Nat) (hn : 0 < n) :
    ∃ w : OddThreeRootClassWitness n, B < w.root := by
  obtain ⟨w⟩ := root_witness_exists_for_every_positive n hn
  let k := B + 1
  let largerRoot := rootPumpIter w.root k
  have hres : largerRoot % 6 = 3 :=
    rootPumpIter_preserves_odd_three w.root w.residue k
  have hpositive : 0 < largerRoot := by omega
  have hgrowth : B < largerRoot := by
    have hx := rootPumpIter_at_least_index w.root (B + 1)
    change B < rootPumpIter w.root (B + 1)
    omega
  have hbridge :
      iter shortcut 1 w.root =
      iter shortcut (6 * k + 1) largerRoot := by
    exact (rootPumpIter_actual_future_join w.root w.residue k).symm
  have hjoin :
      iter shortcut (w.sourceClock + 1) n =
      iter shortcut ((6 * k + 1) + w.rootClock) largerRoot :=
    LawfulFutureJoin.compose_meets w.common hbridge
  let next : OddThreeRootClassWitness n :=
    { root := largerRoot
      sourceClock := w.sourceClock + 1
      rootClock := (6 * k + 1) + w.rootClock
      positive := hpositive
      residue := hres
      common := hjoin }
  exact ⟨next, hgrowth⟩

#print axioms rootPump_preserves_odd_three
#print axioms rootPump_seven_meets_one
#print axioms rootPumpIter_preserves_odd_three
#print axioms rootPumpIter_at_least_index
#print axioms rootPumpIter_actual_future_join
#print axioms odd_three_class_has_arbitrarily_large_roots
#print axioms every_positive_class_has_unbounded_odd_three_witnesses

end CollatzFinal
