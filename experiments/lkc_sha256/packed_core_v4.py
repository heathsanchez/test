#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

text=r'''import Spec

namespace Submission

def base32 : Nat := 4294967296

def ValidDigest (d : Digest) : Prop :=
  d.a < base32 ∧ d.b < base32 ∧ d.c < base32 ∧ d.d < base32 ∧
  d.e < base32 ∧ d.f < base32 ∧ d.g < base32 ∧ d.h < base32

/-- Little-endian base-2^32 state between SHA chain steps. -/
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
  unfold packDigestLE unpackDigestLE
  simp only
  rw [mod_cons a _ ha, div_cons a _ ha]
  rw [mod_cons b _ hb, div_cons b _ hb]
  rw [mod_cons c _ hc, div_cons c _ hc]
  rw [mod_cons d _ hd, div_cons d _ hd]
  rw [mod_cons e _ he, div_cons e _ he]
  rw [mod_cons f _ hf, div_cons f _ hf]
  rw [mod_cons g hword hg, div_cons g hword hg]
  rw [Nat.mod_eq_of_lt hh]

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

theorem valid_feedForward (s f : Digest) :
    ValidDigest
      ⟨add32 s.a f.a, add32 s.b f.b, add32 s.c f.c, add32 s.d f.d,
       add32 s.e f.e, add32 s.f f.f, add32 s.g f.g, add32 s.h f.h⟩ := by
  unfold ValidDigest
  exact ⟨add32_lt_base _ _, add32_lt_base _ _, add32_lt_base _ _,
    add32_lt_base _ _, add32_lt_base _ _, add32_lt_base _ _,
    add32_lt_base _ _, add32_lt_base _ _⟩

theorem valid_compress (s : Digest) (block : List Nat) :
    ValidDigest (compress s block) := by
  unfold compress
  exact valid_feedForward s (rounds (K.zip (extendW 48 block)) s)

theorem valid_sha256step (d : Digest) : ValidDigest (sha256step d) := by
  unfold sha256step
  exact valid_compress iv
    [d.a, d.b, d.c, d.d, d.e, d.f, d.g, d.h,
     0x80000000, 0, 0, 0, 0, 0, 0, 256]

def packedStep (x : Nat) : Nat :=
  packDigestLE (sha256step (unpackDigestLE x))

def iterPacked : Nat → Nat → Nat
  | 0, x => x
  | t + 1, x => iterPacked t (packedStep x)

theorem iterPacked_correct :
    ∀ t d, ValidDigest d →
      unpackDigestLE (iterPacked t (packDigestLE d)) =
        iterDigest sha256step t d
  | 0, d, h => unpack_pack d h
  | t + 1, d, h => by
      simp only [iterPacked, packedStep, iterDigest]
      rw [unpack_pack d h]
      exact iterPacked_correct t (sha256step d) (valid_sha256step d)

def impl (n : Nat) : Nat :=
  let d0 := seedDigest (sha256Seed n)
  let packed := iterPacked (sha256Steps n) (packDigestLE d0)
  encodeDigest (unpackDigestLE packed)

theorem impl_correct : ∀ n, impl n = sha256Spec n := by
  intro n
  unfold impl sha256Spec iterSha
  rw [iterPacked_correct (sha256Steps n) (seedDigest (sha256Seed n))
      (valid_seedDigest (sha256Seed n))]

end Submission
'''

p=OUT/"Submission_v4.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
