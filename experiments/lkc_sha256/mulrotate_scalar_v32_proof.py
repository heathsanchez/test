#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated"
OUT.mkdir(parents=True, exist_ok=True)

# Runtime side: exact V31 probe.
runpy.run_path(str(ROOT / "mulrotate_scalar_v31_probe.py"))
v31 = (OUT / "Submission_mulrotate_scalar_v31_probe.lean").read_text()
runtime = v31.rsplit("\nend Submission", 1)[0] + "\n\n"

# Proof side: reuse the already-qualified V25 certificate bank, replacing only
# the four sigma facts whose implementation changed from OR-rotate to dup32.
runpy.run_path(str(ROOT / "algebra_v25_interaction.py"))
v25 = (OUT / "Submission_algebra_v25_interaction.lean").read_text()
proof = v25[v25.index("theorem w32_eq"):v25.index("theorem impl_correct")]

a = proof.index("theorem bigSigma0Fast_mod_eq")
b = proof.index("theorem majFast_eq")
mulrotate = r'''
/-! V32 interaction bridge: multiplication-fused rotations. -/

theorem dup32_eq_or (x : Nat) (hx : x < 2^32) :
    dup32 x = (x <<< 32) ||| x := by
  unfold dup32
  rw [show 4294967297 = 2^32 + 1 by decide]
  rw [Nat.mul_add, Nat.mul_one]
  rw [Nat.shiftLeft_eq]
  rw [Nat.mul_comm x (2^32)]
  exact Nat.two_pow_add_eq_or_of_lt hx x

theorem shiftLeft32_shiftRight (x n : Nat) (hn : n ≤ 32) :
    (x <<< 32) >>> n = x <<< (32 - n) := by
  rw [Nat.shiftLeft_eq, Nat.shiftRight_eq_div_pow, Nat.shiftLeft_eq]
  rw [← Nat.pow_sub_mul_pow 2 hn]
  rw [← Nat.mul_assoc]
  exact Nat.mul_div_cancel _ (Nat.two_pow_pos n)

theorem dup32_shift_eq_rotrRaw (x n : Nat)
    (hx : x < 2^32) (hn : n ≤ 32) :
    dup32 x >>> n = rotrRaw x n := by
  rw [dup32_eq_or x hx, Nat.shiftRight_or_distrib]
  rw [shiftLeft32_shiftRight x n hn]
  unfold rotrRaw
  simpa [Nat.or_comm]

theorem bigSigma0Fast_mod_eq (x : Nat) (hx : x < 2^32) :
    bigSigma0Fast x % 2^32 = bigSigma0 x := by
  unfold bigSigma0Fast
  simp only
  rw [dup32_shift_eq_rotrRaw x 2 hx (by decide)]
  rw [dup32_shift_eq_rotrRaw x 13 hx (by decide)]
  rw [dup32_shift_eq_rotrRaw x 22 hx (by decide)]
  rw [← mask32_eq_mod]
  unfold bigSigma0 rotr32
  rw [Nat.and_xor_distrib_right, Nat.and_xor_distrib_right]

theorem bigSigma1Fast_mod_eq (x : Nat) (hx : x < 2^32) :
    bigSigma1Fast x % 2^32 = bigSigma1 x := by
  unfold bigSigma1Fast
  simp only
  rw [dup32_shift_eq_rotrRaw x 6 hx (by decide)]
  rw [dup32_shift_eq_rotrRaw x 11 hx (by decide)]
  rw [dup32_shift_eq_rotrRaw x 25 hx (by decide)]
  rw [← mask32_eq_mod]
  unfold bigSigma1 rotr32
  rw [Nat.and_xor_distrib_right, Nat.and_xor_distrib_right]

theorem smallSigma0Fast_mod_eq (x : Nat) (hx : x < 2^32) :
    smallSigma0Fast x % 2^32 = smallSigma0 x := by
  unfold smallSigma0Fast
  simp only
  rw [dup32_shift_eq_rotrRaw x 7 hx (by decide)]
  rw [dup32_shift_eq_rotrRaw x 18 hx (by decide)]
  rw [← mask32_eq_mod]
  unfold smallSigma0 rotr32
  rw [Nat.and_xor_distrib_right, Nat.and_xor_distrib_right]
  have hs : x >>> 3 < 2^32 :=
    Nat.lt_of_le_of_lt (Nat.shiftRight_le x 3) hx
  rw [and_mask32_eq_self (x >>> 3) hs]

theorem smallSigma1Fast_mod_eq (x : Nat) (hx : x < 2^32) :
    smallSigma1Fast x % 2^32 = smallSigma1 x := by
  unfold smallSigma1Fast
  simp only
  rw [dup32_shift_eq_rotrRaw x 17 hx (by decide)]
  rw [dup32_shift_eq_rotrRaw x 19 hx (by decide)]
  rw [← mask32_eq_mod]
  unfold smallSigma1 rotr32
  rw [Nat.and_xor_distrib_right, Nat.and_xor_distrib_right]
  have hs : x >>> 10 < 2^32 :=
    Nat.lt_of_le_of_lt (Nat.shiftRight_le x 10) hx
  rw [and_mask32_eq_self (x >>> 10) hs]

theorem bigSigma0_lt (x : Nat) (hx : x < 2^32) : bigSigma0 x < 2^32 := by
  have h := Nat.mod_lt (bigSigma0Fast x) (by decide : 0 < 2^32)
  rw [bigSigma0Fast_mod_eq x hx] at h
  exact h

theorem bigSigma1_lt (x : Nat) (hx : x < 2^32) : bigSigma1 x < 2^32 := by
  have h := Nat.mod_lt (bigSigma1Fast x) (by decide : 0 < 2^32)
  rw [bigSigma1Fast_mod_eq x hx] at h
  exact h

theorem smallSigma0_lt (x : Nat) (hx : x < 2^32) :
    smallSigma0 x < 2^32 := by
  have h := Nat.mod_lt (smallSigma0Fast x) (by decide : 0 < 2^32)
  rw [smallSigma0Fast_mod_eq x hx] at h
  exact h

theorem smallSigma1_lt (x : Nat) (hx : x < 2^32) :
    smallSigma1 x < 2^32 := by
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
proof = proof[:a] + mulrotate + proof[b:]
proof = proof.replace(
    "(bigSigma1Fast_mod32 s.e)",
    "(bigSigma1Fast_mod32 s.e hs.e)"
).replace(
    "(bigSigma0Fast_mod32 s.a)",
    "(bigSigma0Fast_mod32 s.a hs.a)"
)

wins = [f"w{i}" for i in range(16)]
sts = ["a","b","c","d","e","f","g","h"]
all_names = wins + sts
binders = " ".join(f"({x} : Nat)" for x in all_names)
args = " ".join(all_names)
win_ctor = "⟨" + ",".join(wins) + "⟩"
st_ctor = "⟨" + ",".join(sts) + "⟩"
nextargs = " ".join(wins[1:] + ["nw","na","a","b","c","ne","e","f","g"])
intro_names = " ".join(all_names)

scalar = f'''
/-! V32 interaction bridge: scalar recursion to the structured V30/V25 machine. -/

