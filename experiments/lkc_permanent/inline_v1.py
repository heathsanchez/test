#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated"
OUT.mkdir(parents=True, exist_ok=True)

header = r'''import Spec

namespace Submission
'''

variants = {
"v1": r'''
/-- Remove only the permanentSpecN/permanentSpec decode wrappers. -/
def impl (n : Nat) : Nat :=
  let d := n >>> 32
  let s := n &&& 0xffffffff
  permanentRows d (genPermanentMatrix d s) 0

theorem impl_correct : ∀ n, impl n = permanentSpecN n := by
  intro n
  rfl
''',
"v2": r'''
/-- Also inline genPermanentMatrix, retaining genPermanentRow. -/
def impl (n : Nat) : Nat :=
  let d := n >>> 32
  let s := n &&& 0xffffffff
  permanentRows d ((List.range d).map (genPermanentRow d s)) 0

theorem impl_correct : ∀ n, impl n = permanentSpecN n := by
  intro n
  rfl
''',
"v3": r'''
/-- Inline matrix and row generation while leaving permanentEntry unchanged. -/
def impl (n : Nat) : Nat :=
  let d := n >>> 32
  let s := n &&& 0xffffffff
  permanentRows d
    ((List.range d).map (fun i =>
      (List.range d).map (permanentEntry d s i))) 0

theorem impl_correct : ∀ n, impl n = permanentSpecN n := by
  intro n
  rfl
'''
}

for version, body in variants.items():
    text = header + body + "\nend Submission\n"
    path = OUT / f"Submission_{version}.lean"
    path.write_text(text)
    print(f"{version}: {path} bytes={len(text.encode())}")
