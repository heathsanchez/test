#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"algebra_v20.py"))
src=(OUT/"Submission_algebra_v20.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0] + "\n\n"

proof=r'''
/-! Quotient-level proof for the exact winning Algebra V20 evaluator. -/

theorem w32_eq : w32 = 2^32 - 1 := by decide

theorem mask32_eq_mod (x : Nat) :
    x &&& w32 = x % 2^32 := by
  rw [w32_eq, Nat.and_two_pow_sub_one_eq_mod]

theorem majFast_eq (x y z : Nat) :
    majFast x y z = maj x y z := by
  apply Nat.eq_of_testBit_eq
  intro i
  simp only [majFast, maj, Nat.testBit_xor, Nat.testBit_and]
  generalize x.testBit i = bx
  generalize y.testBit i = byy
  generalize z.testBit i = bz
  cases bx <;> cases byy <;> cases bz <;> decide

/--
The optimized choice function need not equal the trusted choice function above
bit 31. T1 is immediately reduced modulo 2^32, so equality in that quotient
is the exact consequential statement required by the evaluator.
-/
theorem chFast_mod_eq (x y z : Nat) :
    chFast x y z % 2^32 = ch x y z % 2^32 := by
  apply Nat.eq_of_testBit_eq
  intro i
  simp only [Nat.testBit_mod_two_pow]
  by_cases hi : i < 32
  · simp only [hi, decide_true, Bool.true_and]
    unfold chFast ch
    rw [w32_eq]
    simp only [Nat.testBit_xor, Nat.testBit_and,
      Nat.testBit_two_pow_sub_one, hi, decide_true]
    generalize x.testBit i = bx
    generalize y.testBit i = byy
    generalize z.testBit i = bz
    cases bx <;> cases byy <;> cases bz <;> decide
  · simp [hi]

theorem mask4_eq_nested (a b c d : Nat) :
    (a + b + c + d) &&& w32 =
      add32 (add32 a b) (add32 c d) := by
  simp only [add32, mask32_eq_mod]
  simp only [Nat.mod_add_mod, Nat.add_mod_mod]
  simp [Nat.add_assoc]

theorem mask5_eq_nested (a b c d e : Nat) :
    (a + b + c + d + e) &&& w32 =
      add32 a (add32 b (add32 c (add32 d e))) := by
  simp only [add32, mask32_eq_mod]
  simp only [Nat.add_mod_mod]
  simp [Nat.add_assoc]

theorem mask5_chFast_replace
    (a b x y z d e : Nat) :
    (a + b + chFast x y z + d + e) &&& w32 =
      (a + b + ch x y z + d + e) &&& w32 := by
  simp only [mask32_eq_mod]
  have hp :
      (a + b + chFast x y z) % 2^32 =
        (a + b + ch x y z) % 2^32 := by
    rw [← Nat.add_mod_mod (a + b) (chFast x y z) (2^32)]
    rw [← Nat.add_mod_mod (a + b) (ch x y z) (2^32)]
    rw [chFast_mod_eq]
  rw [Nat.add_assoc (a + b + chFast x y z) d e]
  rw [Nat.add_assoc (a + b + ch x y z) d e]
  rw [← Nat.mod_add_mod (a + b + chFast x y z) (2^32) (d + e)]
  rw [← Nat.mod_add_mod (a + b + ch x y z) (2^32) (d + e)]
  rw [hp]

theorem mask5_chFast_eq_nested
    (a b x y z d e : Nat) :
    (a + b + chFast x y z + d + e) &&& w32 =
      add32 a (add32 b (add32 (ch x y z) (add32 d e))) := by
  rw [mask5_chFast_replace a b x y z d e]
  exact mask5_eq_nested a b (ch x y z) d e

theorem roundFast_eq_round (s : Digest) (k w : Nat) :
    roundFast s k w = round s k w := by
  unfold roundFast round
  rw [majFast_eq s.a s.b s.c]
  rw [mask5_chFast_eq_nested
    s.h (bigSigma1 s.e) s.e s.f s.g k w]
  rw [show (bigSigma0 s.a + maj s.a s.b s.c) &&& w32 =
      add32 (bigSigma0 s.a) (maj s.a s.b s.c) by rfl]
  rfl

def Window.toList (w : Window) : List Nat :=
  [w.x0, w.x1, w.x2, w.x3, w.x4, w.x5, w.x6, w.x7,
   w.x8, w.x9, w.x10, w.x11, w.x12, w.x13, w.x14, w.x15]

def Window.nextWord (w : Window) : Nat :=
  add32 (add32 (smallSigma1 w.x14) w.x9)
    (add32 (smallSigma0 w.x1) w.x0)

theorem Window.nextFast_eq_nextWord (w : Window) :
    w.nextFast = w.nextWord := by
  unfold Window.nextFast Window.nextWord
  exact mask4_eq_nested
    (smallSigma1 w.x14) w.x9 (smallSigma0 w.x1) w.x0

def Window.advance (w : Window) : Window :=
  w.push w.nextWord

def roundsSlow : List Nat → Window → Digest → Digest
  | [], _, s => s
  | k :: ks, win, s =>
      roundsSlow ks win.advance (round s k win.x0)

theorem roundsFast_eq_slow :
    ∀ ks win s, roundsFast ks win s = roundsSlow ks win s
  | [], win, s => rfl
  | k :: ks, win, s => by
      simp only [roundsFast, roundsSlow]
      rw [Window.nextFast_eq_nextWord]
      rw [roundFast_eq_round s k win.x0]
      exact roundsFast_eq_slow ks win.advance (round s k win.x0)

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

def streamWords : Nat → Window → List Nat
  | 0, _ => []
  | k + 1, w => w.x0 :: streamWords k w.advance

theorem roundsSlow_eq (ks : List Nat) (w : Window) (s : Digest) :
    roundsSlow ks w s =
      roundsNoZip ks (streamWords ks.length w) s := by
  induction ks generalizing w s with
  | nil =>
      rfl
  | cons k ks ih =>
      simp only [roundsSlow, List.length_cons, streamWords, roundsNoZip]
      exact ih w.advance (round s k w.x0)

def advanceN : Nat → Window → Window
  | 0, w => w
  | k + 1, w => advanceN k w.advance

theorem streamWords_add :
    ∀ m n w, streamWords (m + n) w =
      streamWords m w ++ streamWords n (advanceN m w)
  | 0, n, w => by
      simp [streamWords, advanceN]
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

def finishProof (f : Digest) : Digest :=
  ⟨(iv.a + f.a) &&& w32, (iv.b + f.b) &&& w32,
   (iv.c + f.c) &&& w32, (iv.d + f.d) &&& w32,
   (iv.e + f.e) &&& w32, (iv.f + f.f) &&& w32,
   (iv.g + f.g) &&& w32, (iv.h + f.h) &&& w32⟩

def fastStepNoZipProof (d : Digest) : Digest :=
  finishProof (roundsNoZip K (fastSchedule d) iv)

theorem fastStepNoZipProof_correct (d : Digest) :
    fastStepNoZipProof d = sha256step d := by
  unfold fastStepNoZipProof finishProof sha256step compress
  rw [roundsNoZip_eq, schedule_correct]

theorem streamWordsK_eq_fastSchedule (d : Digest) :
    streamWords K.length (initialWindow d) = fastSchedule d := by
  have hk : K.length = 64 := by decide
  rw [hk, streamWords64_eq]
  rfl

theorem roundsFastK_eq_nozip (d : Digest) :
    roundsFast K (initialWindow d) iv =
      roundsNoZip K (fastSchedule d) iv := by
  calc
    roundsFast K (initialWindow d) iv =
        roundsSlow K (initialWindow d) iv :=
      roundsFast_eq_slow K (initialWindow d) iv
    _ = roundsNoZip K (streamWords K.length (initialWindow d)) iv :=
      roundsSlow_eq K (initialWindow d) iv
    _ = roundsNoZip K (fastSchedule d) iv := by
      rw [streamWordsK_eq_fastSchedule]

theorem fastStepAlgebra_eq_nozip (d : Digest) :
    fastStepAlgebra d = fastStepNoZipProof d := by
  calc
    fastStepAlgebra d =
        finishProof (roundsFast K (initialWindow d) iv) := by
      rfl
    _ = finishProof (roundsNoZip K (fastSchedule d) iv) :=
      congrArg finishProof (roundsFastK_eq_nozip d)
    _ = fastStepNoZipProof d := by
      rfl

theorem fastStepAlgebra_correct (d : Digest) :
    fastStepAlgebra d = sha256step d := by
  exact Eq.trans (fastStepAlgebra_eq_nozip d)
    (fastStepNoZipProof_correct d)

theorem fastStepAlgebra_fun : fastStepAlgebra = sha256step :=
  funext fastStepAlgebra_correct

theorem impl_correct : ∀ n, impl n = sha256Spec n := fun n =>
  congrArg
    (fun step => encodeDigest
      (iterDigest step (sha256Steps n) (seedDigest (sha256Seed n))))
    fastStepAlgebra_fun

end Submission
'''

out=prefix+proof
p=OUT/"Submission_algebra_v20_modproof.lean"
p.write_text(out)
print(f"generated {p} bytes={len(out.encode())}")
