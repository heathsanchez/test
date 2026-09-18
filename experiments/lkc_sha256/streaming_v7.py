#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

# Reuse the already-verified no-zip theorem stack through fastStepNoZip_fun,
# then replace the runtime step by a streaming Window transition.
runpy.run_path(str(ROOT/"nozip_v1.py"))
v1=(OUT/"Submission_v1.lean").read_text()
prefix=v1.split("def impl (n : Nat) : Nat :=",1)[0]

body=r'''
/-- Advance the 16-word schedule window by one recurrence step. -/
def Window.advance (w : Window) : Window :=
  w.push w.nextWord

/-- Stream schedule words without ever materialising the 64-word schedule. -/
def streamWords : Nat → Window → List Nat
  | 0, _ => []
  | k + 1, w => w.x0 :: streamWords k w.advance

/-- Consume constants while carrying only the current 16-word schedule window. -/
def roundsWindow : List Nat → Window → Digest → Digest
  | [], _, s => s
  | k :: ks, w, s =>
      roundsWindow ks w.advance (round s k w.x0)

theorem roundsWindow_eq (ks : List Nat) (w : Window) (s : Digest) :
    roundsWindow ks w s =
      roundsNoZip ks (streamWords ks.length w) s := by
  induction ks generalizing w s with
  | nil =>
      rfl
  | cons k ks ih =>
      simp only [roundsWindow, List.length_cons, streamWords, roundsNoZip]
      exact ih w.advance (round s k w.x0)

/--
A 16-word Window followed by 48 generated words is exactly the 64-word
on-demand stream.  This finite bridge is paid once in the proof, not at
every SHA chain step.
-/
theorem streamWords64_eq (w : Window) :
    streamWords 64 w = w.toList ++ generate 48 w := by
  rcases w with ⟨x0,x1,x2,x3,x4,x5,x6,x7,x8,x9,x10,x11,x12,x13,x14,x15⟩
  rfl

def fastStepWindow (d : Digest) : Digest :=
  let f := roundsWindow K (initialWindow d) iv
  ⟨add32 iv.a f.a, add32 iv.b f.b, add32 iv.c f.c, add32 iv.d f.d,
   add32 iv.e f.e, add32 iv.f f.f, add32 iv.g f.g, add32 iv.h f.h⟩

theorem fastStepWindow_eq_nozip (d : Digest) :
    fastStepWindow d = fastStepNoZip d := by
  unfold fastStepWindow fastStepNoZip fastSchedule
  rw [roundsWindow_eq]
  change
    (let f := roundsNoZip K
      (streamWords 64 (initialWindow d)) iv
     ⟨add32 iv.a f.a, add32 iv.b f.b, add32 iv.c f.c, add32 iv.d f.d,
      add32 iv.e f.e, add32 iv.f f.f, add32 iv.g f.g, add32 iv.h f.h⟩) =
    (let w := initialWindow d
     let f := roundsNoZip K (w.toList ++ generate 48 w) iv
     ⟨add32 iv.a f.a, add32 iv.b f.b, add32 iv.c f.c, add32 iv.d f.d,
      add32 iv.e f.e, add32 iv.f f.f, add32 iv.g f.g, add32 iv.h f.h⟩)
  rw [streamWords64_eq]

theorem fastStepWindow_correct (d : Digest) :
    fastStepWindow d = sha256step d := by
  rw [fastStepWindow_eq_nozip]
  exact fastStepNoZip_correct d

theorem fastStepWindow_fun : fastStepWindow = sha256step :=
  funext fastStepWindow_correct

def base32 : Nat := 4294967296

def ValidDigest (d : Digest) : Prop :=
  d.a < base32 ∧ d.b < base32 ∧ d.c < base32 ∧ d.d < base32 ∧
  d.e < base32 ∧ d.f < base32 ∧ d.g < base32 ∧ d.h < base32

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

theorem valid_fastStepWindow (d : Digest) : ValidDigest (fastStepWindow d) := by
  rw [fastStepWindow_correct]
  unfold sha256step compress
  unfold ValidDigest
  exact ⟨add32_lt_base _ _, add32_lt_base _ _, add32_lt_base _,
    add32_lt_base _ _, add32_lt_base _ _, add32_lt_base _ _,
    add32_lt_base _ _, add32_lt_base _ _⟩

def packedStepWindow (x : Nat) : Nat :=
  packDigestLE (fastStepWindow (unpackDigestLE x))

def iterPackedWindow : Nat → Nat → Nat
  | 0, x => x
  | t + 1, x => iterPackedWindow t (packedStepWindow x)

theorem iterPackedWindow_correct :
    ∀ t d, ValidDigest d →
      unpackDigestLE (iterPackedWindow t (packDigestLE d)) =
        iterDigest fastStepWindow t d
  | 0, d, h => unpack_pack d h
  | t + 1, d, h => by
      simp only [iterPackedWindow, packedStepWindow, iterDigest]
      rw [unpack_pack d h]
      exact iterPackedWindow_correct t (fastStepWindow d)
        (valid_fastStepWindow d)

def impl (n : Nat) : Nat :=
  let d0 := seedDigest (sha256Seed n)
  let packed := iterPackedWindow (sha256Steps n) (packDigestLE d0)
  encodeDigest (unpackDigestLE packed)

theorem impl_correct : ∀ n, impl n = sha256Spec n := by
  intro n
  unfold impl sha256Spec iterSha
  rw [iterPackedWindow_correct
      (sha256Steps n) (seedDigest (sha256Seed n))
      (valid_seedDigest (sha256Seed n))]
  rw [fastStepWindow_fun]

end Submission
'''

text=prefix+body
p=OUT/"Submission_v7.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
