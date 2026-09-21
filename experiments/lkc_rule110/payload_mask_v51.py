#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
base=(ROOT/'Submission_v47.lean').read_text()
mask=(1<<254)-1
old='''def fastPayload (x : Nat) : Nat :=
  compactFast (fastSparse x) &&& (2 ^ 254 - 1)
'''
new=f'''def payloadMask254 : Nat := {hex(mask)}

theorem payloadMask254_eq : payloadMask254 = 2 ^ 254 - 1 := by decide

def fastPayload (x : Nat) : Nat :=
  compactFast (fastSparse x) &&& payloadMask254
'''
if old not in base: raise SystemExit('fastPayload pattern not found')
out=base.replace(old,new,1)
# Make the existing equality proof see the old mask expression.
out=out.replace('''  unfold fastPayload
  rw [fastSparse_eq, compactFast_eq, compactTree_bits256 x h]
''','''  unfold fastPayload
  rw [payloadMask254_eq]
  rw [fastSparse_eq, compactFast_eq, compactTree_bits256 x h]
''',1)
p=ROOT/'generated'/'Submission_v51.lean'; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(out)
print(f'generated {p} bytes={len(out)}')
