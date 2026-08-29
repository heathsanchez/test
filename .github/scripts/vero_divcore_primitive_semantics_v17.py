from pathlib import Path
import json, shutil, subprocess

ROOT=Path.cwd(); SOURCE=(ROOT/'coldcert'/'project').resolve(); OUT=(ROOT/'vero_divcore_primitive_semantics_v17').resolve()
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(); P=OUT/'source'; shutil.copytree(SOURCE,P)
for c in P.rglob('.lake'):
    if c.is_dir(): shutil.rmtree(c)

header=r'''
import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

open Galoistools
namespace VeroDivCorePrimitiveSemanticsV17
'''
footer='\nend VeroDivCorePrimitiveSemanticsV17\n'

probes={
'strip_eval_mod': r'''
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
        simp [Galoistools.gfStrip, ih, Galoistools.refPolyEvalRevAux]
      · simp [Galoistools.gfStrip, h]
''',
'add_eval_mod': r'''
theorem add_eval_mod (p x : Nat) (a b : List Nat) :
    NatModEq p
      (Galoistools.refPolyEval p (Galoistools.gfAdd a b p) x)
      (Galoistools.refPolyEval p a x + Galoistools.refPolyEval p b x) := by
  unfold NatModEq Galoistools.gfAdd Galoistools.refPolyEval
  induction a.reverse generalizing b with
  | nil => simp [Galoistools.zipAddPad, Galoistools.gfStrip, Galoistools.refPolyEvalRevAux]
  | cons ah at ih =>
      cases hbr : b.reverse with
      | nil => simp [Galoistools.zipAddPad, Galoistools.gfStrip, Galoistools.refPolyEvalRevAux, ih]
      | cons bh bt => simp [Galoistools.zipAddPad, Galoistools.gfStrip, Galoistools.refPolyEvalRevAux, ih]
''',
'sub_eval_cancel_mod': r'''
theorem sub_eval_cancel_mod (p x : Nat) (cur sub : List Nat)
    (hp : 1 < p) (hn : Galoistools.IsNorm p cur) :
    NatModEq p
      (Galoistools.refPolyEval p
        (Galoistools.gfAdd (Galoistools.gfSub cur sub p) sub p) x)
      (Galoistools.refPolyEval p cur x) := by
  unfold NatModEq Galoistools.gfAdd Galoistools.gfSub Galoistools.refPolyEval
  simp
'''
}

build=subprocess.run(['lake','build','Galoistools.Proof.Ring','Galoistools.Impl.Division','Galoistools.Spec.Division'],cwd=P,text=True,capture_output=True,timeout=300)
if build.returncode:
    raw=build.stdout+'\n'+build.stderr
    print('V17_PRIMITIVE_SEMANTICS',json.dumps({'stage':'build','exit':build.returncode,'tail':raw[-12000:]})); raise SystemExit(1)

rows=[]
for name,body in probes.items():
    q=P/f'Probe_{name}.lean'; q.write_text(header+body+footer)
    cp=subprocess.run(['lake','env','lean',q.name],cwd=P,text=True,capture_output=True,timeout=300)
    raw=cp.stdout+'\n'+cp.stderr
    row={'probe':name,'exit':cp.returncode,'tail':raw[-18000:] if cp.returncode else ''}
    rows.append(row)
    print('V17_PRIMITIVE_ARM',name,json.dumps({'exit':cp.returncode,'tail':row['tail']}))
(OUT/'result.json').write_text(json.dumps(rows,indent=2))
print('V17_PRIMITIVE_SEMANTICS',json.dumps({'stage':'probes','rows':[{'probe':r['probe'],'exit':r['exit']} for r in rows]}))
raise SystemExit(0)
