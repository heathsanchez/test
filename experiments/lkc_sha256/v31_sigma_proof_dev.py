#!/usr/bin/env python3
# rerun after alpha-only base binder cleanup
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"mulrotate_scalar_v31_probe.py"))
src=(OUT/"Submission_mulrotate_scalar_v31_probe.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0] + "\n\n"

rots=[2,6,7,11,13,17,18,19,22,25]
pieces=[r'''
/-! V31 proof-only interaction shadow: fixed-width rotate certificate. -/

theorem w32_eq_v31 : w32 = 2^32 - 1 := by decide

theorem mask32_eq_mod_v31 (x : Nat) :
    x &&& w32 = x % 2^32 := by
  rw [w32_eq_v31, Nat.and_two_pow_sub_one_eq_mod]

theorem and_mask32_eq_self_v31 (x : Nat) (hx : x < 2^32) :
    x &&& w32 = x := by
  rw [w32_eq_v31]
  exact Nat.and_two_pow_sub_one_of_lt_two_pow hx

theorem dup32_eq_or_v31 (x : Nat) (hx : x < 2^32) :
    dup32 x = (x <<< 32) ||| x := by
  have hnum : 4294967297 = 2^32 + 1 := by decide
  calc
    x * 4294967297 = 2^32 * x + x := by
      rw [hnum, Nat.mul_add, Nat.mul_one, Nat.mul_comm x (2^32)]
    _ = (x <<< 32) ||| x := by
      rw [Nat.shiftLeft_eq, Nat.mul_comm x (2^32)]
      exact Nat.two_pow_add_eq_or_of_lt hx x
''']

for n in rots:
    m=32-n
    pieces.append(f'''
theorem shift32_{n}_v31 (x : Nat) :
    (x <<< 32) >>> {n} = x <<< {m} := by
  rw [Nat.shiftLeft_eq, Nat.shiftRight_eq_div_pow, Nat.shiftLeft_eq]
  have hp : 2^32 = 2^{n} * 2^{m} := by decide
  rw [hp, ← Nat.mul_assoc, Nat.mul_comm x (2^{n}), Nat.mul_assoc]
  exact Nat.mul_div_cancel_left (x * 2^{m}) (by decide : 0 < 2^{n})

theorem dup32_shift{n}_v31 (x : Nat) (hx : x < 2^32) :
    dup32 x >>> {n} = (x >>> {n}) ||| (x <<< {m}) := by
  rw [dup32_eq_or_v31 x hx, Nat.shiftRight_or_distrib, shift32_{n}_v31]
  rw [Nat.or_comm]

theorem dup32_rotr{n}_v31 (x : Nat) (hx : x < 2^32) :
    (dup32 x >>> {n}) &&& w32 = rotr32 x {n} := by
  rw [dup32_shift{n}_v31 x hx]
  rfl
''')

pieces.append(r'''
theorem bigSigma0Fast_mod_eq_v31 (x : Nat) (hx : x < 2^32) :
    bigSigma0Fast x % 2^32 = bigSigma0 x := by
  rw [← mask32_eq_mod_v31]
  unfold bigSigma0Fast bigSigma0
  dsimp only
  rw [Nat.and_xor_distrib_right, Nat.and_xor_distrib_right]
  rw [dup32_rotr2_v31 x hx, dup32_rotr13_v31 x hx, dup32_rotr22_v31 x hx]

theorem bigSigma1Fast_mod_eq_v31 (x : Nat) (hx : x < 2^32) :
    bigSigma1Fast x % 2^32 = bigSigma1 x := by
  rw [← mask32_eq_mod_v31]
  unfold bigSigma1Fast bigSigma1
  dsimp only
  rw [Nat.and_xor_distrib_right, Nat.and_xor_distrib_right]
  rw [dup32_rotr6_v31 x hx, dup32_rotr11_v31 x hx, dup32_rotr25_v31 x hx]

theorem smallSigma0Fast_mod_eq_v31 (x : Nat) (hx : x < 2^32) :
    smallSigma0Fast x % 2^32 = smallSigma0 x := by
  rw [← mask32_eq_mod_v31]
  unfold smallSigma0Fast smallSigma0
  dsimp only
  rw [Nat.and_xor_distrib_right, Nat.and_xor_distrib_right]
  rw [dup32_rotr7_v31 x hx, dup32_rotr18_v31 x hx]
  have hs : x >>> 3 < 2^32 :=
    Nat.lt_of_le_of_lt (Nat.shiftRight_le x 3) hx
  rw [and_mask32_eq_self_v31 (x >>> 3) hs]

theorem smallSigma1Fast_mod_eq_v31 (x : Nat) (hx : x < 2^32) :
    smallSigma1Fast x % 2^32 = smallSigma1 x := by
  rw [← mask32_eq_mod_v31]
  unfold smallSigma1Fast smallSigma1
  dsimp only
  rw [Nat.and_xor_distrib_right, Nat.and_xor_distrib_right]
  rw [dup32_rotr17_v31 x hx, dup32_rotr19_v31 x hx]
  have hs : x >>> 10 < 2^32 :=
    Nat.lt_of_le_of_lt (Nat.shiftRight_le x 10) hx
  rw [and_mask32_eq_self_v31 (x >>> 10) hs]

end Submission
''')

text=prefix+"".join(pieces)
p=OUT/"V31SigmaProofDev.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
