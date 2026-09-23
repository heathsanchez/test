#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"mulrotate_scalar_v31_probe.py"))
runpy.run_path(str(ROOT/"algebra_v25_interaction.py"))
runpy.run_path(str(ROOT/"v31_sigma_proof_dev.py"))

v31=(OUT/"Submission_mulrotate_scalar_v31_probe.lean").read_text()
v25=(OUT/"Submission_algebra_v25_interaction.lean").read_text()
sig=(OUT/"V31SigmaProofDev.lean").read_text()

runtime=v31.rsplit("\nend Submission",1)[0]
runtime=runtime.replace("def implV31 (n : Nat) : Nat :=", "def impl (n : Nat) : Nat :=", 1)

def between(s,a,b):
    return s[s.index(a):s.index(b)]

# V25 generic modular helpers, excluding its old sigma lemmas.
helpers=between(v25,"theorem w32_eq :","theorem bigSigma0Fast_mod_eq")

# V31 fixed-width dup32 rotate/sigma certificate; reuse generic V25 mask helper names.
sigblock=between(sig,"theorem dup32_eq_or_v31","\nend Submission")
sigblock=(sigblock
    .replace("_v31","")
    .replace("mask32_eq_mod_v31","mask32_eq_mod")
    .replace("and_mask32_eq_self_v31","and_mask32_eq_self"))

# Bounds + congruence wrappers required by the V25 round shadow.
modwrap=r'''
theorem bigSigma0_lt (x : Nat) (hx : x < 2^32) : bigSigma0 x < 2^32 := by
  have h := Nat.mod_lt (bigSigma0Fast x) (by decide : 0 < 2^32)
  rw [bigSigma0Fast_mod_eq x hx] at h
  exact h

theorem bigSigma1_lt (x : Nat) (hx : x < 2^32) : bigSigma1 x < 2^32 := by
  have h := Nat.mod_lt (bigSigma1Fast x) (by decide : 0 < 2^32)
  rw [bigSigma1Fast_mod_eq x hx] at h
  exact h

theorem smallSigma0_lt (x : Nat) (hx : x < 2^32) : smallSigma0 x < 2^32 := by
  have h := Nat.mod_lt (smallSigma0Fast x) (by decide : 0 < 2^32)
  rw [smallSigma0Fast_mod_eq x hx] at h
  exact h

theorem smallSigma1_lt (x : Nat) (hx : x < 2^32) : smallSigma1 x < 2^32 := by
  have h := Nat.mod_lt (smallSigma1Fast x) (by decide : 0 < 2^32)
  rw [smallSigma1Fast_mod_eq x hx] at h
  exact h

theorem bigSigma0Fast_mod32 (x : Nat) (hx : x < 2^32) :
    Mod32Eq (bigSigma0Fast x) (bigSigma0 x) := by
  unfold Mod32Eq
  rw [bigSigma0Fast_mod_eq x hx, Nat.mod_eq_of_lt (bigSigma0_lt x hx)]

theorem bigSigma1Fast_mod32 (x : Nat) (hx : x < 2^32) :
    Mod32Eq (bigSigma1Fast x) (bigSigma1 x) := by
  unfold Mod32Eq
  rw [bigSigma1Fast_mod_eq x hx, Nat.mod_eq_of_lt (bigSigma1_lt x hx)]

theorem smallSigma0Fast_mod32 (x : Nat) (hx : x < 2^32) :
    Mod32Eq (smallSigma0Fast x) (smallSigma0 x) := by
  unfold Mod32Eq
  rw [smallSigma0Fast_mod_eq x hx, Nat.mod_eq_of_lt (smallSigma0_lt x hx)]

theorem smallSigma1Fast_mod32 (x : Nat) (hx : x < 2^32) :
    Mod32Eq (smallSigma1Fast x) (smallSigma1 x) := by
  unfold Mod32Eq
  rw [smallSigma1Fast_mod_eq x hx, Nat.mod_eq_of_lt (smallSigma1_lt x hx)]
'''

# Boolean and nested-add helpers are unchanged.
boolhelpers=between(v25,"theorem majFast_eq","structure ValidDigest")

# State/window validity bank.
validity=between(v25,"structure ValidDigest","def t1Raw")

# V25 round shadow, adapted so big sigmas receive the bounded-state hypothesis.
roundbridge=between(v25,"def t1Raw","def Window.toList")
roundbridge=roundbridge.replace(
    "theorem t2_mod32 (s : Digest) :",
    "theorem t2_mod32 (s : Digest) (hs : ValidDigest s) :")
roundbridge=roundbridge.replace(
    "(bigSigma1Fast_mod32 s.e)",
    "(bigSigma1Fast_mod32 s.e hs.e)")
roundbridge=roundbridge.replace(
    "(bigSigma0Fast_mod32 s.a)",
    "(bigSigma0Fast_mod32 s.a hs.a)")
roundbridge=roundbridge.replace(
    "(t2_mod32 s))",
    "(t2_mod32 s hs))")

# V25 window bridge already passes ValidWindow bounds into small sigmas.
windowbridge=between(v25,"def Window.toList","def Window.advance")

