from pathlib import Path
import json, shutil, subprocess, re

ROOT=Path.cwd(); SOURCE=(ROOT/'coldcert'/'project').resolve(); OUT=(ROOT/'vero_divcore_natmodeq_cancel_v16').resolve()
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(); P=OUT/'source'; shutil.copytree(SOURCE,P)
for c in P.rglob('.lake'):
    if c.is_dir(): shutil.rmtree(c)

def probe_from(path):
    s=path.read_text()
    m=re.search(r"probe=r'''(.*?)'''\n\(P/", s, re.S)
    if not m: raise RuntimeError(f'probe not found: {path}')
    return m.group(1)

v19=probe_from(ROOT/'.github/scripts/vero_divcore_add_semantics_v19.py')
v20=probe_from(ROOT/'.github/scripts/vero_divcore_sub_cancel_v20.py')
base=v19[:v19.rfind('end VeroDivCoreAddSemanticsV19')]
sub=v20[v20.index('theorem sub_add_coeff_mod'):v20.rfind('end VeroDivCoreSubCancelV20')]
extra=r'''

theorem gfSub_add_eval_mod (p x : Nat) (cur sub : List Nat) (hp : 0 < p) :
    (Galoistools.refPolyEval p (Galoistools.gfSub cur sub p) x +
      Galoistools.refPolyEval p sub x) % p =
    Galoistools.refPolyEval p cur x % p := by
  have hs := strip_eval_mod p x
    (Galoistools.zipSubPad p cur.reverse sub.reverse).reverse
  unfold NatModEq Galoistools.refPolyEval at hs
  unfold Galoistools.refPolyEval
  simp only [List.reverse_reverse] at hs ⊢
  unfold Galoistools.gfSub
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

end VeroDivCoreAddSemanticsV19
'''
probe=base+sub+extra
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
