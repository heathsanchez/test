#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"mulrotate_scalar_v31_probe.py"))
runpy.run_path(str(ROOT/"algebra_v25_interaction.py"))
runpy.run_path(str(ROOT/"v31_sigma_proof_dev.py"))
runpy.run_path(str(ROOT/"v31_proof_state_interface.py"))

v31=(OUT/"Submission_mulrotate_scalar_v31_probe.lean").read_text()
v25=(OUT/"Submission_algebra_v25_interaction.lean").read_text()
sig=(OUT/"V31SigmaProofDev.lean").read_text()
pst=(OUT/"V31ProofStateInterface.lean").read_text()

runtime=v31.rsplit("\nend Submission",1)[0]
runtime=runtime.replace("def implV31 (n : Nat) : Nat :=", "def impl (n : Nat) : Nat :=", 1)

def between(s,a,b):
    return s[s.index(a):s.index(b)]

helpers=between(v25,"theorem w32_eq :","theorem bigSigma0Fast_mod_eq")
sigblock=between(sig,"theorem dup32_eq_or_v31","\nend Submission")
sigblock=(sigblock.replace("_v31","")
    .replace("mask32_eq_mod_v31","mask32_eq_mod")
    .replace("and_mask32_eq_self_v31","and_mask32_eq_self"))

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

boolhelpers=between(v25,"theorem majFast_eq","structure ValidDigest")
validity=between(v25,"structure ValidDigest","def t1Raw")
roundbridge=between(v25,"def t1Raw","def Window.toList")
roundbridge=roundbridge.replace(
    "theorem t2_mod32 (s : Digest) :",
    "theorem t2_mod32 (s : Digest) (hs : ValidDigest s) :")
roundbridge=roundbridge.replace("(bigSigma1Fast_mod32 s.e)","(bigSigma1Fast_mod32 s.e hs.e)")
roundbridge=roundbridge.replace("(bigSigma0Fast_mod32 s.a)","(bigSigma0Fast_mod32 s.a hs.a)")
roundbridge=roundbridge.replace("(t2_mod32 s))","(t2_mod32 s hs))")
windowbridge=between(v25,"def Window.toList","def Window.advance")
advance=between(v25,"def Window.advance","def roundsSlow")

roundslow=r'''
def roundsSlow : List Nat → Window → Digest → Digest
  | [], _, s => s
  | k :: ks, win, s =>
      roundsSlow ks win.advance (round s k win.x0)
'''

# Exactly the already-green proof-only compressed interface.
pstate=between(pst,"structure ProofState","\nend Submission")

