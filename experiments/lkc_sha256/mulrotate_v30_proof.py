#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

# Exact V30 runtime.
runpy.run_path(str(ROOT/"mulrotate_v30_probe.py"))
runtime=(OUT/"Submission_mulrotate_v30_probe.lean").read_text()
runtime=runtime.replace("def implMulRotate (n : Nat) : Nat :=", "def impl (n : Nat) : Nat :=", 1)
prefix=runtime.rsplit("\nend Submission",1)[0] + "\n\n"

# Reuse the already-qualified V25 proof bank around the new sigma implementation.
runpy.run_path(str(ROOT/"algebra_v25_interaction.py"))
v25=(OUT/"Submission_algebra_v25_interaction.lean").read_text()
proof=v25[v25.index("theorem w32_eq"):v25.rindex("\nend Submission")]

# Keep the common modular infrastructure, replace only the sigma-specific block.
start=proof.index("theorem bigSigma0Fast_mod_eq")
end=proof.index("theorem majFast_eq")

custom=r'''
theorem dup32_eq_or (x : Nat) (hx : x < 2^32) :
    dup32 x = (x <<< 32) ||| x := by
  have hnum : 4294967297 = 2^32 + 1 := by decide
  calc
    x * 4294967297 = 2^32 * x + x := by
      rw [hnum, Nat.mul_add, Nat.mul_one, Nat.mul_comm x (2^32)]
    _ = (x <<< 32) ||| x := by
      rw [Nat.shiftLeft_eq, Nat.mul_comm x (2^32)]
      exact Nat.two_pow_add_eq_or_of_lt hx x
'''

for n in [2,6,7,11,13,17,18,19,22,25]:
    m=32-n
    custom+=f'''
theorem shift32_{n} (x : Nat) :
    (x <<< 32) >>> {n} = x <<< {m} := by
  rw [Nat.shiftLeft_eq, Nat.shiftRight_eq_div_pow, Nat.shiftLeft_eq]
  have hp : 2^32 = 2^{n} * 2^{m} := by decide
  rw [hp, ← Nat.mul_assoc, Nat.mul_comm x (2^{n}), Nat.mul_assoc]
  exact Nat.mul_div_cancel_left (x * 2^{m}) (by decide : 0 < 2^{n})

theorem dup32_shift{n} (x : Nat) (hx : x < 2^32) :
    dup32 x >>> {n} = (x >>> {n}) ||| (x <<< {m}) := by
  rw [dup32_eq_or x hx, Nat.shiftRight_or_distrib, shift32_{n}]
  rw [Nat.or_comm]

theorem dup32_rotr{n} (x : Nat) (hx : x < 2^32) :
    (dup32 x >>> {n}) &&& w32 = rotr32 x {n} := by
  rw [dup32_shift{n} x hx]
  rfl
'''

custom+=r'''
theorem bigSigma0Fast_mod_eq (x : Nat) (hx : x < 2^32) :
    bigSigma0Fast x % 2^32 = bigSigma0 x := by
  rw [← mask32_eq_mod]
  unfold bigSigma0Fast bigSigma0
  dsimp only
  rw [Nat.and_xor_distrib_right, Nat.and_xor_distrib_right]
  rw [dup32_rotr2 x hx, dup32_rotr13 x hx, dup32_rotr22 x hx]

theorem bigSigma1Fast_mod_eq (x : Nat) (hx : x < 2^32) :
    bigSigma1Fast x % 2^32 = bigSigma1 x := by
  rw [← mask32_eq_mod]
  unfold bigSigma1Fast bigSigma1
  dsimp only
  rw [Nat.and_xor_distrib_right, Nat.and_xor_distrib_right]
  rw [dup32_rotr6 x hx, dup32_rotr11 x hx, dup32_rotr25 x hx]

theorem smallSigma0Fast_mod_eq (x : Nat) (hx : x < 2^32) :
    smallSigma0Fast x % 2^32 = smallSigma0 x := by
  rw [← mask32_eq_mod]
  unfold smallSigma0Fast smallSigma0
  dsimp only
  rw [Nat.and_xor_distrib_right, Nat.and_xor_distrib_right]
  rw [dup32_rotr7 x hx, dup32_rotr18 x hx]
  have hs : x >>> 3 < 2^32 :=
    Nat.lt_of_le_of_lt (Nat.shiftRight_le x 3) hx
  rw [and_mask32_eq_self (x >>> 3) hs]

theorem smallSigma1Fast_mod_eq (x : Nat) (hx : x < 2^32) :
    smallSigma1Fast x % 2^32 = smallSigma1 x := by
  rw [← mask32_eq_mod]
  unfold smallSigma1Fast smallSigma1
  dsimp only
  rw [Nat.and_xor_distrib_right, Nat.and_xor_distrib_right]
  rw [dup32_rotr17 x hx, dup32_rotr19 x hx]
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

proof=proof[:start]+custom+proof[end:]
proof=proof.replace("theorem t2_mod32 (s : Digest) :", "theorem t2_mod32 (s : Digest) (hs : ValidDigest s) :")
proof=proof.replace("(t2_mod32 s))", "(t2_mod32 s hs))")
proof=proof.replace("bigSigma1Fast_mod32 s.e)", "bigSigma1Fast_mod32 s.e hs.e)")
proof=proof.replace("bigSigma0Fast_mod32 s.a)", "bigSigma0Fast_mod32 s.a hs.a)")

# Replace V25's recursive rounds proof with a small certified one-step bridge.
rs0=proof.index("theorem roundsFast_eq_slow")
rs1=proof.index("def generate", rs0)
rounds_bridge=r'''theorem roundsFast_cons_bridge
    (k : Nat) (ks : List Nat) (win : Window) (s : Digest)
    (hs : ValidDigest s) (hw : ValidWindow win) :
    roundsFast (k :: ks) win s =
      roundsFast ks win.advance (round s k win.x0) := by
  simp only [roundsFast]
  rw [Window.nextFast_eq_nextWord win hw]
  rw [roundFast_eq_round s k win.x0 hs]
  rfl

theorem roundsFast_eq_slow
    (ks : List Nat) : ∀ win s, ValidDigest s → ValidWindow win →
      roundsFast ks win s = roundsSlow ks win s := by
  induction ks with
  | nil =>
      intro win s hs hw
      rfl
  | cons k ks ih =>
      intro win s hs hw
      calc
        roundsFast (k :: ks) win s =
            roundsFast ks win.advance (round s k win.x0) :=
          roundsFast_cons_bridge k ks win s hs hw
        _ = roundsSlow ks win.advance (round s k win.x0) :=
          ih win.advance (round s k win.x0)
            (valid_round s k win.x0 hs) (valid_advance win hw)
        _ = roundsSlow (k :: ks) win s := by rfl

'''
proof=proof[:rs0]+rounds_bridge+proof[rs1:]

text=prefix+proof+"\nend Submission\n"
p=OUT/"Submission_mulrotate_v30_proof.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
