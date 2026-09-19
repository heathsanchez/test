#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"nozip_v1.py"))
v1=(OUT/"Submission_v1.lean").read_text()
prefix=v1.split("def impl (n : Nat) : Nat :=",1)[0]

def make(chunk: int) -> str:
    lines=[f"/-- Apply exactly {chunk} proved no-zip SHA steps without recursive chain control. -/",
           f"def step{chunk} (d : Digest) : Digest :="]
    prev="d"
    for i in range(1,chunk+1):
        lines.append(f"  let d{i} := fastStepNoZip {prev}")
        prev=f"d{i}"
    lines.append(f"  {prev}")
    body="\n".join(lines)
    return prefix + body + f'''

def iterGroups{chunk} : Nat → Digest → Digest
  | 0, d => d
  | q + 1, d => iterGroups{chunk} q (step{chunk} d)

/--
Write n = {chunk}*q + r once, recurse only q times, then discharge the
small remainder with the already trusted iterator.
-/
def iterChunk{chunk} (n : Nat) (d : Digest) : Digest :=
  let q := n / {chunk}
  let r := n % {chunk}
  iterDigest fastStepNoZip r (iterGroups{chunk} q d)

def impl (n : Nat) : Nat :=
  encodeDigest
    (iterChunk{chunk} (sha256Steps n) (seedDigest (sha256Seed n)))

end Submission
'''

for c in (4,8,16,32,64):
    text=make(c)
    p=OUT/f"Submission_chain{c}_v19.lean"
    p.write_text(text)
    print(f"generated {p} bytes={len(text.encode())}")
