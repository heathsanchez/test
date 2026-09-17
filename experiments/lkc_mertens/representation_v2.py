#!/usr/bin/env python3
"""Generate isolated, algorithmic Mertens candidates. No precomputed answers."""
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'generated'
OUT.mkdir(exist_ok=True)
runpy.run_path(str(ROOT / 'singlepass_v1.py'))
baseline = (OUT / 'Submission_v1.lean').read_text()
assert baseline.count('def impl (n : Nat)') == 1
prefix = baseline.split('def impl (n : Nat)')[0]

ADJACENT = r'''
/-- Equal entries in a sorted list occur consecutively. -/
def moebiusAdjacent : List Nat → Int
  | [] => 1
  | [_] => -1
  | a :: b :: xs => if a = b then 0 else -moebiusAdjacent (b :: xs)

theorem head_mem_iff_adjacent (a b : Nat) (xs : List Nat)
    (hs : (a :: b :: xs).Pairwise (· ≤ ·)) :
    a ∈ b :: xs ↔ a = b := by
  rcases List.pairwise_cons.mp hs with ⟨ha, hb⟩
  constructor
  · intro hm
    rcases List.mem_cons.mp hm with he | ht
    · exact he
    · have hab : a ≤ b := ha b (by simp)
      have hba : b ≤ a := (List.pairwise_cons.mp hb).1 a ht
      exact Nat.le_antisymm hab hba
  · intro he
    simp [he]

theorem moebiusAdjacent_eq (xs : List Nat)
    (hs : xs.Pairwise (· ≤ ·)) : moebiusAdjacent xs = moebiusList xs := by
  induction xs with
  | nil => rfl
  | cons a xs ih =>
      cases xs with
      | nil => simp [moebiusAdjacent, moebiusList]
      | cons b xs =>
          have ht := (List.pairwise_cons.mp hs).2
          rw [moebiusAdjacent, moebiusList]
          simp only [head_mem_iff_adjacent a b xs hs, ih ht]

def moebiusAdjacentSingle (n : Nat) : Int :=
  if n = 0 then 0 else moebiusAdjacent n.primeFactorsList

theorem moebiusAdjacentSingle_eq (n : Nat) :
    moebiusAdjacentSingle n = ArithmeticFunction.moebius n := by
  by_cases hn : n = 0
  · subst n
    simp [moebiusAdjacentSingle]
  · unfold moebiusAdjacentSingle
    rw [if_neg hn, moebiusAdjacent_eq _ (Nat.primeFactorsList_sorted n).pairwise]
    simpa only [moebiusSingle, if_neg hn] using moebiusSingle_eq n
'''

SUM = r'''
/-- Traverse the inclusive positive range without materializing a Finset. -/
def sumDown (f : Nat → Int) : Nat → Int → Int
  | 0, acc => acc
  | k + 1, acc => sumDown f k (acc + f (k + 1))

theorem sumDown_eq (f : Nat → Int) (n : Nat) (acc : Int) :
    sumDown f n acc = acc + ∑ i ∈ Finset.range n, f (i + 1) := by
  induction n generalizing acc with
  | zero => simp [sumDown]
  | succ n ih =>
      simp only [sumDown, ih, Finset.sum_range_succ]
      omega

theorem sumDown_correct (f : Nat → Int)
    (hf : ∀ n, f n = ArithmeticFunction.moebius n) (n : Nat) :
    sumDown f n 0 = mertensSpec n := by
  rw [sumDown_eq, zero_add]
  simp only [hf]
  unfold mertensSpec
  rw [Finset.sum_range_succ']
  simp
'''

