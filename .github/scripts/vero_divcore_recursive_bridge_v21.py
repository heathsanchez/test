from pathlib import Path
import json, shutil, subprocess

ROOT=Path.cwd(); SOURCE=(ROOT/'coldcert'/'project').resolve(); OUT=(ROOT/'vero_divcore_recursive_bridge_v21').resolve()
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(); P=OUT/'source'; shutil.copytree(SOURCE,P)
for c in P.rglob('.lake'):
    if c.is_dir(): shutil.rmtree(c)

probe=r'''
import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

open Galoistools
namespace VeroDivCoreRecursiveBridgeV21

@[simp] theorem mul_eval_hom (p x : Nat) (u v : List Nat) :
    Galoistools.refPolyEval p (Galoistools.gfMul u v p) x =
      (Galoistools.refPolyEval p u x * Galoistools.refPolyEval p v x) % p := by
  simp only [Galoistools.gfMul]
  by_cases hzero : u = [] ∨ v = []
  · rw [if_pos hzero]
    rcases hzero with rfl | rfl <;>
      simp [Galoistools.refPolyEval, Galoistools.refPolyEvalRevAux]
  · rw [if_neg hzero, refPolyEval_gfStrip]
    simp only [Galoistools.refPolyEval, List.reverse_reverse]
    have hconv := natModEq_refPolyEvalRevAux_convolve p x u.reverse v.reverse
    unfold NatModEq at hconv
    have hevalmod :
        Galoistools.refPolyEvalRevAux p x
          (Galoistools.convolve p u.reverse v.reverse) % p =
        Galoistools.refPolyEvalRevAux p x
          (Galoistools.convolve p u.reverse v.reverse) := by
      cases Galoistools.convolve p u.reverse v.reverse <;>
        simp [Galoistools.refPolyEvalRevAux]
    calc
      Galoistools.refPolyEvalRevAux p x
          (Galoistools.convolve p u.reverse v.reverse) =
        Galoistools.refPolyEvalRevAux p x
          (Galoistools.convolve p u.reverse v.reverse) % p := hevalmod.symm
      _ = (Galoistools.refPolyEvalRevAux p x u.reverse *
            Galoistools.refPolyEvalRevAux p x v.reverse) % p := hconv

theorem quotient_sub_bridge (p x c s : Nat) (g : List Nat) :
    NatModEq p
      (Galoistools.refPolyEval p
        (Galoistools.gfMul (Galoistools.shiftUp s [c]) g p) x)
      (Galoistools.refPolyEval p
        (Galoistools.shiftUp s (Galoistools.scaleP p c g)) x) := by
  unfold NatModEq
  rw [mul_eval_hom]
  simp [Galoistools.shiftUp, Galoistools.scaleP,
    Galoistools.refPolyEval, Galoistools.refPolyEvalRevAux,
    Nat.add_mod, Nat.mul_mod]

end VeroDivCoreRecursiveBridgeV21
'''
(P/'DivCoreRecursiveBridgeV21.lean').write_text(probe)
build=subprocess.run(['lake','build','Galoistools.Proof.Ring','Galoistools.Impl.Division','Galoistools.Spec.Division'],cwd=P,text=True,capture_output=True,timeout=300)
if build.returncode:
    raw=build.stdout+'\n'+build.stderr
    print('V21_RECURSIVE_BRIDGE_GATE',json.dumps({'stage':'build','exit':build.returncode,'tail':raw[-12000:]})); raise SystemExit(1)
cp=subprocess.run(['lake','env','lean','DivCoreRecursiveBridgeV21.lean'],cwd=P,text=True,capture_output=True,timeout=300)
raw=cp.stdout+'\n'+cp.stderr
print('V21_RECURSIVE_BRIDGE_GATE',json.dumps({'stage':'lemma','exit':cp.returncode,'tail':raw[-20000:]}))
(OUT/'result.json').write_text(json.dumps({'exit':cp.returncode,'raw':raw},indent=2))
raise SystemExit(cp.returncode)
