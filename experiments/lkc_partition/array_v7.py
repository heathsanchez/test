#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

text=r'''import Spec
import Init.Data.Nat.Fold
import Init.Data.Array.Lemmas

namespace Submission

def initialRow (n : Nat) : List Nat :=
  (List.range (n + 1)).map fun m => if m = 0 then 1 else 0

/-- V4 semantic bridge. -/
def nextRow (k n : Nat) (prev : List Nat) : List Nat :=
  (List.range (n + 1)).map fun m =>
    ((List.range (m / (k + 1) + 1)).map
      (fun j => prev.getD (m - j * (k + 1)) 0)).foldl (· + ·) 0

def buildRows : Nat → Nat → List Nat
  | 0, n => initialRow n
  | k + 1, n => nextRow k n (buildRows k n)

def sumFold (q : Nat) (f : Nat → Nat) : Nat :=
  Nat.fold q (fun i _ acc => acc + f i) 0

theorem sumFold_succ (q : Nat) (f : Nat → Nat) :
    sumFold (q + 1) f = sumFold q f + f q := by
  rfl

theorem sumFold_shift :
    ∀ q (f : Nat → Nat),
      sumFold (q + 1) f = f 0 + sumFold q (fun j => f (j + 1))
  | 0, f => by
      simp [sumFold, Nat.fold]
  | q + 1, f => by
      rw [sumFold_succ, sumFold_shift q f, sumFold_succ]
      simp [Nat.add_assoc]

theorem sumFold_congr :
    ∀ q (f g : Nat → Nat),
      (∀ i, i < q → f i = g i) →
      sumFold q f = sumFold q g
  | 0, f, g, h => rfl
  | q + 1, f, g, h => by
      rw [sumFold_succ, sumFold_succ]
      rw [sumFold_congr q f g (fun i hi => h i (by omega))]
      rw [h q (by omega)]

def rowValue (step : Nat) (prev : List Nat) (m : Nat) : Nat :=
  sumFold (m / step + 1)
    (fun j => prev.getD (m - j * step) 0)

theorem rowValue_recurrence
    (step : Nat) (prev : List Nat) (m : Nat) (hs : 0 < step) :
    rowValue step prev m =
      prev.getD m 0 +
        (if step ≤ m then rowValue step prev (m - step) else 0) := by
  by_cases hle : step ≤ m
  · rw [if_pos hle]
    unfold rowValue
    rw [sumFold_shift]
    simp only [Nat.zero_mul, Nat.sub_zero]
    have hdiv : m / step = (m - step) / step + 1 := by
      conv => lhs
              rw [show m = (m - step) + step by omega]
      rw [Nat.add_div_right _ hs]
    rw [hdiv]
    apply congrArg (fun x => prev.getD m 0 + x)
    apply sumFold_congr
    intro j hj
    simp only [Nat.add_mul, Nat.one_mul, Nat.sub_sub]
    congr 2
    omega
  · rw [if_neg hle]
    have hlt : m < step := by omega
    unfold rowValue
    rw [Nat.div_eq_of_lt hlt]
    simp [sumFold, Nat.fold]

theorem natFold_sum_eq_list (f : Nat → Nat) :
    ∀ q, Nat.fold q (fun i _ acc => acc + f i) 0 =
      ((List.range q).map f).foldl (· + ·) 0
  | 0 => rfl
  | q + 1 => by
      rw [Nat.fold_succ, List.range_succ, List.map_append, List.foldl_append]
      simp only [List.map, List.foldl_cons, List.foldl_nil]
      rw [natFold_sum_eq_list f q]

theorem sumFold_eq_list (q : Nat) (f : Nat → Nat) :
    sumFold q f = ((List.range q).map f).foldl (· + ·) 0 := by
  exact natFold_sum_eq_list f q

def nextRowFold (k n : Nat) (prev : List Nat) : List Nat :=
  (List.range (n + 1)).map fun m =>
    rowValue (k + 1) prev m

theorem nextRowFold_eq (k n : Nat) (prev : List Nat) :
    nextRowFold k n prev = nextRow k n prev := by
  unfold nextRowFold nextRow rowValue
  apply List.map_congr_left
  intro m hm
  exact sumFold_eq_list
    (m / (k + 1) + 1)
    (fun j => prev.getD (m - j * (k + 1)) 0)

/-- Array and list indexing are observationally identical. -/
theorem array_getD_toList (xs : Array Nat) (i : Nat) :
    xs.getD i 0 = xs.toList.getD i 0 := by
  by_cases hi : i < xs.size
  · have hil : i < xs.toList.length := by simpa using hi
    simp only [Array.getD, hi, dite_true]
    rw [List.getD_eq_getElem?_getD, List.getElem?_eq_getElem hil]
    simp only [Option.getD_some]
    symm
    exact Array.getElem_toList (xs := xs) (i := i) hil
  · have hil : ¬ i < xs.toList.length := by simpa using hi
    simp [Array.getD, hi, List.getD_eq_getElem?_getD,
      List.getElem?_eq_none (Nat.le_of_not_gt hil)]

/--
Build a row left-to-right in an Array.  Every cell reuses two indexed values:
one from the previous row and, when available, one already pushed in this row.
-/
def streamArray (step : Nat) (prev : Array Nat) : Nat → Array Nat
  | 0 => #[]
  | m + 1 =>
      let curr := streamArray step prev m
      let x :=
        prev.getD m 0 +
          (if step ≤ m then curr.getD (m - step) 0 else 0)
      curr.push x

theorem range_map_getD
    (f : Nat → Nat) (count i fallback : Nat) (h : i < count) :
    ((List.range count).map f).getD i fallback = f i := by
  simp only [List.getD_eq_getElem?_getD, List.getElem?_map]
  rw [List.getElem?_range h]
  simp

theorem streamArray_toList
    (step : Nat) (prev : Array Nat) (hs : 0 < step) :
    ∀ count,
      (streamArray step prev count).toList =
        (List.range count).map (rowValue step prev.toList)
  | 0 => rfl
  | m + 1 => by
      simp only [streamArray, Array.toList_push, List.range_succ,
        List.map_append, List.map]
      rw [streamArray_toList step prev hs m]
      congr 1
      rw [rowValue_recurrence step prev.toList m hs]
      rw [array_getD_toList prev m]
      by_cases hle : step ≤ m
      · simp only [if_pos hle]
        rw [array_getD_toList (streamArray step prev m) (m - step)]
        rw [streamArray_toList step prev hs m]
        rw [range_map_getD (rowValue step prev.toList) m (m - step) 0 (by omega)]
      · simp only [if_neg hle]

def nextRowArray (k n : Nat) (prev : Array Nat) : Array Nat :=
  streamArray (k + 1) prev (n + 1)

theorem nextRowArray_toList (k n : Nat) (prev : Array Nat) :
    (nextRowArray k n prev).toList =
      nextRowFold k n prev.toList := by
  unfold nextRowArray nextRowFold
  exact streamArray_toList (k + 1) prev (by omega) (n + 1)

def buildRowsArray : Nat → Nat → Array Nat
  | 0, n => (initialRow n).toArray
  | k + 1, n => nextRowArray k n (buildRowsArray k n)

theorem buildRowsArray_toList :
    ∀ k n, (buildRowsArray k n).toList = buildRows k n
  | 0, n => by
      simp [buildRowsArray, buildRows]
  | k + 1, n => by
      simp only [buildRowsArray, buildRows]
      rw [nextRowArray_toList]
      rw [buildRowsArray_toList k n]
      rw [nextRowFold_eq]

theorem initialRow_getD (n m : Nat) (h : m ≤ n) :
    (initialRow n).getD m 0 = partAux 0 m := by
  rw [initialRow, range_map_getD (h := by omega)]
  cases m <;> rfl

theorem nextRow_getD
    (k n : Nat) (prev : List Nat)
    (hprev : ∀ m, m ≤ n → prev.getD m 0 = partAux k m)
    (m : Nat) (hm : m ≤ n) :
    (nextRow k n prev).getD m 0 = partAux (k + 1) m := by
  rw [nextRow, range_map_getD (h := by omega)]
  unfold partAux
  have hmap :
      (List.range (m / (k + 1) + 1)).map
          (fun j => prev.getD (m - j * (k + 1)) 0) =
        (List.range (m / (k + 1) + 1)).map
          (fun j => partAux k (m - j * (k + 1))) := by
    apply List.map_congr_left
    intro j hj
    apply hprev
    omega
  rw [hmap]

theorem buildRows_getD :
    ∀ k n m, m ≤ n → (buildRows k n).getD m 0 = partAux k m
  | 0, n, m, hm => initialRow_getD n m hm
  | k + 1, n, m, hm => by
      apply nextRow_getD k n (buildRows k n)
      · intro x hx
        exact buildRows_getD k n x hx
      · exact hm

def partitionArray (n : Nat) : Nat :=
  (buildRowsArray n n).getD n 0

def impl : Nat → Nat := partitionArray

theorem impl_correct : ∀ n, impl n = partitionSpec n := by
  intro n
  unfold impl partitionArray partitionSpec
  rw [array_getD_toList]
  rw [buildRowsArray_toList]
  exact buildRows_getD n n n (Nat.le_refl n)

end Submission
'''
p=OUT/"Submission_v7.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
