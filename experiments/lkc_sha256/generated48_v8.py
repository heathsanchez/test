#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"nozip_v1.py"))
v1=(OUT/"Submission_v1.lean").read_text()
prefix=v1.split("def impl (n : Nat) : Nat :=",1)[0]

body=r'''
/--
Consume one generated schedule word per round.  Unlike extendW, no schedule
list grows: the 16-word Window is the complete recurrence state.
-/
def roundsGenerated : List Nat → Window → Digest → Digest
  | [], _, s => s
  | k :: ks, w, s =>
      let x := w.nextWord
      roundsGenerated ks (w.push x) (round s k x)

theorem roundsGenerated_eq :
    ∀ ks w s,
      roundsGenerated ks w s =
        roundsNoZip ks (generate ks.length w) s
  | [], w, s => rfl
  | k :: ks, w, s => by
      simp only [roundsGenerated, List.length_cons, generate, roundsNoZip]
      exact roundsGenerated_eq ks (w.push w.nextWord)
        (round s k w.nextWord)

/-- Split parallel round consumption across two equally aligned prefixes. -/
theorem roundsNoZip_append
    (ks1 ks2 ws1 ws2 : List Nat) (s : Digest)
    (hlen : ks1.length = ws1.length) :
    roundsNoZip (ks1 ++ ks2) (ws1 ++ ws2) s =
      roundsNoZip ks2 ws2 (roundsNoZip ks1 ws1 s) := by
  induction ks1 generalizing ws1 s with
  | nil =>
      cases ws1 with
      | nil => rfl
      | cons w ws => simp at hlen
  | cons k ks ih =>
      cases ws1 with
      | nil => simp at hlen
      | cons w ws =>
          simp only [List.length_cons, Nat.succ.injEq] at hlen
          simp only [List.cons_append, roundsNoZip]
          exact ih ws (round s k w) hlen

/--
Runtime transition: the initial 16 words are consumed directly, then the
remaining 48 rounds consume words generated on demand from the Window.
No 64-word schedule and no K.zip are constructed.
-/
def fastStepGenerated (d : Digest) : Digest :=
  let w := initialWindow d
  let s16 := roundsNoZip (K.take 16) w.toList iv
  let f := roundsGenerated (K.drop 16) w s16
  ⟨add32 iv.a f.a, add32 iv.b f.b, add32 iv.c f.c, add32 iv.d f.d,
   add32 iv.e f.e, add32 iv.f f.f, add32 iv.g f.g, add32 iv.h f.h⟩

theorem k_take16_len : (K.take 16).length = 16 := by rfl
theorem k_drop16_len : (K.drop 16).length = 48 := by rfl
theorem window_len (w : Window) : w.toList.length = 16 := by
  simp [Window.toList]

theorem fastStepGenerated_eq_nozip (d : Digest) :
    fastStepGenerated d = fastStepNoZip d := by
  let w := initialWindow d
  have hlen : (K.take 16).length = w.toList.length := by
    rw [k_take16_len, window_len]
  have hsplit :
      roundsNoZip K (w.toList ++ generate 48 w) iv =
        roundsNoZip (K.drop 16) (generate 48 w)
          (roundsNoZip (K.take 16) w.toList iv) := by
    calc
      roundsNoZip K (w.toList ++ generate 48 w) iv =
          roundsNoZip (K.take 16 ++ K.drop 16)
            (w.toList ++ generate 48 w) iv := by
              rw [List.take_append_drop]
      _ = roundsNoZip (K.drop 16) (generate 48 w)
            (roundsNoZip (K.take 16) w.toList iv) :=
          roundsNoZip_append (K.take 16) (K.drop 16)
            w.toList (generate 48 w) iv hlen
  have hgen :
      roundsGenerated (K.drop 16) w
          (roundsNoZip (K.take 16) w.toList iv) =
        roundsNoZip (K.drop 16) (generate 48 w)
          (roundsNoZip (K.take 16) w.toList iv) := by
    have h := roundsGenerated_eq (K.drop 16) w
      (roundsNoZip (K.take 16) w.toList iv)
    rw [k_drop16_len] at h
    exact h
  unfold fastStepGenerated fastStepNoZip fastSchedule
  change
    (let w := initialWindow d
     let s16 := roundsNoZip (K.take 16) w.toList iv
     let f := roundsGenerated (K.drop 16) w s16
     ⟨add32 iv.a f.a, add32 iv.b f.b, add32 iv.c f.c, add32 iv.d f.d,
      add32 iv.e f.e, add32 iv.f f.f, add32 iv.g f.g, add32 iv.h f.h⟩) =
    (let w := initialWindow d
     let f := roundsNoZip K (w.toList ++ generate 48 w) iv
     ⟨add32 iv.a f.a, add32 iv.b f.b, add32 iv.c f.c, add32 iv.d f.d,
      add32 iv.e f.e, add32 iv.f f.f, add32 iv.g f.g, add32 iv.h f.h⟩)
  dsimp only
  rw [hgen, ← hsplit]

theorem fastStepGenerated_correct (d : Digest) :
    fastStepGenerated d = sha256step d := by
  rw [fastStepGenerated_eq_nozip]
  exact fastStepNoZip_correct d

theorem fastStepGenerated_fun : fastStepGenerated = sha256step :=
  funext fastStepGenerated_correct

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

theorem valid_fastStepGenerated (d : Digest) : ValidDigest (fastStepGenerated d) := by
  rw [fastStepGenerated_correct]
  unfold sha256step compress
  unfold ValidDigest
  exact ⟨add32_lt_base _ _, add32_lt_base _ _, add32_lt_base _,
    add32_lt_base _ _, add32_lt_base _ _, add32_lt_base _ _,
    add32_lt_base _ _, add32_lt_base _ _⟩

def packedStepGenerated (x : Nat) : Nat :=
  packDigestLE (fastStepGenerated (unpackDigestLE x))

def iterPackedGenerated : Nat → Nat → Nat
  | 0, x => x
  | t + 1, x => iterPackedGenerated t (packedStepGenerated x)

theorem iterPackedGenerated_correct :
    ∀ t d, ValidDigest d →
      unpackDigestLE (iterPackedGenerated t (packDigestLE d)) =
        iterDigest fastStepGenerated t d
  | 0, d, h => unpack_pack d h
  | t + 1, d, h => by
      simp only [iterPackedGenerated, packedStepGenerated, iterDigest]
      rw [unpack_pack d h]
      exact iterPackedGenerated_correct t (fastStepGenerated d)
        (valid_fastStepGenerated d)

def impl (n : Nat) : Nat :=
  let d0 := seedDigest (sha256Seed n)
  let packed := iterPackedGenerated (sha256Steps n) (packDigestLE d0)
  encodeDigest (unpackDigestLE packed)

theorem impl_correct : ∀ n, impl n = sha256Spec n := by
  intro n
  unfold impl sha256Spec iterSha
  rw [iterPackedGenerated_correct
      (sha256Steps n) (seedDigest (sha256Seed n))
      (valid_seedDigest (sha256Seed n))]
  rw [fastStepGenerated_fun]

end Submission
'''

text=prefix+body
p=OUT/"Submission_v8.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
