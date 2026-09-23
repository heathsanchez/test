#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated"
OUT.mkdir(parents=True, exist_ok=True)

# Start from the already-qualified V25 submission/proof bank unchanged in its
# semantic machinery. Only its public impl is renamed to become the proof shadow.
runpy.run_path(str(ROOT / "algebra_v25_interaction.py"))
base = (OUT / "Submission_algebra_v25_interaction.lean").read_text()
base = base.replace("def impl (n : Nat) : Nat :=", "def implV25 (n : Nat) : Nat :=", 1)
base = base.replace(
    "theorem impl_correct : ∀ n, impl n = sha256Spec n := by",
    "theorem implV25_correct : ∀ n, implV25 n = sha256Spec n := by",
    1,
)
base = base.replace("  unfold impl sha256Spec iterSha", "  unfold implV25 sha256Spec iterSha", 1)
prefix = base.rsplit("\nend Submission", 1)[0] + "\n\n"

runtime = r'''
/-!
V34 runtime: exact computational shape of the V31 MulRotate + scalar-state
champion, under distinct names so V25 remains an untouched semantic shadow.
-/

def dup32V34 (x : Nat) : Nat := x * 4294967297

def smallSigma0V34 (x : Nat) : Nat :=
  let z := dup32V34 x
  (z >>> 7) ^^^ (z >>> 18) ^^^ (x >>> 3)

def smallSigma1V34 (x : Nat) : Nat :=
  let z := dup32V34 x
  (z >>> 17) ^^^ (z >>> 19) ^^^ (x >>> 10)

def bigSigma0V34 (x : Nat) : Nat :=
  let z := dup32V34 x
  (z >>> 2) ^^^ (z >>> 13) ^^^ (z >>> 22)

def bigSigma1V34 (x : Nat) : Nat :=
  let z := dup32V34 x
  (z >>> 6) ^^^ (z >>> 11) ^^^ (z >>> 25)
'''

wins = [f"w{i}" for i in range(16)]
sts = ["a","b","c","d","e","f","g","h"]
types = " → ".join(["Nat"] * 24 + ["Digest"])
nilpat = ", ".join(["[]"] + ["_"] * 16 + sts)
conspat = ", ".join(["k :: ks"] + wins + sts)
nextargs = " ".join(wins[1:] + ["nw","na","a","b","c","ne","e","f","g"])

runtime += f'''
def roundsScalarV34 : List Nat → {types}
  | {nilpat} => ⟨a,b,c,d,e,f,g,h⟩
  | {conspat} =>
      let nw := (smallSigma1V34 w14 + w9 + smallSigma0V34 w1 + w0) &&& w32
      let t1 := h + bigSigma1V34 e + chFast e f g + k + w0
      let t2 := bigSigma0V34 a + majFast a b c
      let na := (t1 + t2) &&& w32
      let ne := (d + t1) &&& w32
      roundsScalarV34 ks {nextargs}

def fastStepV34 (d : Digest) : Digest :=
  let f := roundsScalarV34 K
    d.a d.b d.c d.d d.e d.f d.g d.h
    0x80000000 0 0 0 0 0 0 256
    iv.a iv.b iv.c iv.d iv.e iv.f iv.g iv.h
  feedForwardIV f

def impl (n : Nat) : Nat :=
  encodeDigest
    (iterDigest fastStepV34 (sha256Steps n) (seedDigest (sha256Seed n)))
'''