shadow=r'''
/-! Compact proof-only recursive shadow for the measured V31 scalar runtime. -/

def roundsScalarMulW (ks : List Nat) (w : Window) (s : Digest) : Digest :=
  roundsScalarMul ks
    w.x0 w.x1 w.x2 w.x3 w.x4 w.x5 w.x6 w.x7
    w.x8 w.x9 w.x10 w.x11 w.x12 w.x13 w.x14 w.x15
    s.a s.b s.c s.d s.e s.f s.g s.h

def roundsShadow : List Nat → Window → Digest → Digest
  | [], _, s => s
  | k :: ks, w, s =>
      roundsShadow ks (w.push w.nextFast) (roundFast s k w.x0)

theorem scalar_nil (w : Window) (s : Digest) :
    roundsScalarMulW [] w s = s := by
  unfold roundsScalarMulW
  rw [roundsScalarMul]

theorem scalar_cons (k : Nat) (ks : List Nat) (w : Window) (s : Digest) :
    roundsScalarMulW (k :: ks) w s =
      roundsScalarMulW ks (w.push w.nextFast) (roundFast s k w.x0) := by
  rcases w with ⟨w0,w1,w2,w3,w4,w5,w6,w7,w8,w9,w10,w11,w12,w13,w14,w15⟩
  rcases s with ⟨a,b,c,d,e,f,g,h⟩
  unfold roundsScalarMulW
  rw [roundsScalarMul]
  rfl

theorem scalar_eq_shadow (ks : List Nat) :
    ∀ w s, roundsScalarMulW ks w s = roundsShadow ks w s := by
  induction ks with
  | nil =>
      intro w s
      rw [scalar_nil]
      rfl
  | cons k ks ih =>
      intro w s
      rw [scalar_cons]
      exact ih (w.push w.nextFast) (roundFast s k w.x0)
'''

advance=between(v25,"def Window.advance","def roundsSlow")

slow=r'''
def roundsSlow : List Nat → Window → Digest → Digest
  | [], _, s => s
  | k :: ks, win, s =>
      roundsSlow ks win.advance (round s k win.x0)

theorem roundsShadow_eq_slow :
    ∀ ks win s, ValidDigest s → ValidWindow win →
      roundsShadow ks win s = roundsSlow ks win s
  | [], win, s, hs, hw => rfl
  | k :: ks, win, s, hs, hw => by
      simp only [roundsShadow, roundsSlow]
      rw [Window.nextFast_eq_nextWord win hw]
      rw [roundFast_eq_round s k win.x0 hs]
      exact roundsShadow_eq_slow ks win.advance (round s k win.x0)
        (valid_round s k win.x0 hs) (valid_advance win hw)
'''

# Reuse schedule/nozip proof through the point where the fast runtime is attached.
schedule=between(v25,"def generate","theorem roundsFastK_eq_nozip")
# Keep feedForwardIV_eq_old and streamWordsK theorem, which are inside schedule.

final=r'''
theorem roundsScalarK_eq_nozip (d : Digest) (hd : ValidDigest d) :
    roundsScalarMulW K (initialWindow d) iv =
      roundsNoZip K (fastSchedule d) iv := by
  calc
    roundsScalarMulW K (initialWindow d) iv =
        roundsShadow K (initialWindow d) iv :=
      scalar_eq_shadow K (initialWindow d) iv
    _ = roundsSlow K (initialWindow d) iv :=
      roundsShadow_eq_slow K (initialWindow d) iv valid_iv
        (valid_initialWindow d hd)
    _ = roundsNoZip K (streamWords K.length (initialWindow d)) iv :=
      roundsSlow_eq K (initialWindow d) iv
    _ = roundsNoZip K (fastSchedule d) iv := by
      rw [streamWordsK_eq_fastSchedule]

theorem fastStepV31_eq_nozip (d : Digest) (hd : ValidDigest d) :
    fastStepV31 d = fastStepNoZipProof d := by
  change
    feedForwardIV (roundsScalarMulW K (initialWindow d) iv) =
      feedForwardOld (roundsNoZip K (fastSchedule d) iv)
  rw [roundsScalarK_eq_nozip d hd]
  exact feedForwardIV_eq_old _

theorem fastStepV31_correct (d : Digest) (hd : ValidDigest d) :
    fastStepV31 d = sha256step d := by
  rw [fastStepV31_eq_nozip d hd]
  exact fastStepNoZipProof_correct d

theorem valid_fastStepV31 (d : Digest) : ValidDigest (fastStepV31 d) := by
  unfold fastStepV31 feedForwardIV
  constructor <;> exact mask32_lt _

'''

iterhelpers=between(v25,"theorem seedStep32_lt","theorem iterAlgebra_correct")

finish=r'''
theorem iterV31_correct (t : Nat) (d : Digest) (hd : ValidDigest d) :
    iterDigest fastStepV31 t d = iterDigest sha256step t d :=
  iterDigest_congr_of_invariant
    ValidDigest fastStepV31 sha256step
    fastStepV31_correct (fun d _ => valid_fastStepV31 d) t d hd

theorem impl_correct : ∀ n, impl n = sha256Spec n := by
  intro n
  unfold impl implV31 sha256Spec iterSha
  exact congrArg encodeDigest
    (iterV31_correct
      (sha256Steps n) (seedDigest (sha256Seed n))
      (valid_seedDigest (sha256Seed n)))

end Submission
'''

# implV31 has been renamed to impl, so the final proof must not unfold the old name.
finish=finish.replace("unfold impl implV31 sha256Spec iterSha","unfold impl sha256Spec iterSha")

text="\n\n".join([
    runtime,helpers,sigblock,modwrap,boolhelpers,validity,roundbridge,
    windowbridge,shadow,advance,slow,schedule,final,iterhelpers,finish
])
p=OUT/"Submission_v31_interaction_proof.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
