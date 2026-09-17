#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated"
OUT.mkdir(parents=True, exist_ok=True)

core = r'''import Spec

namespace Submission

/-- Update `fuel` consecutive DP cells, beginning at index `j`, for one
allowed part size `k`.  The table is generated during kernel computation. -/
def addPartLoop (k j : Nat) : Nat → Array Nat → Array Nat
  | 0, a => a
  | fuel + 1, a =>
      let v := a.getD j 0 + a.getD (j - k) 0
      addPartLoop k (j + 1) fuel (a.setIfInBounds j v)

/-- Process consecutive allowed part sizes, beginning at `k`. -/
def runParts (n k : Nat) : Nat → Array Nat → Array Nat
  | 0, a => a
  | fuel + 1, a =>
      let a' := addPartLoop k k (n + 1 - k) a
      runParts n (k + 1) fuel a'

/-- Bottom-up coin-change DP for the exact partition number. -/
def partitionDP (n : Nat) : Nat :=
  let a0 := (Array.replicate (n + 1) 0).setIfInBounds 0 1
  let a := runParts n 1 n a0
  a.getD n 0

def impl : Nat → Nat := partitionDP
'''

# Development-only semantic shell.  These literals are NOT emitted into the
# submission; they only make the computation executable before the universal
# proof is complete.
def parts(m: int):
    a=[0]*(m+1); a[0]=1
    for k in range(1,m+1):
        for j in range(k,m+1):
            a[j]+=a[j-k]
    return a

vals = parts(80)
probe = core
for n in list(range(0, 21)) + [26, 36, 50, 80]:
    probe += f"\nexample : impl {n} = {vals[n]} := by rfl\n"
probe += "\nend Submission\n"
(OUT / "Probe_v3.lean").write_text(probe)

submission = core + r'''

/-- Proof frontier: once the DP invariant is established, this theorem replaces
this deliberately failing RED placeholder. -/
theorem impl_correct : ∀ n, impl n = partitionSpec n := by
  intro n
  rfl

end Submission
'''
(OUT / "Submission_v3.lean").write_text(submission)
print(f"generated {OUT / 'Probe_v3.lean'} bytes={(OUT / 'Probe_v3.lean').stat().st_size}")
print(f"generated {OUT / 'Submission_v3.lean'} bytes={(OUT / 'Submission_v3.lean').stat().st_size}")
