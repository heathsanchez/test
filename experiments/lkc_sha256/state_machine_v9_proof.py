#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"state_machine_v9.py"))
src=(OUT/"Submission_state_v9.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0] + "\n\n"

proof=r'''
/- Proof-only bridge. The evaluated path above remains the tiny state machine. -/

def Window.toList (w : Window) : List Nat :=
  [w.x0, w.x1, w.x2, w.x3, w.x4, w.x5, w.x6, w.x7,
   w.x8, w.x9, w.x10, w.x11, w.x12, w.x13, w.x14, w.x15]

def Window.push (w : Window) (x : Nat) : Window :=
  ⟨w.x1, w.x2, w.x3, w.x4, w.x5, w.x6, w.x7, w.x8,
   w.x9, w.x10, w.x11, w.x12, w.x13, w.x14, w.x15, x⟩

theorem advance_eq_push (w : Window) :
    w.advance = w.push w.nextWord := by
  rfl

def generate : Nat → Window → List Nat
  | 0, _ => []
  | k + 1, w =>
      let x := w.nextWord
      x :: generate k (w.push x)

def fastSchedule (d : Digest) : List Nat :=
  let w := initialWindow d
  w.toList ++ generate 48 w

def roundsNoZip : List Nat → List Nat → Digest → Digest
  | [], _, s => s
  | _, [], s => s
  | k :: ks, w :: ws, s => roundsNoZip ks ws (round s k w)

theorem roundsNoZip_eq (ks ws : List Nat) (s : Digest) :
    roundsNoZip ks ws s = rounds (ks.zip ws) s := by
  induction ks generalizing ws s with
  | nil =>
      simp [roundsNoZip, rounds]
  | cons k ks ih =>
      cases ws with
      | nil =>
          simp [roundsNoZip, rounds]
      | cons w ws =>
          simp [roundsNoZip, rounds, ih]

theorem drop_last16 (pre : List Nat) (w : Window) :
    (pre ++ w.toList).drop ((pre ++ w.toList).length - 16) = w.toList := by
  simp [Window.toList]

theorem nextWord_eq (w : Window) :
    add32 (add32 (smallSigma1 (w.toList.getD 14 0)) (w.toList.getD 9 0))
      (add32 (smallSigma0 (w.toList.getD 1 0)) (w.toList.getD 0 0)) =
      w.nextWord := by
  rfl

theorem append_push (pre : List Nat) (w : Window) :
    (pre ++ w.toList) ++ [w.nextWord] =
      (pre ++ [w.x0]) ++ (w.push w.nextWord).toList := by
  simp [Window.toList, Window.push]

theorem extend_eq : ∀ k pre w,
    extendW k (pre ++ w.toList) =
      pre ++ w.toList ++ generate k w
  | 0, pre, w => by
      simp [extendW, generate]
  | k + 1, pre, w => by
      rw [extendW, drop_last16, nextWord_eq, append_push]
      rw [extend_eq k (pre ++ [w.x0]) (w.push w.nextWord)]
      simp [generate, Window.toList, Window.push, List.append_assoc]

theorem schedule_correct (d : Digest) :
    fastSchedule d =
      extendW 48 [d.a, d.b, d.c, d.d, d.e, d.f, d.g, d.h,
        0x80000000, 0, 0, 0, 0, 0, 0, 256] := by
  simpa [fastSchedule, initialWindow, Window.toList] using
    (extend_eq 48 [] (initialWindow d)).symm

/-- The words exposed by successive state transitions. -/
def streamWords : Nat → Window → List Nat
  | 0, _ => []
  | k + 1, w => w.x0 :: streamWords k w.advance

theorem roundsWindow_eq (ks : List Nat) (w : Window) (s : Digest) :
    roundsWindow ks w s =
      roundsNoZip ks (streamWords ks.length w) s := by
  induction ks generalizing w s with
  | nil =>
      rfl
  | cons k ks ih =>
      simp only [roundsWindow, List.length_cons, streamWords, roundsNoZip]
      exact ih w.advance (round s k w.x0)

def advanceN : Nat → Window → Window
  | 0, w => w
  | k + 1, w => advanceN k w.advance

theorem streamWords_add :
    ∀ m n w, streamWords (m + n) w =
      streamWords m w ++ streamWords n (advanceN m w)
  | 0, n, w => by
      rfl
  | m + 1, n, w => by
      simp only [Nat.succ_add, streamWords, advanceN, List.cons_append]
      rw [streamWords_add m n w.advance]

theorem streamWords16_eq_toList (w : Window) :
    streamWords 16 w = w.toList := by
  rcases w with ⟨x0,x1,x2,x3,x4,x5,x6,x7,x8,x9,x10,x11,x12,x13,x14,x15⟩
  rfl

theorem advanceN_succ_right :
    ∀ k w, (advanceN k w).advance = advanceN k w.advance
  | 0, w => rfl
  | k + 1, w => by
      simp only [advanceN]
      exact advanceN_succ_right k w.advance

theorem advanceN16_x0 (w : Window) :
    (advanceN 16 w).x0 = w.nextWord := by
  rcases w with ⟨x0,x1,x2,x3,x4,x5,x6,x7,x8,x9,x10,x11,x12,x13,x14,x15⟩
  rfl

theorem streamWords_after16_eq_generate :
    ∀ k w, streamWords k (advanceN 16 w) = generate k w
  | 0, w => rfl
  | k + 1, w => by
      simp only [streamWords, generate]
      rw [advanceN16_x0]
      rw [advanceN_succ_right 16 w]
      exact congrArg (List.cons w.nextWord)
        (streamWords_after16_eq_generate k w.advance)

theorem streamWords64_eq (w : Window) :
    streamWords 64 w = w.toList ++ generate 48 w := by
  change streamWords (16 + 48) w = _
  rw [streamWords_add]
  rw [streamWords16_eq_toList]
  rw [streamWords_after16_eq_generate]

def fastStepNoZip (d : Digest) : Digest :=
  let f := roundsNoZip K (fastSchedule d) iv
  ⟨add32 iv.a f.a, add32 iv.b f.b, add32 iv.c f.c, add32 iv.d f.d,
   add32 iv.e f.e, add32 iv.f f.f, add32 iv.g f.g, add32 iv.h f.h⟩

theorem fastStepNoZip_correct (d : Digest) : fastStepNoZip d = sha256step d := by
  unfold fastStepNoZip sha256step compress
  rw [roundsNoZip_eq, schedule_correct]

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

theorem impl_correct : ∀ n, impl n = sha256Spec n := fun n =>
  congrArg
    (fun step => encodeDigest
      (iterDigest step (sha256Steps n) (seedDigest (sha256Seed n))))
    fastStepWindow_fun

end Submission
'''

text=prefix+proof
p=OUT/"Submission_state_v9_proof.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
