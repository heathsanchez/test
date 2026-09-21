#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated"
OUT.mkdir(parents=True, exist_ok=True)

text = r'''import Spec
import Init.Data.Nat.Fold
import Init.Data.Queue

namespace Submission

def initialRow (n : Nat) : List Nat :=
  (List.range (n + 1)).map fun m => if m = 0 then 1 else 0

/-- V4 semantic bridge retained only for the universal proof. -/
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

/-! V8: an amortized O(1) functional FIFO replaces V6's repeated
    outRev.getD (part - 1) traversal. -/

def queueContents (q : Std.Queue Nat) : List Nat :=
  q.dList ++ q.eList.reverse

def queuePop (q : Std.Queue Nat) : Nat × Std.Queue Nat :=
  match q.dequeue? with
  | some p => p
  | none => (0, q)

theorem queueContents_enqueue (q : Std.Queue Nat) (x : Nat) :
    queueContents (q.enqueue x) = queueContents q ++ [x] := by
  simp [queueContents, Std.Queue.enqueue, List.reverse_cons, List.append_assoc]

theorem queuePop_fst (q : Std.Queue Nat) :
    (queuePop q).1 = (queueContents q).headD 0 := by
  rcases q with ⟨e, d⟩
  cases d with
  | nil =>
      cases h : e.reverse with
      | nil => simp [queuePop, queueContents, Std.Queue.dequeue?, h]
      | cons x xs => simp [queuePop, queueContents, Std.Queue.dequeue?, h]
  | cons x xs =>
      simp [queuePop, queueContents, Std.Queue.dequeue?]

theorem queueContents_pop_snd (q : Std.Queue Nat) :
    queueContents (queuePop q).2 = (queueContents q).tail := by
  rcases q with ⟨e, d⟩
  cases d with
  | nil =>
      cases h : e.reverse with
      | nil => simp [queuePop, queueContents, Std.Queue.dequeue?, h]
      | cons x xs => simp [queuePop, queueContents, Std.Queue.dequeue?, h]
  | cons x xs =>
      simp [queuePop, queueContents, Std.Queue.dequeue?]

structure RowState where
  q : Std.Queue Nat
  outRev : List Nat

def initialQueue (step : Nat) : Std.Queue Nat :=
  { eList := [], dList := List.replicate step 0 }

def initialState (step : Nat) : RowState :=
  { q := initialQueue step, outRev := [] }

def rowStep (prev : List Nat) (m : Nat) (st : RowState) : RowState :=
  let popped := queuePop st.q
  let y := prev.getD m 0 + popped.1
  { q := popped.2.enqueue y, outRev := y :: st.outRev }

def rowState (step : Nat) (prev : List Nat) : Nat → RowState
  | 0 => initialState step
  | m + 1 => rowStep prev m (rowState step prev m)

def rowValues (step : Nat) (prev : List Nat) (count : Nat) : List Nat :=
  (List.range count).map (rowValue step prev)

def expectedQueue (step : Nat) (prev : List Nat) (count : Nat) : List Nat :=
  (List.replicate step 0 ++ rowValues step prev count).drop count

theorem expectedQueue_succ
    (step : Nat) (prev : List Nat) (m : Nat) (hs : 0 < step) :
    expectedQueue step prev (m + 1) =
      (expectedQueue step prev m).tail ++ [rowValue step prev m] := by
  unfold expectedQueue rowValues
  rw [List.range_succ, List.map_append]
  simp only [List.map]
  rw [← List.append_assoc]
  rw [List.drop_append_of_le_length]
  · rw [List.drop_add_one_eq_tail_drop]
  · simp
    omega

theorem expectedQueue_head
    (step : Nat) (prev : List Nat) (m : Nat) (hs : 0 < step) :
    (expectedQueue step prev m).headD 0 =
      if step ≤ m then rowValue step prev (m - step) else 0 := by
  unfold expectedQueue rowValues
  rw [List.headD_eq_head?_getD, List.head?_drop]
  by_cases hlt : m < step
  · have hnle : ¬ step ≤ m := by omega
    rw [List.getElem?_append_left (by simpa using hlt)]
    simp [hlt, hnle]
  · have hle : step ≤ m := by omega
    rw [List.getElem?_append_right (by simpa using hle)]
    simp only [List.length_replicate]
    rw [List.getElem?_map]
    rw [List.getElem?_range (by omega)]
    simp [hle]

theorem rowState_invariant
    (step : Nat) (prev : List Nat) (hs : 0 < step) :
    ∀ count,
      let st := rowState step prev count
      st.outRev = (rowValues step prev count).reverse ∧
      queueContents st.q = expectedQueue step prev count
  | 0 => by
      simp [rowState, initialState, initialQueue, queueContents,
        rowValues, expectedQueue]
  | m + 1 => by
      have ih := rowState_invariant step prev hs m
      let st := rowState step prev m
      have hout : st.outRev = (rowValues step prev m).reverse := ih.1
      have hq : queueContents st.q = expectedQueue step prev m := ih.2
      have hlag :
          (queuePop st.q).1 =
            if step ≤ m then rowValue step prev (m - step) else 0 := by
        rw [queuePop_fst, hq, expectedQueue_head step prev m hs]
      have hy :
          prev.getD m 0 + (queuePop st.q).1 = rowValue step prev m := by
        rw [hlag, rowValue_recurrence step prev m hs]
      constructor
      · unfold rowState rowStep
        simp only
        rw [hy, hout]
        unfold rowValues
        rw [List.range_succ, List.map_append]
        simp
      · unfold rowState rowStep
        simp only
        rw [queueContents_enqueue, queueContents_pop_snd, hq, hy]
        exact (expectedQueue_succ step prev m hs).symm

def nextRowQueueCore (step : Nat) (prev : List Nat) (count : Nat) : List Nat :=
  (rowState step prev count).outRev.reverse

theorem nextRowQueueCore_eq
    (step : Nat) (prev : List Nat) (count : Nat) (hs : 0 < step) :
    nextRowQueueCore step prev count = rowValues step prev count := by
  unfold nextRowQueueCore
  rw [(rowState_invariant step prev hs count).1]
  simp

def nextRowQueue (k n : Nat) (prev : List Nat) : List Nat :=
  nextRowQueueCore (k + 1) prev (n + 1)

def nextRowFold (k n : Nat) (prev : List Nat) : List Nat :=
  (List.range (n + 1)).map fun m =>
    rowValue (k + 1) prev m

theorem nextRowQueue_eq (k n : Nat) (prev : List Nat) :
    nextRowQueue k n prev = nextRowFold k n prev := by
  simpa [nextRowQueue, nextRowFold, rowValues] using
    nextRowQueueCore_eq (k + 1) prev (n + 1) (by omega)

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

def buildRowsQueue : Nat → Nat → List Nat
  | 0, n => initialRow n
  | k + 1, n => nextRowQueue k n (buildRowsQueue k n)

theorem buildRowsQueue_eq :
    ∀ k n, buildRowsQueue k n = buildRows k n
  | 0, n => rfl
  | k + 1, n => by
      simp only [buildRowsQueue, buildRows]
      rw [buildRowsQueue_eq k n, nextRowQueue_eq, nextRowFold_eq]

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

def partitionQueue (n : Nat) : Nat :=
  (buildRowsQueue n n).getD n 0

def impl : Nat → Nat := partitionQueue

theorem impl_correct : ∀ n, impl n = partitionSpec n := by
  intro n
  unfold impl partitionQueue partitionSpec
  rw [buildRowsQueue_eq]
  exact buildRows_getD n n n (Nat.le_refl n)

end Submission
'''

p = OUT / "Submission_v8.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
