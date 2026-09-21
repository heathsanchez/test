#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

text=r'''import Spec
import Init.Data.Nat.Fold
import Init.Data.Nat.Lemmas
import Init.Data.List.Zip
import Init.Data.List.Nat.TakeDrop

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

/-- Proof-only semantic sum, inherited from V5. -/
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

def nextRowFold (k n : Nat) (prev : List Nat) : List Nat :=
  (List.range (n + 1)).map fun m =>
    rowValue (k + 1) prev m

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

theorem nextRowFold_eq (k n : Nat) (prev : List Nat) :
    nextRowFold k n prev = nextRow k n prev := by
  unfold nextRowFold nextRow rowValue
  apply List.map_congr_left
  intro m hm
  exact sumFold_eq_list
    (m / (k + 1) + 1)
    (fun j => prev.getD (m - j * (k + 1)) 0)

/-! V8 operational representation: repeated whole-row shift + zipWith. -/

def shiftPad (step : Nat) (xs : List Nat) : List Nat :=
  List.replicate step 0 ++ xs

def addShift (step : Nat) (prev acc : List Nat) : List Nat :=
  List.zipWith (· + ·) prev (shiftPad step acc)

def iterateShift (step : Nat) (prev : List Nat) : Nat → List Nat
  | 0 => List.replicate prev.length 0
  | q + 1 => addShift step prev (iterateShift step prev q)

def iterValue (step : Nat) (prev : List Nat) : Nat → Nat → Nat
  | 0, _ => 0
  | q + 1, m =>
      prev.getD m 0 +
        (if step ≤ m then iterValue step prev q (m - step) else 0)

theorem shiftPad_length (step : Nat) (xs : List Nat) :
    (shiftPad step xs).length = step + xs.length := by
  simp [shiftPad]

theorem iterateShift_length (step : Nat) (prev : List Nat) :
    ∀ q, (iterateShift step prev q).length = prev.length
  | 0 => by simp [iterateShift]
  | q + 1 => by
      simp only [iterateShift, addShift, List.length_zipWith,
        shiftPad_length, iterateShift_length step prev q]
      omega

theorem shiftPad_getD (step : Nat) (xs : List Nat) (m : Nat) :
    (shiftPad step xs).getD m 0 =
      if step ≤ m then xs.getD (m - step) 0 else 0 := by
  unfold shiftPad
  simp only [List.getD_eq_getElem?_getD]
  by_cases h : step ≤ m
  · rw [if_pos h]
    rw [List.getElem?_append_right (by simpa using h)]
    simp
  · have hm : m < step := by omega
    rw [if_neg h]
    rw [List.getElem?_append_left (by simpa using hm)]
    rw [List.getElem?_replicate]
    simp [hm]

theorem zipAdd_getD
    (prev acc : List Nat) (m : Nat)
    (hm : m < prev.length) (hlen : prev.length ≤ acc.length) :
    (List.zipWith (· + ·) prev acc).getD m 0 =
      prev.getD m 0 + acc.getD m 0 := by
  simp only [List.getD_eq_getElem?_getD, List.getElem?_zipWith]
  have ha : m < acc.length := Nat.lt_of_lt_of_le hm hlen
  rw [List.getElem?_eq_getElem hm, List.getElem?_eq_getElem ha]
  simp

theorem iterateShift_getD (step : Nat) (prev : List Nat) :
    ∀ q m, m < prev.length →
      (iterateShift step prev q).getD m 0 = iterValue step prev q m
  | 0, m, hm => by
      simp [iterateShift, iterValue, List.getD_eq_getElem?_getD, hm]
  | q + 1, m, hm => by
      simp only [iterateShift, addShift, iterValue]
      rw [zipAdd_getD prev
        (shiftPad step (iterateShift step prev q)) m hm]
      · rw [shiftPad_getD]
        by_cases h : step ≤ m
        · rw [if_pos h]
          rw [iterateShift_getD step prev q (m - step) (by omega)]
        · rw [if_neg h]
      · rw [shiftPad_length, iterateShift_length]
        omega

theorem iterValue_eq_rowValue
    (step : Nat) (prev : List Nat) (hs : 0 < step) :
    ∀ q m, m < q * step →
      iterValue step prev q m = rowValue step prev m
  | 0, m, h => by
      simp at h
  | q + 1, m, h => by
      rw [iterValue, rowValue_recurrence step prev m hs]
      by_cases hle : step ≤ m
      · simp only [if_pos hle]
        apply congrArg (fun x => prev.getD m 0 + x)
        apply iterValue_eq_rowValue step prev hs q (m - step)
        have hh : m < q * step + step := by
          simpa [Nat.add_mul] using h
        omega
      · simp [hle]

def nextRowShift (k n : Nat) (prev : List Nat) : List Nat :=
  iterateShift (k + 1) prev (n / (k + 1) + 1)

theorem nextRowShift_length (k n : Nat) (prev : List Nat) :
    (nextRowShift k n prev).length = prev.length := by
  exact iterateShift_length (k + 1) prev (n / (k + 1) + 1)

theorem nextRowShift_getD
    (k n : Nat) (prev : List Nat)
    (hlen : prev.length = n + 1)
    (m : Nat) (hm : m ≤ n) :
    (nextRowShift k n prev).getD m 0 =
      rowValue (k + 1) prev m := by
  unfold nextRowShift
  rw [iterateShift_getD (k + 1) prev
    (n / (k + 1) + 1) m (by rw [hlen]; omega)]
  apply iterValue_eq_rowValue (k + 1) prev (by omega)
  have hn := Nat.lt_mul_div_succ n (b := k + 1) (by omega)
  have hn' : n < (n / (k + 1) + 1) * (k + 1) := by
    simpa [Nat.mul_comm] using hn
  omega

theorem nextRowShift_eq
    (k n : Nat) (prev : List Nat)
    (hlen : prev.length = n + 1) :
    nextRowShift k n prev = nextRowFold k n prev := by
  apply List.ext_getElem
  · rw [nextRowShift_length, hlen]
    simp [nextRowFold]
  · intro i hi hs
    have him : i ≤ n := by
      rw [nextRowShift_length, hlen] at hi
      omega
    have hget := nextRowShift_getD k n prev hlen i him
    simp only [List.getD_eq_getElem?_getD,
      List.getElem?_eq_getElem hi,
      List.getElem?_eq_getElem hs,
      Option.getD_some] at hget
    simpa [nextRowFold, range_map_getD] using hget

def buildRowsShift : Nat → Nat → List Nat
  | 0, n => initialRow n
  | k + 1, n => nextRowShift k n (buildRowsShift k n)

theorem buildRows_length : ∀ k n, (buildRows k n).length = n + 1
  | 0, n => by simp [buildRows, initialRow]
  | k + 1, n => by simp [buildRows, nextRow]

theorem buildRowsShift_eq : ∀ k n, buildRowsShift k n = buildRows k n
  | 0, n => rfl
  | k + 1, n => by
      simp only [buildRowsShift, buildRows]
      rw [buildRowsShift_eq k n]
      rw [nextRowShift_eq k n (buildRows k n) (buildRows_length k n)]
      rw [nextRowFold_eq]

theorem range_map_getD
    (f : Nat → Nat) (count i fallback : Nat) (h : i < count) :
    ((List.range count).map f).getD i fallback = f i := by
  simp only [List.getD_eq_getElem?_getD, List.getElem?_map]
  rw [List.getElem?_range h]
  simp

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

def partitionShift (n : Nat) : Nat :=
  (buildRowsShift n n).getD n 0

def impl : Nat → Nat := partitionShift

theorem impl_correct : ∀ n, impl n = partitionSpec n := by
  intro n
  unfold impl partitionShift partitionSpec
  rw [buildRowsShift_eq]
  exact buildRows_getD n n n (Nat.le_refl n)

end Submission
'''
p=OUT/"Submission_v8.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
