#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"threecompiled_v13.py"))
src=(OUT/"Submission_v13.lean").read_text()

extra=r'''
/-! V14: compile the part-size-3 semantic sum into its 3-step recurrence. -/

theorem threeValue_recurrence (m : Nat) :
    threeValue m =
      m / 2 + 1 + (if 3 ≤ m then threeValue (m - 3) else 0) := by
  by_cases h : 3 ≤ m
  · rw [if_pos h]
    unfold threeValue
    rw [sumFold_shift]
    simp only [Nat.zero_mul, Nat.sub_zero]
    have hdiv : m / 3 = (m - 3) / 3 + 1 := by
      conv => lhs
              rw [show m = (m - 3) + 3 by omega]
      rw [Nat.add_div_right _ (by decide : 0 < 3)]
    rw [hdiv]
    apply congrArg (fun x => m / 2 + 1 + x)
    apply sumFold_congr
    intro j hj
    congr 2
    omega
  · rw [if_neg h]
    have hm : m < 3 := by omega
    unfold threeValue
    rw [Nat.div_eq_of_lt hm]
    simp [sumFold, Nat.fold]

/-- Same complete {1,2,3}-row value as V13, but a tiny structural recursion
rather than rebuilding a generic sum at every coordinate. -/
def threeFastValue : Nat → Nat
  | 0 => 1
  | 1 => 1
  | 2 => 2
  | m + 3 => (m + 3) / 2 + 1 + threeFastValue m

theorem threeFastValue_eq : ∀ m, threeFastValue m = threeValue m
  | 0 => by
      simpa [threeFastValue] using (threeValue_recurrence 0).symm
  | 1 => by
      simpa [threeFastValue] using (threeValue_recurrence 1).symm
  | 2 => by
      simpa [threeFastValue] using (threeValue_recurrence 2).symm
  | m + 3 => by
      rw [threeFastValue, threeValue_recurrence]
      simp only [show 3 ≤ m + 3 by omega, if_pos]
      rw [threeFastValue_eq m]

def threesRowFast (n : Nat) : List Nat :=
  (List.range (n + 1)).map threeFastValue

theorem threesRowFast_getD (n m : Nat) (hm : m ≤ n) :
    (threesRowFast n).getD m 0 = partAux 3 m := by
  rw [threesRowFast, range_map_getD (h := by omega), threeFastValue_eq]
  exact (partAux_three m).symm

theorem threesRowFast_eq_buildRowsSeeded_three (n : Nat) :
    threesRowFast n = buildRowsSeeded 3 n := by
  apply List.ext_getElem
  · rw [buildRowsSeeded_eq, buildRowsDirect_eq, buildRowsShift_eq,
      buildRows_length]
    simp [threesRowFast]
  · intro i hi ht
    have him : i ≤ n := by
      simp [threesRowFast] at hi
      omega
    have hl := threesRowFast_getD n i him
    have hr :
        (buildRowsSeeded 3 n).getD i 0 = partAux 3 i := by
      rw [buildRowsSeeded_eq, buildRowsDirect_eq, buildRowsShift_eq]
      exact buildRows_getD 3 n i him
    have hd :
        (threesRowFast n).getD i 0 =
          (buildRowsSeeded 3 n).getD i 0 :=
      hl.trans hr.symm
    have hleft :
        (threesRowFast n).getD i 0 = (threesRowFast n)[i] := by
      simp [List.getD_eq_getElem?_getD, hi]
    have hright :
        (buildRowsSeeded 3 n).getD i 0 =
          (buildRowsSeeded 3 n)[i] := by
      simp [List.getD_eq_getElem?_getD, ht]
    exact hleft.symm.trans (hd.trans hright)

def buildAboveThreeFast : Nat → Nat → List Nat
  | 0, n => threesRowFast n
  | r + 1, n => nextRowSeeded (r + 3) n (buildAboveThreeFast r n)

theorem buildAboveThreeFast_eq :
    ∀ r n, buildAboveThreeFast r n = buildRowsSeeded (r + 3) n
  | 0, n => threesRowFast_eq_buildRowsSeeded_three n
  | r + 1, n => by
      simp only [buildAboveThreeFast]
      rw [buildAboveThreeFast_eq r n]
      rfl

def partitionThreeFast : Nat → Nat
  | 0 => 1
  | 1 => 1
  | 2 => 2
  | n + 3 => (buildAboveThreeFast n (n + 3)).getD (n + 3) 0
'''

anchor="def partitionThree : Nat → Nat\n"
if anchor not in src:
    raise SystemExit("V13 partitionThree anchor missing")
src=src.replace(anchor,extra+"\n"+anchor,1)
src=src.replace("def impl : Nat → Nat := partitionThree",
                "def impl : Nat → Nat := partitionThreeFast",1)
start=src.index("theorem impl_correct : ∀ n, impl n = partitionSpec n := by")
end=src.index("\nend Submission", start)
proof=src[start:end]
proof=proof.replace("buildAboveThree m", "buildAboveThreeFast m")
proof=proof.replace("buildAboveThree_eq", "buildAboveThreeFast_eq")
src=src[:start]+proof+src[end:]

p=OUT/"Submission_v14_three_recurrence.lean"
p.write_text(src)
print(f"generated {p} bytes={len(src.encode())}")
