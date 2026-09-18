#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"base32_machine_v12.py"))
src=(OUT/"Submission_machine_v12.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0] + "\n\n"

proof=r'''
/- Generic base-2^32 codec lemmas. -/

theorem mod_consB (a rest : Nat) (ha : a < base32) :
    (a + base32 * rest) % base32 = a := by
  simp [Nat.add_mul_mod_self_left, Nat.mod_eq_of_lt ha]

theorem div_consB (a rest : Nat) (ha : a < base32) :
    (a + base32 * rest) / base32 = rest := by
  rw [Nat.add_mul_div_left a rest (by decide)]
  rw [Nat.div_eq_of_lt ha, Nat.zero_add]

def laneRec : Nat → Nat → Nat
  | 0, x => x % base32
  | i + 1, x => laneRec i (x / base32)

theorem laneRec_eq_laneB (x : Nat) : ∀ i, laneRec i x = laneB x i
  | 0 => by
      simp [laneRec, laneB]
  | i + 1 => by
      simp only [laneRec]
      rw [laneRec_eq_laneB (x / base32) i]
      unfold laneB
      rw [Nat.div_div_eq_div_mul]
      rw [Nat.pow_succ]
      simp [Nat.mul_comm]

def packWords : List Nat → Nat
  | [] => 0
  | x :: xs => x + base32 * packWords xs

def AllWord32 (xs : List Nat) : Prop :=
  ∀ x, x ∈ xs → x < base32

theorem laneRec_packWords :
    ∀ i xs, AllWord32 xs →
      laneRec i (packWords xs) = xs.getD i 0
  | _, [], _ => by
      simp [laneRec, packWords]
  | 0, x :: xs, hall => by
      have hx : x < base32 := hall x (by simp)
      simp [laneRec, packWords, mod_consB x (packWords xs) hx]
  | i + 1, x :: xs, hall => by
      have hx : x < base32 := hall x (by simp)
      have htail : AllWord32 xs := by
        intro y hy
        exact hall y (by simp [hy])
      simp only [laneRec, packWords]
      rw [div_consB x (packWords xs) hx]
      simpa using laneRec_packWords i xs htail

theorem laneB_packWords (i : Nat) (xs : List Nat) (hall : AllWord32 xs) :
    laneB (packWords xs) i = xs.getD i 0 := by
  rw [← laneRec_eq_laneB (packWords xs) i]
  exact laneRec_packWords i xs hall

theorem pack8B_eq_packWords (a b c d e f g h : Nat) :
    pack8B a b c d e f g h = packWords [a,b,c,d,e,f,g,h] := by
  rfl

theorem laneB_pack8B_0 (a b c d e f g h : Nat)
    (ha : a < base32) (hb : b < base32) (hc : c < base32) (hd : d < base32)
    (he : e < base32) (hf : f < base32) (hg : g < base32) (hh : h < base32) :
    laneB (pack8B a b c d e f g h) 0 = a := by
  have hall : AllWord32 [a,b,c,d,e,f,g,h] := by
    simp [AllWord32, ha,hb,hc,hd,he,hf,hg,hh]
  rw [pack8B_eq_packWords]
  simpa using laneB_packWords 0 [a,b,c,d,e,f,g,h] hall

theorem laneB_pack8B_1 (a b c d e f g h : Nat)
    (ha : a < base32) (hb : b < base32) (hc : c < base32) (hd : d < base32)
    (he : e < base32) (hf : f < base32) (hg : g < base32) (hh : h < base32) :
    laneB (pack8B a b c d e f g h) 1 = b := by
  have hall : AllWord32 [a,b,c,d,e,f,g,h] := by
    simp [AllWord32, ha,hb,hc,hd,he,hf,hg,hh]
  rw [pack8B_eq_packWords]
  simpa using laneB_packWords 1 [a,b,c,d,e,f,g,h] hall

theorem laneB_pack8B_2 (a b c d e f g h : Nat)
    (ha : a < base32) (hb : b < base32) (hc : c < base32) (hd : d < base32)
    (he : e < base32) (hf : f < base32) (hg : g < base32) (hh : h < base32) :
    laneB (pack8B a b c d e f g h) 2 = c := by
  have hall : AllWord32 [a,b,c,d,e,f,g,h] := by
    simp [AllWord32, ha,hb,hc,hd,he,hf,hg,hh]
  rw [pack8B_eq_packWords]
  simpa using laneB_packWords 2 [a,b,c,d,e,f,g,h] hall

theorem laneB_pack8B_3 (a b c d e f g h : Nat)
    (ha : a < base32) (hb : b < base32) (hc : c < base32) (hd : d < base32)
    (he : e < base32) (hf : f < base32) (hg : g < base32) (hh : h < base32) :
    laneB (pack8B a b c d e f g h) 3 = d := by
  have hall : AllWord32 [a,b,c,d,e,f,g,h] := by
    simp [AllWord32, ha,hb,hc,hd,he,hf,hg,hh]
  rw [pack8B_eq_packWords]
  simpa using laneB_packWords 3 [a,b,c,d,e,f,g,h] hall

theorem laneB_pack8B_4 (a b c d e f g h : Nat)
    (ha : a < base32) (hb : b < base32) (hc : c < base32) (hd : d < base32)
    (he : e < base32) (hf : f < base32) (hg : g < base32) (hh : h < base32) :
    laneB (pack8B a b c d e f g h) 4 = e := by
  have hall : AllWord32 [a,b,c,d,e,f,g,h] := by
    simp [AllWord32, ha,hb,hc,hd,he,hf,hg,hh]
  rw [pack8B_eq_packWords]
  simpa using laneB_packWords 4 [a,b,c,d,e,f,g,h] hall

theorem laneB_pack8B_5 (a b c d e f g h : Nat)
    (ha : a < base32) (hb : b < base32) (hc : c < base32) (hd : d < base32)
    (he : e < base32) (hf : f < base32) (hg : g < base32) (hh : h < base32) :
    laneB (pack8B a b c d e f g h) 5 = f := by
  have hall : AllWord32 [a,b,c,d,e,f,g,h] := by
    simp [AllWord32, ha,hb,hc,hd,he,hf,hg,hh]
  rw [pack8B_eq_packWords]
  simpa using laneB_packWords 5 [a,b,c,d,e,f,g,h] hall

theorem laneB_pack8B_6 (a b c d e f g h : Nat)
    (ha : a < base32) (hb : b < base32) (hc : c < base32) (hd : d < base32)
    (he : e < base32) (hf : f < base32) (hg : g < base32) (hh : h < base32) :
    laneB (pack8B a b c d e f g h) 6 = g := by
  have hall : AllWord32 [a,b,c,d,e,f,g,h] := by
    simp [AllWord32, ha,hb,hc,hd,he,hf,hg,hh]
  rw [pack8B_eq_packWords]
  simpa using laneB_packWords 6 [a,b,c,d,e,f,g,h] hall

theorem laneB_pack8B_7 (a b c d e f g h : Nat)
    (ha : a < base32) (hb : b < base32) (hc : c < base32) (hd : d < base32)
    (he : e < base32) (hf : f < base32) (hg : g < base32) (hh : h < base32) :
    laneB (pack8B a b c d e f g h) 7 = h := by
  have hall : AllWord32 [a,b,c,d,e,f,g,h] := by
    simp [AllWord32, ha,hb,hc,hd,he,hf,hg,hh]
  rw [pack8B_eq_packWords]
  simpa using laneB_packWords 7 [a,b,c,d,e,f,g,h] hall

end Submission
'''

text=prefix+proof
p=OUT/"Base32_codec_v12.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