theorem roundsScalarMul_eq_roundsFast :
    ∀ (ks : List Nat) {binders},
      roundsScalarMul ks {args} =
        roundsFast ks {win_ctor} {st_ctor} := by
  intro ks
  induction ks with
  | nil =>
      intro {intro_names}
      rfl
  | cons k ks ih =>
      intro {intro_names}
      simp only [roundsScalarMul, roundsFast]
      simpa [Window.nextFast, Window.push, roundFast] using
        (ih {nextargs})

theorem fastStepV31_eq_fastStepAlgebra (d : Digest) :
    fastStepV31 d = fastStepAlgebra d := by
  unfold fastStepV31 fastStepAlgebra
  apply congrArg feedForwardIV
  simpa [initialWindow] using
    (roundsScalarMul_eq_roundsFast K
      d.a d.b d.c d.d d.e d.f d.g d.h
      0x80000000 0 0 0 0 0 0 256
      iv.a iv.b iv.c iv.d iv.e iv.f iv.g iv.h)

theorem fastStepV31_correct (d : Digest) (hd : ValidDigest d) :
    fastStepV31 d = sha256step d := by
  rw [fastStepV31_eq_fastStepAlgebra]
  exact fastStepAlgebra_correct d hd

theorem valid_fastStepV31 (d : Digest) :
    ValidDigest (fastStepV31 d) := by
  rw [fastStepV31_eq_fastStepAlgebra]
  exact valid_fastStepAlgebra d

theorem iterV31_correct (t : Nat) (d : Digest) (hd : ValidDigest d) :
    iterDigest fastStepV31 t d = iterDigest sha256step t d :=
  iterDigest_congr_of_invariant
    ValidDigest fastStepV31 sha256step
    fastStepV31_correct (fun d _ => valid_fastStepV31 d) t d hd

def impl (n : Nat) : Nat :=
  encodeDigest
    (iterDigest fastStepV31 (sha256Steps n) (seedDigest (sha256Seed n)))

theorem impl_correct : ∀ n, impl n = sha256Spec n := by
  intro n
  unfold impl sha256Spec iterSha
  exact congrArg encodeDigest
    (iterV31_correct
      (sha256Steps n) (seedDigest (sha256Seed n))
      (valid_seedDigest (sha256Seed n)))

end Submission
'''

text = runtime + proof + scalar
p = OUT / "Submission_mulrotate_scalar_v32_proof.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
