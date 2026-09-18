#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

text=r'''import Spec

namespace Submission

/-- Stream generated rows directly into the DFS instead of materializing matrix/row lists. -/
def permanentRowsGen (width dimension seed : Nat) :
    List Nat → Nat → Nat
  | [], _ => 1
  | i :: is, used =>
      (List.range width).foldl (fun total j =>
        let entry := permanentEntry dimension seed i j
        if entry = 0 || used.testBit j then
          total
        else
          total + entry *
            permanentRowsGen width dimension seed is (used ||| (1 <<< j))) 0

theorem permanentRowsGen_eq :
    ∀ width dimension seed is used,
      permanentRowsGen width dimension seed is used =
        permanentRows width
          (is.map (genPermanentRow dimension seed)) used
  | width, dimension, seed, [], used => rfl
  | width, dimension, seed, i :: is, used => by
      simp only [permanentRowsGen, List.map_cons, permanentRows, genPermanentRow]
      apply List.foldl_congr
      intro total j hj
      simp only [List.mem_range] at hj
      simp only [List.getD_map, List.getD_range, hj, if_pos,
        permanentRowsGen_eq width dimension seed is]

def impl (n : Nat) : Nat :=
  let d := permanentDimension n
  let s := permanentSeed n
  permanentRowsGen d d s (List.range d) 0

theorem impl_correct : ∀ n, impl n = permanentSpecN n := by
  intro n
  unfold impl permanentSpecN permanentSpec genPermanentMatrix
  rw [permanentRowsGen_eq]

end Submission
'''
p=OUT/"Submission_v2.lean"; p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