FUSED = r'''
/-- Consume the least factor immediately; repeated factors terminate at zero.
Fuel is a termination device, not a table or restriction on inputs. -/
def moebiusFusedFuel : Nat → Nat → Int
  | 0, _ => 0
  | fuel + 1, n =>
      if n = 0 then 0
      else if n = 1 then 1
      else
        let p := n.minFac
        let q := n / p
        if q % p = 0 then 0 else -moebiusFusedFuel fuel q

theorem moebius_factor_step (n : Nat) (hn0 : n ≠ 0) (hn1 : n ≠ 1) :
    ArithmeticFunction.moebius n =
      if (n / n.minFac) % n.minFac = 0 then 0
      else -ArithmeticFunction.moebius (n / n.minFac) := by
  have hn2 : 2 ≤ n := by omega
  have hp : n.minFac.Prime := Nat.minFac_prime hn1
  have hqpos : 0 < n / n.minFac :=
    Nat.div_pos (Nat.minFac_le (by omega)) hp.pos
  have hq0 : n / n.minFac ≠ 0 := by omega
  have heq : n.primeFactorsList =
      n.minFac :: (n / n.minFac).primeFactorsList := by
    have h := Nat.primeFactorsList_add_two (n - 2)
    have he : n - 2 + 2 = n := by omega
    rw [he] at h
    exact h
  have hmem : n.minFac ∈ (n / n.minFac).primeFactorsList ↔
      (n / n.minFac) % n.minFac = 0 := by
    rw [Nat.mem_primeFactorsList_iff_dvd hq0 hp, Nat.dvd_iff_mod_eq_zero]
  have hval := moebiusSingle_eq n
  have hqval := moebiusSingle_eq (n / n.minFac)
  simp only [moebiusSingle, if_neg hn0] at hval
  simp only [moebiusSingle, if_neg hq0] at hqval
  rw [← hval, heq, moebiusList]
  simp only [hmem, hqval]

theorem moebiusFusedFuel_eq (fuel : Nat) : ∀ n, n < fuel →
    moebiusFusedFuel fuel n = ArithmeticFunction.moebius n := by
  induction fuel with
  | zero => intro n hn; omega
  | succ fuel ih =>
      intro n hn
      by_cases hn0 : n = 0
      · subst n
        simp [moebiusFusedFuel]
      · by_cases hn1 : n = 1
        · subst n
          simp [moebiusFusedFuel]
        · have hn2 : 2 ≤ n := by omega
          have hp : n.minFac.Prime := Nat.minFac_prime hn1
          have hsmall : n / n.minFac < n :=
            Nat.div_lt_self (by omega) (by have := hp.two_le; omega)
          rw [moebiusFusedFuel, if_neg hn0, if_neg hn1]
          change (if (n / n.minFac) % n.minFac = 0 then 0
            else -moebiusFusedFuel fuel (n / n.minFac)) = _
          rw [ih (n / n.minFac) (by omega), moebius_factor_step n hn0 hn1]

def moebiusFused (n : Nat) : Int := moebiusFusedFuel (n + 1) n

theorem moebiusFused_eq (n : Nat) :
    moebiusFused n = ArithmeticFunction.moebius n :=
  moebiusFusedFuel_eq (n + 1) n (by omega)
'''

variants = {
    'v2': (ADJACENT, 'moebiusAdjacentSingle', False),
    'v3': (SUM, 'moebiusSingle', True),
    'v4': (ADJACENT + SUM, 'moebiusAdjacentSingle', True),
    'v5': (FUSED + SUM, 'moebiusFused', True),
}
for name, (middle, fn, tail) in variants.items():
    expression = f'sumDown {fn} n 0' if tail else f'∑ k ∈ Finset.range (n + 1), {fn} k'
    proof = (f'  intro n\n  exact sumDown_correct {fn} {fn}_eq n' if tail else
             f'  intro n\n  simp only [impl, mertensSpec, {fn}_eq]')
    text = prefix + middle + f'\ndef impl (n : Nat) : Int := {expression}\n\n'
    text += 'theorem impl_correct : ∀ n, impl n = mertensSpec n := by\n' + proof + '\n\nend Submission\n'
    assert len(text.encode()) <= 1048576
    assert all(word not in text for word in ['sorry', 'admit', 'native_decide', 'unsafe ', 'partial '])
    path = OUT / f'Submission_{name}.lean'
    path.write_text(text)
    print(f'{name}: {path} ({len(text.encode())} bytes)')
