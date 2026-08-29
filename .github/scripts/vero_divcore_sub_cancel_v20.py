from pathlib import Path
import json, shutil, subprocess

ROOT=Path.cwd(); SOURCE=(ROOT/'coldcert'/'project').resolve(); OUT=(ROOT/'vero_divcore_sub_cancel_v20').resolve()
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(); P=OUT/'source'; shutil.copytree(SOURCE,P)
for c in P.rglob('.lake'):
    if c.is_dir(): shutil.rmtree(c)

probe=r'''
import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

open Galoistools
namespace VeroDivCoreSubCancelV20

theorem revaux_append_zero_mod (p x : Nat) : ∀ xs : List Nat,
    Galoistools.refPolyEvalRevAux p x (xs ++ [0]) % p =
    Galoistools.refPolyEvalRevAux p x xs % p := by
  intro xs
  induction xs with
  | nil => simp [Galoistools.refPolyEvalRevAux]
  | cons a as ih =>
      simp [Galoistools.refPolyEvalRevAux, ih, Nat.add_mod, Nat.mul_mod]

theorem gfStrip_cons_zero (as : List Nat) :
    Galoistools.gfStrip (0 :: as) = Galoistools.gfStrip as := by
  simp [Galoistools.gfStrip]

theorem strip_eval_mod (p x : Nat) (f : List Nat) :
    NatModEq p
      (Galoistools.refPolyEval p (Galoistools.gfStrip f) x)
      (Galoistools.refPolyEval p f x) := by
  unfold NatModEq Galoistools.refPolyEval
  induction f with
  | nil => simp [Galoistools.gfStrip, Galoistools.refPolyEvalRevAux]
  | cons a as ih =>
      by_cases h : a = 0
      · subst a
        rw [gfStrip_cons_zero]
        simp only [List.reverse_cons]
        rw [ih]
        exact (revaux_append_zero_mod p x as.reverse).symm
      · simp [Galoistools.gfStrip, h]

theorem revaux_map_mod (p x : Nat) : ∀ xs : List Nat,
    Galoistools.refPolyEvalRevAux p x (xs.map (fun a => a % p)) % p =
    Galoistools.refPolyEvalRevAux p x xs % p := by
  intro xs
  induction xs with
  | nil => simp [Galoistools.refPolyEvalRevAux]
  | cons a as ih =>
      simp [Galoistools.refPolyEvalRevAux, ih, Nat.add_mod, Nat.mul_mod]

theorem sub_add_coeff_mod (p a b : Nat) (hp : 0 < p) :
    ((((a + (p - b % p)) % p) % p + b) % p) = a % p := by
  have hb : b % p ≤ p := Nat.le_of_lt (Nat.mod_lt b hp)
  have hcancel : (p - b % p) + b % p = p := Nat.sub_add_cancel hb
  calc
    ((((a + (p - b % p)) % p) % p + b) % p)
        = ((a + (p - b % p)) + b) % p := by simp [Nat.add_mod]
    _ = ((a + (p - b % p)) + b % p) % p := by simp [Nat.add_mod]
    _ = (a + ((p - b % p) + b % p)) % p := by rw [Nat.add_assoc]
    _ = (a + p) % p := by rw [hcancel]
    _ = a % p := by simp [Nat.add_mod]

-- Exact normalized coefficient shape emitted by zipSubPad followed by zipAddPad.
theorem sub_add_coeff_mod_norm (p a b : Nat) (hp : 0 < p) :
    (((a % p + (p - b % p) % p) % p + b % p) % p) = a % p := by
  calc
    (((a % p + (p - b % p) % p) % p + b % p) % p)
        = (((a + (p - b % p)) % p + b) % p) := by
            simp [Nat.add_mod]
    _ = a % p := by
            simpa [Nat.mod_mod] using sub_add_coeff_mod p a b hp

-- Strong interface needed by V16: subtracting then adding back preserves Horner evaluation.
theorem revaux_sub_add_cancel_mod (p x : Nat) (hp : 0 < p) : ∀ as bs : List Nat,
    Galoistools.refPolyEvalRevAux p x
      (Galoistools.zipAddPad p (Galoistools.zipSubPad p as bs) bs) % p =
    Galoistools.refPolyEvalRevAux p x as % p := by
  intro as
  induction as with
  | nil =>
      intro bs
      induction bs with
      | nil => simp [Galoistools.zipSubPad, Galoistools.zipAddPad, Galoistools.refPolyEvalRevAux]
      | cons b bs ih =>
          simp only [Galoistools.zipSubPad, Galoistools.zipAddPad,
            Galoistools.refPolyEvalRevAux, List.map_cons]
          calc
            ((((p - b % p) % p + b) % p +
                x * Galoistools.refPolyEvalRevAux p x
                  (Galoistools.zipAddPad p
                    (bs.map (fun y => (p - y % p) % p)) bs)) % p) % p)
                = ((0 + x * 0) % p) := by
                    rw [show ((p - b % p) % p + b) % p = 0 by
                      simpa using sub_add_coeff_mod_norm p 0 b hp]
                    have htail :
                        Galoistools.refPolyEvalRevAux p x
                          (Galoistools.zipAddPad p
                            (Galoistools.zipSubPad p [] bs) bs) % p = 0 := by
                      simpa [Galoistools.refPolyEvalRevAux] using ih
                    simpa [Galoistools.zipSubPad, Nat.add_mod, Nat.mul_mod] using htail
            _ = Galoistools.refPolyEvalRevAux p x [] % p := by
                    simp [Galoistools.refPolyEvalRevAux]
  | cons a as ih =>
      intro bs
      cases bs with
      | nil =>
          simp only [Galoistools.zipSubPad, Galoistools.zipAddPad,
            Galoistools.refPolyEvalRevAux, List.map_cons]
          have hm := revaux_map_mod p x as
          simpa [List.map_map, Function.comp_def, Nat.mod_mod,
            Nat.add_mod, Nat.mul_mod] using hm
      | cons b bs =>
          simp only [Galoistools.zipSubPad, Galoistools.zipAddPad,
            Galoistools.refPolyEvalRevAux]
          have htail := ih bs
          calc
            (((((a + (p - b % p)) % p) % p + b) % p +
                x * Galoistools.refPolyEvalRevAux p x
                  (Galoistools.zipAddPad p
                    (Galoistools.zipSubPad p as bs) bs)) % p) % p)
                = ((a % p + x *
                    (Galoistools.refPolyEvalRevAux p x
                      (Galoistools.zipAddPad p
                        (Galoistools.zipSubPad p as bs) bs) % p)) % p) := by
                    rw [sub_add_coeff_mod p a b hp]
                    simp [Nat.add_mod, Nat.mul_mod]
            _ = ((a % p + x *
                    (Galoistools.refPolyEvalRevAux p x as % p)) % p) := by
                    rw [htail]
            _ = (a + x * Galoistools.refPolyEvalRevAux p x as) % p := by
                    simp [Nat.add_mod, Nat.mul_mod]

end VeroDivCoreSubCancelV20
'''
(P/'DivCoreSubCancelV20.lean').write_text(probe)
build=subprocess.run(['lake','build','Galoistools.Proof.Ring','Galoistools.Impl.Division','Galoistools.Spec.Division'],cwd=P,text=True,capture_output=True,timeout=300)
if build.returncode:
    raw=build.stdout+'\n'+build.stderr
    print('V20_SUB_CANCEL_GATE',json.dumps({'stage':'build','exit':build.returncode,'tail':raw[-12000:]})); raise SystemExit(1)
cp=subprocess.run(['lake','env','lean','DivCoreSubCancelV20.lean'],cwd=P,text=True,capture_output=True,timeout=300)
raw=cp.stdout+'\n'+cp.stderr
print('V20_SUB_CANCEL_GATE',json.dumps({'stage':'lemma','exit':cp.returncode,'tail':raw[-20000:]}))
(OUT/'result.json').write_text(json.dumps({'exit':cp.returncode,'raw':raw},indent=2))
raise SystemExit(cp.returncode)