packed_slow=r'''
def ValidProofState (p : ProofState) : Prop :=
  ValidWindow p.window ∧ ValidDigest p.digest

def ProofState.slowNext (k : Nat) (p : ProofState) : ProofState :=
  ProofState.ofWS p.window.advance (round p.digest k p.window.x0)

def slowPacked (ks : List Nat) (p : ProofState) : Digest :=
  roundsSlow ks p.window p.digest

theorem slowPacked_nil (p : ProofState) :
    slowPacked [] p = p.digest := by
  rfl

theorem slowPacked_cons (k : Nat) (ks : List Nat) (p : ProofState) :
    slowPacked (k :: ks) p = slowPacked ks (p.slowNext k) := by
  rfl

theorem proofState_next_eq_slowNext
    (k : Nat) (p : ProofState) (hp : ValidProofState p) :
    p.next k = p.slowNext k := by
  unfold ProofState.next ProofState.slowNext
  dsimp
  rw [Window.nextFast_eq_nextWord p.window hp.1]
  rw [roundFast_eq_round p.digest k p.window.x0 hp.2]
  rfl

theorem valid_slowNext (k : Nat) (p : ProofState) (hp : ValidProofState p) :
    ValidProofState (p.slowNext k) := by
  unfold ValidProofState ProofState.slowNext
  constructor
  · exact valid_advance p.window hp.1
  · exact valid_round p.digest k p.window.x0 hp.2

theorem valid_next (k : Nat) (p : ProofState) (hp : ValidProofState p) :
    ValidProofState (p.next k) := by
  rw [proofState_next_eq_slowNext k p hp]
  exact valid_slowNext k p hp

/-- Pure abstract transport theorem; no SHA implementation appears in its proof. -/
theorem runners_equal_step_congr
    {K P O : Type}
    (Good : P → Prop)
    (nextF nextG : K → P → P)
    (F G : List K → P → O)
    (fNil : ∀ p, F [] p = G [] p)
    (fCons : ∀ k ks p, F (k :: ks) p = F ks (nextF k p))
    (gCons : ∀ k ks p, G (k :: ks) p = G ks (nextG k p))
    (nextEq : ∀ k p, Good p → nextF k p = nextG k p)
    (nextGood : ∀ k p, Good p → Good (nextF k p)) :
    ∀ ks p, Good p → F ks p = G ks p := by
  intro ks
  induction ks with
  | nil =>
      intro p hp
      exact fNil p
  | cons k ks ih =>
      intro p hp
      calc
        F (k :: ks) p = F ks (nextF k p) := fCons k ks p
        _ = G ks (nextF k p) := ih (nextF k p) (nextGood k p hp)
        _ = G ks (nextG k p) := by rw [nextEq k p hp]
        _ = G (k :: ks) p := (gCons k ks p).symm

theorem shadowPacked_eq_slowPacked :
    ∀ ks p, ValidProofState p → shadowPacked ks p = slowPacked ks p :=
  runners_equal_step_congr
    ValidProofState ProofState.next ProofState.slowNext
    shadowPacked slowPacked
    (fun p => by rfl)
    shadowPacked_cons slowPacked_cons
    proofState_next_eq_slowNext valid_next

theorem valid_initialProofState (d : Digest) (hd : ValidDigest d) :
    ValidProofState (ProofState.ofWS (initialWindow d) iv) := by
  constructor
  · exact valid_initialWindow d hd
  · exact valid_iv
'''

schedule=between(v25,"def generate","theorem roundsFastK_eq_nozip")

final=r'''
theorem packedK_eq_nozip (d : Digest) (hd : ValidDigest d) :
    scalarPacked K (ProofState.ofWS (initialWindow d) iv) =
      roundsNoZip K (fastSchedule d) iv := by
  calc
    scalarPacked K (ProofState.ofWS (initialWindow d) iv) =
        shadowPacked K (ProofState.ofWS (initialWindow d) iv) :=
      scalarPacked_eq_shadowPacked K (ProofState.ofWS (initialWindow d) iv)
    _ = slowPacked K (ProofState.ofWS (initialWindow d) iv) :=
      shadowPacked_eq_slowPacked K (ProofState.ofWS (initialWindow d) iv)
        (valid_initialProofState d hd)
    _ = roundsSlow K (initialWindow d) iv := by rfl
    _ = roundsNoZip K (streamWords K.length (initialWindow d)) iv :=
      roundsSlow_eq K (initialWindow d) iv
    _ = roundsNoZip K (fastSchedule d) iv := by
      rw [streamWordsK_eq_fastSchedule]

theorem fastStepV31_eq_nozip (d : Digest) (hd : ValidDigest d) :
    fastStepV31 d = fastStepNoZipProof d := by
  change
    feedForwardIV
      (scalarPacked K (ProofState.ofWS (initialWindow d) iv)) =
      feedForwardOld (roundsNoZip K (fastSchedule d) iv)
  rw [packedK_eq_nozip d hd]
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
  unfold impl sha256Spec iterSha
  exact congrArg encodeDigest
    (iterV31_correct
      (sha256Steps n) (seedDigest (sha256Seed n))
      (valid_seedDigest (sha256Seed n)))

end Submission
'''

text="\n\n".join([
 runtime,helpers,sigblock,modwrap,boolhelpers,validity,roundbridge,
 windowbridge,advance,roundslow,pstate,packed_slow,schedule,final,iterhelpers,finish
])
p=OUT/"Submission_v31_interaction_proof_v2.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
