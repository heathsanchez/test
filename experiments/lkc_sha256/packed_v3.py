#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

# Reuse the already verified no-zip step source, but replace only the final iterated representation.
runpy.run_path(str(ROOT/"nozip_v1.py"))
v1=(OUT/"Submission_v1.lean").read_text()
prefix=v1.split("def impl (n : Nat) : Nat :=",1)[0]

packed=r'''
def base32 : Nat := 4294967296

def ValidDigest (d : Digest) : Prop :=
  d.a < base32 ∧ d.b < base32 ∧ d.c < base32 ∧ d.d < base32 ∧
  d.e < base32 ∧ d.f < base32 ∧ d.g < base32 ∧ d.h < base32

/-- Little-endian base-2^32 packing used only between chain steps. -/
def packDigestLE (d : Digest) : Nat :=
  d.a + base32 * (
  d.b + base32 * (
  d.c + base32 * (
  d.d + base32 * (
  d.e + base32 * (
  d.f + base32 * (
  d.g + base32 * d.h))))))

def unpackDigestLE (x : Nat) : Digest :=
  let a := x % base32
  let x := x / base32
  let b := x % base32
  let x := x / base32
  let c := x % base32
  let x := x / base32
  let d := x % base32
  let x := x / base32
  let e := x % base32
  let x := x / base32
  let f := x % base32
  let x := x / base32
  let g := x % base32
  let h := (x / base32) % base32
  ⟨a,b,c,d,e,f,g,h⟩

theorem mod_cons (a rest : Nat) (ha : a < base32) :
    (a + base32 * rest) % base32 = a := by
  simp [Nat.add_mul_mod_self_left, Nat.mod_eq_of_lt ha]

theorem div_cons (a rest : Nat) (ha : a < base32) :
    (a + base32 * rest) / base32 = rest := by
  rw [Nat.add_mul_div_left a rest (by decide)]
  rw [Nat.div_eq_of_lt ha, Nat.zero_add]

theorem unpack_pack (d : Digest) (h : ValidDigest d) :
    unpackDigestLE (packDigestLE d) = d := by
  rcases d with ⟨a,b,c,d,e,f,g,hword⟩
  simp only [ValidDigest] at h
  rcases h with ⟨ha,hb,hc,hd,he,hf,hg,hh⟩
  simp [packDigestLE, unpackDigestLE, mod_cons, div_cons,
    ha,hb,hc,hd,he,hf,hg,hh]

theorem add32_lt_base (a b : Nat) : add32 a b < base32 := by
  unfold add32
  exact Nat.lt_of_le_of_lt Nat.and_le_right (by decide)

theorem seedStep32_lt_base (x : Nat) : seedStep32 x < base32 := by
  unfold seedStep32
  exact Nat.lt_of_le_of_lt Nat.and_le_right (by decide)

theorem valid_seedDigest (seed : Nat) : ValidDigest (seedDigest seed) := by
  unfold ValidDigest seedDigest
  dsimp
  exact ⟨seedStep32_lt_base _, seedStep32_lt_base _, seedStep32_lt_base _,
    seedStep32_lt_base _, seedStep32_lt_base _, seedStep32_lt_base _,
    seedStep32_lt_base _, seedStep32_lt_base _⟩

theorem valid_fastStepNoZip (d : Digest) : ValidDigest (fastStepNoZip d) := by
  unfold ValidDigest fastStepNoZip
  dsimp
  exact ⟨add32_lt_base _ _, add32_lt_base _ _, add32_lt_base _ _,
    add32_lt_base _ _, add32_lt_base _ _, add32_lt_base _ _,
    add32_lt_base _ _, add32_lt_base _ _⟩

def packedStep (x : Nat) : Nat :=
  packDigestLE (fastStepNoZip (unpackDigestLE x))

def iterPacked : Nat → Nat → Nat
  | 0, x => x
  | t + 1, x => iterPacked t (packedStep x)

theorem iterPacked_correct :
    ∀ t d, ValidDigest d →
      unpackDigestLE (iterPacked t (packDigestLE d)) =
        iterDigest fastStepNoZip t d
  | 0, d, h => unpack_pack d h
  | t + 1, d, h => by
      simp only [iterPacked, packedStep, iterDigest]
      rw [unpack_pack d h]
      exact iterPacked_correct t (fastStepNoZip d) (valid_fastStepNoZip d)

def impl (n : Nat) : Nat :=
  let d0 := seedDigest (sha256Seed n)
  let packed := iterPacked (sha256Steps n) (packDigestLE d0)
  encodeDigest (unpackDigestLE packed)

theorem impl_correct : ∀ n, impl n = sha256Spec n := by
  intro n
  unfold impl sha256Spec iterSha
  rw [iterPacked_correct (sha256Steps n) (seedDigest (sha256Seed n))
      (valid_seedDigest (sha256Seed n))]
  rw [fastStepNoZip_fun]

end Submission
'''

text=prefix+packed
p=OUT/"Submission_v3.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