proof = r'''
/-! Small interaction certificate from V34 runtime to the sealed V25 shadow. -/

theorem dup32V34_eq_or (x : Nat) (hx : x < 2^32) :
    dup32V34 x = (x <<< 32) ||| x := by
  unfold dup32V34
  rw [show 4294967297 = 2^32 + 1 by decide]
  rw [Nat.mul_add, Nat.mul_one]
  rw [Nat.shiftLeft_eq]
  rw [Nat.mul_comm x (2^32)]
  exact Nat.two_pow_add_eq_or_of_lt hx x

theorem shiftLeft32_shiftRightV34 (x n : Nat) (hn : n ≤ 32) :
    (x <<< 32) >>> n = x <<< (32 - n) := by
  rw [Nat.shiftLeft_eq, Nat.shiftRight_eq_div_pow, Nat.shiftLeft_eq]
  rw [← Nat.pow_sub_mul_pow 2 hn]
  rw [← Nat.mul_assoc]
  exact Nat.mul_div_cancel _ (Nat.two_pow_pos n)

theorem dup32V34_shift_eq_rotrRaw (x n : Nat)
    (hx : x < 2^32) (hn : n ≤ 32) :
    dup32V34 x >>> n = rotrRaw x n := by
  rw [dup32V34_eq_or x hx, Nat.shiftRight_or_distrib]
  rw [shiftLeft32_shiftRightV34 x n hn]
  unfold rotrRaw
  exact Nat.or_comm _ _

theorem smallSigma0V34_eq (x : Nat) (hx : x < 2^32) :
    smallSigma0V34 x = smallSigma0Fast x := by
  unfold smallSigma0V34 smallSigma0Fast
  simp only
  rw [dup32V34_shift_eq_rotrRaw x 7 hx (by decide)]
  rw [dup32V34_shift_eq_rotrRaw x 18 hx (by decide)]

theorem smallSigma1V34_eq (x : Nat) (hx : x < 2^32) :
    smallSigma1V34 x = smallSigma1Fast x := by
  unfold smallSigma1V34 smallSigma1Fast
  simp only
  rw [dup32V34_shift_eq_rotrRaw x 17 hx (by decide)]
  rw [dup32V34_shift_eq_rotrRaw x 19 hx (by decide)]

theorem bigSigma0V34_eq (x : Nat) (hx : x < 2^32) :
    bigSigma0V34 x = bigSigma0Fast x := by
  unfold bigSigma0V34 bigSigma0Fast
  simp only
  rw [dup32V34_shift_eq_rotrRaw x 2 hx (by decide)]
  rw [dup32V34_shift_eq_rotrRaw x 13 hx (by decide)]
  rw [dup32V34_shift_eq_rotrRaw x 22 hx (by decide)]

theorem bigSigma1V34_eq (x : Nat) (hx : x < 2^32) :
    bigSigma1V34 x = bigSigma1Fast x := by
  unfold bigSigma1V34 bigSigma1Fast
  simp only
  rw [dup32V34_shift_eq_rotrRaw x 6 hx (by decide)]
  rw [dup32V34_shift_eq_rotrRaw x 11 hx (by decide)]
  rw [dup32V34_shift_eq_rotrRaw x 25 hx (by decide)]

def roundsScalarViewV34 (ks : List Nat) (w : Window) (s : Digest) : Digest :=
  roundsScalarV34 ks
    w.x0 w.x1 w.x2 w.x3 w.x4 w.x5 w.x6 w.x7
    w.x8 w.x9 w.x10 w.x11 w.x12 w.x13 w.x14 w.x15
    s.a s.b s.c s.d s.e s.f s.g s.h

theorem roundsScalarViewV34_cons
    (k : Nat) (ks : List Nat) (w : Window) (s : Digest)
    (hw : ValidWindow w) (hs : ValidDigest s) :
    roundsScalarViewV34 (k :: ks) w s =
      roundsScalarViewV34 ks
        (w.push w.nextFast) (roundFast s k w.x0) := by
  unfold roundsScalarViewV34
  simp only [roundsScalarV34]
  unfold Window.push Window.nextFast roundFast
  rw [smallSigma1V34_eq w.x14 hw.x14]
  rw [smallSigma0V34_eq w.x1 hw.x1]
  rw [bigSigma1V34_eq s.e hs.e]
  rw [bigSigma0V34_eq s.a hs.a]

theorem valid_roundFastV25
    (s : Digest) (k w : Nat) (hs : ValidDigest s) :
    ValidDigest (roundFast s k w) := by
  rw [roundFast_eq_round s k w hs]
  exact valid_round s k w hs

theorem valid_push_nextFastV25 (w : Window) (hw : ValidWindow w) :
    ValidWindow (w.push w.nextFast) := by
  exact valid_push w w.nextFast hw (mask32_lt _)

theorem roundsScalarViewV34_eq_roundsFast :
    ∀ ks w s, ValidWindow w → ValidDigest s →
      roundsScalarViewV34 ks w s = roundsFast ks w s
  | [], w, s, hw, hs => by
      unfold roundsScalarViewV34
      rfl
  | k :: ks, w, s, hw, hs => by
      rw [roundsScalarViewV34_cons k ks w s hw hs]
      simp only [roundsFast]
      exact roundsScalarViewV34_eq_roundsFast
        ks (w.push w.nextFast) (roundFast s k w.x0)
        (valid_push_nextFastV25 w hw)
        (valid_roundFastV25 s k w.x0 hs)

theorem fastStepV34_eq_fastStepAlgebra
    (d : Digest) (hd : ValidDigest d) :
    fastStepV34 d = fastStepAlgebra d := by
  unfold fastStepV34 fastStepAlgebra
  apply congrArg feedForwardIV
  change roundsScalarViewV34 K (initialWindow d) iv =
    roundsFast K (initialWindow d) iv
  exact roundsScalarViewV34_eq_roundsFast
    K (initialWindow d) iv (valid_initialWindow d hd) valid_iv

theorem fastStepV34_correct (d : Digest) (hd : ValidDigest d) :
    fastStepV34 d = sha256step d := by
  rw [fastStepV34_eq_fastStepAlgebra d hd]
  exact fastStepAlgebra_correct d hd

theorem valid_fastStepV34 (d : Digest) (hd : ValidDigest d) :
    ValidDigest (fastStepV34 d) := by
  rw [fastStepV34_eq_fastStepAlgebra d hd]
  exact valid_fastStepAlgebra d

theorem iterV34_correct (t : Nat) (d : Digest) (hd : ValidDigest d) :
    iterDigest fastStepV34 t d = iterDigest sha256step t d :=
  iterDigest_congr_of_invariant
    ValidDigest fastStepV34 sha256step
    fastStepV34_correct valid_fastStepV34 t d hd

theorem impl_correct : ∀ n, impl n = sha256Spec n := by
  intro n
  unfold impl sha256Spec iterSha
  exact congrArg encodeDigest
    (iterV34_correct
      (sha256Steps n) (seedDigest (sha256Seed n))
      (valid_seedDigest (sha256Seed n)))

end Submission
'''

text = prefix + runtime + proof
p = OUT / "Submission_mulrotate_scalar_v34_shadow_proof.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
