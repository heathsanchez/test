from pathlib import Path
import json, shutil, subprocess

ROOT=Path.cwd(); SOURCE=(ROOT/'coldcert'/'project').resolve(); OUT=(ROOT/'vero_divcore_natmodeq_cancel_v16').resolve()
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(); P=OUT/'source'; shutil.copytree(SOURCE,P)
for c in P.rglob('.lake'):
    if c.is_dir(): shutil.rmtree(c)

probe=r'''
import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

open Galoistools
namespace VeroDivCoreNatModEqCancelV16

theorem revaux_append_zero_mod (p x : Nat) : ∀ xs : List Nat,
    Galoistools.refPolyEvalRevAux p x (xs ++ [0]) % p =
    Galoistools.refPolyEvalRevAux p x xs % p := by
  intro xs
  induction xs with
  | nil => simp [Galoistools.refPolyEvalRevAux]
  | cons a as ih => simp [Galoistools.refPolyEvalRevAux, ih, Nat.add_mod, Nat.mul_mod]

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
  | cons a as ih => simp [Galoistools.refPolyEvalRevAux, ih, Nat.add_mod, Nat.mul_mod]

theorem horner_add_mod (p x a b A B : Nat) :
    (((a + b) % p + x * ((A + B) % p)) % p) =
      (((a + x * A) % p + (b + x * B) % p) % p) := by
  calc
    (((a + b) % p + x * ((A + B) % p)) % p)
        = ((a + b) + x * (A + B)) % p := by simp [Nat.add_mod, Nat.mul_mod]
    _ = ((a + x * A) + (b + x * B)) % p := by
          simp [Nat.mul_add, Nat.add_assoc, Nat.add_comm, Nat.add_left_comm]
    _ = (((a + x * A) % p + (b + x * B) % p) % p) := by simp [Nat.add_mod]

theorem revaux_zipAddPad_mod (p x : Nat) : ∀ as bs : List Nat,
    Galoistools.refPolyEvalRevAux p x (Galoistools.zipAddPad p as bs) % p =
      (Galoistools.refPolyEvalRevAux p x as +
       Galoistools.refPolyEvalRevAux p x bs) % p := by
  intro as
  induction as with
  | nil =>
      intro bs
      simp [Galoistools.zipAddPad, Galoistools.refPolyEvalRevAux,
        revaux_map_mod, Nat.add_mod, Nat.mul_mod]
  | cons a as ih =>
      intro bs
      cases bs with
      | nil =>
          simp [Galoistools.zipAddPad, Galoistools.refPolyEvalRevAux,
            revaux_map_mod, Nat.add_mod, Nat.mul_mod]
      | cons b bs =>
          simp only [Galoistools.zipAddPad, Galoistools.refPolyEvalRevAux]
          calc
            (((a + b) % p + x * Galoistools.refPolyEvalRevAux p x
                (Galoistools.zipAddPad p as bs)) % p) % p
                = (((a + b) % p + x *
                    (Galoistools.refPolyEvalRevAux p x
                      (Galoistools.zipAddPad p as bs) % p)) % p) := by
                    simp [Nat.add_mod, Nat.mul_mod]
            _ = (((a + b) % p + x *
                    ((Galoistools.refPolyEvalRevAux p x as +
                      Galoistools.refPolyEvalRevAux p x bs) % p)) % p) := by
                    rw [ih bs]
            _ = (((a + x * Galoistools.refPolyEvalRevAux p x as) % p +
                    (b + x * Galoistools.refPolyEvalRevAux p x bs) % p) % p) := by
                    exact horner_add_mod p x a b
                      (Galoistools.refPolyEvalRevAux p x as)
                      (Galoistools.refPolyEvalRevAux p x bs)

theorem gfAdd_eval_mod (p x : Nat) (f g : List Nat) :
    NatModEq p
      (Galoistools.refPolyEval p (Galoistools.gfAdd f g p) x)
      (Galoistools.refPolyEval p f x + Galoistools.refPolyEval p g x) := by
  unfold Galoistools.gfAdd
  have hs := strip_eval_mod p x
    (Galoistools.zipAddPad p f.reverse g.reverse).reverse
  unfold NatModEq Galoistools.refPolyEval at hs ⊢
  simp only [List.reverse_reverse] at hs ⊢
  calc
    Galoistools.refPolyEvalRevAux p x
        (Galoistools.gfStrip
          (Galoistools.zipAddPad p f.reverse g.reverse).reverse).reverse % p
      = Galoistools.refPolyEvalRevAux p x
          (Galoistools.zipAddPad p f.reverse g.reverse) % p := hs
    _ = (Galoistools.refPolyEvalRevAux p x f.reverse +
          Galoistools.refPolyEvalRevAux p x g.reverse) % p :=
          revaux_zipAddPad_mod p x f.reverse g.reverse

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
    _ = a % p := by simp

theorem revaux_neg_add_zero_mod (p x : Nat) (hp : 0 < p) : ∀ bs : List Nat,
    Galoistools.refPolyEvalRevAux p x
      (Galoistools.zipAddPad p
        (bs.map (fun y => (p - y % p) % p)) bs) % p = 0 := by
  intro bs
  induction bs with
  | nil => simp [Galoistools.zipAddPad, Galoistools.refPolyEvalRevAux]
  | cons b bs ih =>
      simp only [List.map_cons, Galoistools.zipAddPad, Galoistools.refPolyEvalRevAux]
      rw [show (((p - b % p) % p + b) % p) = 0 by
        simpa using sub_add_coeff_mod p 0 b hp]
      simp [ih, Nat.add_mod, Nat.mul_mod]

theorem revaux_sub_add_cancel_mod (p x : Nat) (hp : 0 < p) : ∀ as bs : List Nat,
    Galoistools.refPolyEvalRevAux p x
      (Galoistools.zipAddPad p (Galoistools.zipSubPad p as bs) bs) % p =
    Galoistools.refPolyEvalRevAux p x as % p := by
  intro as
  induction as with
  | nil =>
      intro bs
      simp [Galoistools.zipSubPad, revaux_neg_add_zero_mod p x hp,
        Galoistools.refPolyEvalRevAux]
  | cons a as ih =>
      intro bs
      cases bs with
      | nil =>
          simp only [Galoistools.zipSubPad, Galoistools.zipAddPad,
            Galoistools.refPolyEvalRevAux, List.map_cons]
          simp only [List.map_map, Function.comp_def, Nat.mod_mod]
          have htail := revaux_map_mod p x as
          have hcore :
              ((a % p + x * Galoistools.refPolyEvalRevAux p x
                (as.map (fun z => z % p))) % p) =
              ((a + x * Galoistools.refPolyEvalRevAux p x as) % p) := by
            calc
              ((a % p + x * Galoistools.refPolyEvalRevAux p x
                  (as.map (fun z => z % p))) % p)
                  = ((a % p + x *
                      (Galoistools.refPolyEvalRevAux p x
                        (as.map (fun z => z % p)) % p)) % p) := by
                      simp [Nat.add_mod, Nat.mul_mod]
              _ = ((a % p + x *
                      (Galoistools.refPolyEvalRevAux p x as % p)) % p) := by rw [htail]
              _ = (a + x * Galoistools.refPolyEvalRevAux p x as) % p := by
                      simp [Nat.add_mod, Nat.mul_mod]
          simpa [Nat.mod_mod] using hcore
      | cons b bs =>
          simp only [Galoistools.zipSubPad, Galoistools.zipAddPad,
            Galoistools.refPolyEvalRevAux]
          rw [sub_add_coeff_mod p a b hp]
          have htail := ih bs
          have hcore :
              ((a % p + x * Galoistools.refPolyEvalRevAux p x
                (Galoistools.zipAddPad p
                  (Galoistools.zipSubPad p as bs) bs)) % p) =
              ((a + x * Galoistools.refPolyEvalRevAux p x as) % p) := by
            calc
              ((a % p + x * Galoistools.refPolyEvalRevAux p x
                  (Galoistools.zipAddPad p
                    (Galoistools.zipSubPad p as bs) bs)) % p)
                  = ((a % p + x *
                      (Galoistools.refPolyEvalRevAux p x
                        (Galoistools.zipAddPad p
                          (Galoistools.zipSubPad p as bs) bs) % p)) % p) := by
                      simp [Nat.add_mod, Nat.mul_mod]
              _ = ((a % p + x *
                      (Galoistools.refPolyEvalRevAux p x as % p)) % p) := by rw [htail]
              _ = (a + x * Galoistools.refPolyEvalRevAux p x as) % p := by
                      simp [Nat.add_mod, Nat.mul_mod]
          simpa [Nat.mod_mod] using hcore

theorem gfSub_add_eval_mod (p x : Nat) (cur sub : List Nat) (hp : 0 < p) :
    (Galoistools.refPolyEval p (Galoistools.gfSub cur sub p) x +
      Galoistools.refPolyEval p sub x) % p =
    Galoistools.refPolyEval p cur x % p := by
  have hs := strip_eval_mod p x
    (Galoistools.zipSubPad p cur.reverse sub.reverse).reverse
  unfold NatModEq Galoistools.refPolyEval at hs ⊢
  simp only [List.reverse_reverse] at hs ⊢
  unfold Galoistools.gfSub
  simp only [List.reverse_reverse]
  calc
    (Galoistools.refPolyEvalRevAux p x
        (Galoistools.gfStrip
          (Galoistools.zipSubPad p cur.reverse sub.reverse).reverse).reverse +
      Galoistools.refPolyEvalRevAux p x sub.reverse) % p
      = (Galoistools.refPolyEvalRevAux p x
          (Galoistools.zipSubPad p cur.reverse sub.reverse) +
        Galoistools.refPolyEvalRevAux p x sub.reverse) % p := by
          rw [show Galoistools.refPolyEvalRevAux p x
              (Galoistools.gfStrip
                (Galoistools.zipSubPad p cur.reverse sub.reverse).reverse).reverse % p =
              Galoistools.refPolyEvalRevAux p x
                (Galoistools.zipSubPad p cur.reverse sub.reverse) % p from hs]
          simp [Nat.add_mod]
    _ = Galoistools.refPolyEvalRevAux p x
          (Galoistools.zipAddPad p
            (Galoistools.zipSubPad p cur.reverse sub.reverse) sub.reverse) % p := by
          exact (revaux_zipAddPad_mod p x
            (Galoistools.zipSubPad p cur.reverse sub.reverse) sub.reverse).symm
    _ = Galoistools.refPolyEvalRevAux p x cur.reverse % p :=
          revaux_sub_add_cancel_mod p x hp cur.reverse sub.reverse

theorem divcore_natmodeq_cancel (p x : Nat) (cur sub : List Nat)
    (hp : 1 < p) :
    NatModEq p
      (Galoistools.refPolyEval p
        (Galoistools.gfAdd (Galoistools.gfSub cur sub p) sub p) x)
      (Galoistools.refPolyEval p cur x) := by
  have hadd := gfAdd_eval_mod p x (Galoistools.gfSub cur sub p) sub
  have hcancel := gfSub_add_eval_mod p x cur sub (Nat.zero_lt_of_lt hp)
  unfold NatModEq at hadd ⊢
  calc
    Galoistools.refPolyEval p
        (Galoistools.gfAdd (Galoistools.gfSub cur sub p) sub p) x % p
      = (Galoistools.refPolyEval p (Galoistools.gfSub cur sub p) x +
          Galoistools.refPolyEval p sub x) % p := hadd
    _ = Galoistools.refPolyEval p cur x % p := hcancel

end VeroDivCoreNatModEqCancelV16
'''
(P/'DivCoreNatModEqCancelV16.lean').write_text(probe)
build=subprocess.run(['lake','build','Galoistools.Proof.Ring','Galoistools.Impl.Division','Galoistools.Spec.Division'],cwd=P,text=True,capture_output=True,timeout=300)
if build.returncode:
    raw=build.stdout+'\n'+build.stderr
    print('V16_DIVCORE_NATMODEQ_GATE',json.dumps({'stage':'build','exit':build.returncode,'tail':raw[-12000:]})); raise SystemExit(1)
cp=subprocess.run(['lake','env','lean','DivCoreNatModEqCancelV16.lean'],cwd=P,text=True,capture_output=True,timeout=300)
raw=cp.stdout+'\n'+cp.stderr
print('V16_DIVCORE_NATMODEQ_GATE',json.dumps({'stage':'lemma','exit':cp.returncode,'tail':raw[-20000:]}))
(OUT/'result.json').write_text(json.dumps({'exit':cp.returncode,'raw':raw},indent=2))
raise SystemExit(cp.returncode)
