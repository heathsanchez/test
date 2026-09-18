#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"packed_core_v4.py"))
src=(OUT/"Submission_v4.lean").read_text()
start=src.index("def packedStep")

prefix=src[:start]
middle=r'''
def packedStep (x : Nat) : Nat :=
  packDigestLE (sha256step (unpackDigestLE x))

def iterFn {α : Type} (f : α → α) : Nat → α → α
  | 0, x => x
  | t + 1, x => iterFn f t (f x)

/-- Generic conjugacy theorem.  The recursion is abstract and independent of SHA. -/
theorem conjugate_iter
    {α β : Type}
    (pack : α → β) (unpack : β → α) (step : α → α) (P : α → Prop)
    (hleft : ∀ a, P a → unpack (pack a) = a)
    (hstep : ∀ a, P a → P (step a)) :
    ∀ t a, P a →
      unpack (iterFn (fun x => pack (step (unpack x))) t (pack a)) =
        iterFn step t a
  | 0, a, ha => hleft a ha
  | t + 1, a, ha => by
      simp only [iterFn]
      rw [hleft a ha]
      exact conjugate_iter pack unpack step P hleft hstep
        t (step a) (hstep a ha)

theorem iterFn_eq_iterDigest (step : Digest → Digest) :
    ∀ t d, iterFn step t d = iterDigest step t d
  | 0, d => rfl
  | t + 1, d => by
      simp only [iterFn, iterDigest]
      exact iterFn_eq_iterDigest step t (step d)

def impl (n : Nat) : Nat :=
  let d0 := seedDigest (sha256Seed n)
  let packed := iterFn packedStep (sha256Steps n) (packDigestLE d0)
  encodeDigest (unpackDigestLE packed)

theorem impl_correct : ∀ n, impl n = sha256Spec n := by
  intro n
  unfold impl sha256Spec iterSha packedStep
  rw [conjugate_iter
      packDigestLE unpackDigestLE sha256step ValidDigest
      unpack_pack (fun a _ => valid_sha256step a)
      (sha256Steps n) (seedDigest (sha256Seed n))
      (valid_seedDigest (sha256Seed n))]
  rw [iterFn_eq_iterDigest]

end Submission
'''
text=prefix+middle
p=OUT/"Submission_v5.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
