from pathlib import Path
import shutil, subprocess, json, re

ROOT=Path.cwd()
SOURCE=(ROOT/'coldcert'/'project').resolve()
OUT=(ROOT/'vero_msi_interface_compilation_v2').resolve()
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir()
DIV=Path('Galoistools/Proof/Division.lean')

MONIC_NIL = r'''

@[simp] theorem msi_gfMonic_nil (p : Nat) :
    (Galoistools.gfMonic [] p).snd = [] := by
  rfl
'''

STRIP_IDEM = r'''

@[simp] theorem msi_gfStrip_idem (xs : List Nat) :
    Galoistools.gfStrip (Galoistools.gfStrip xs) = Galoistools.gfStrip xs := by
  induction xs with
  | nil => rfl
  | cons a as ih =>
      by_cases h : a = 0
      · simp [Galoistools.gfStrip, h, ih]
      · simp [Galoistools.gfStrip, h]
'''

MONIC_CANON = MONIC_NIL + r'''

@[simp] theorem msi_gfMonic_if_nil (g : List Nat) (p : Nat) :
    (if g = [] then [] else (Galoistools.gfMonic g p).snd) =
      (Galoistools.gfMonic g p).snd := by
  by_cases h : g = []
  · subst g
    simp
  · simp [h]
'''

SHAM = r'''

@[simp] theorem msi_sham_append_nil (xs : List Nat) : xs ++ [] = xs := by simp
'''

def inject(src, extra):
    marker='-- !benchmark @end global_aux'
    i=src.find(marker)
    if i < 0: raise RuntimeError('global_aux marker missing')
    return src[:i] + extra + '\n' + src[i:]

def run(label, extra=''):
    p=OUT/label
    shutil.copytree(SOURCE,p)
    for c in p.rglob('.lake'):
        if c.is_dir(): shutil.rmtree(c)
    pf=p/DIV
    if extra: pf.write_text(inject(pf.read_text(),extra))
    cp=subprocess.run(['lake','build','Galoistools.Proof.Division'],cwd=p,text=True,capture_output=True,timeout=300)
    raw=cp.stdout+'\n'+cp.stderr
    errs=[x for x in raw.splitlines() if 'error:' in x]
    return {'exit':cp.returncode,'error_count':len(errs),'error_lines':errs,'tail':raw[-22000:]}

arms={
 'cold':'',
 'sham':SHAM,
 'monic_nil':MONIC_NIL,
 'strip_idem':STRIP_IDEM,
 'joint_v1':MONIC_NIL+STRIP_IDEM,
 'monic_canonical_v2':MONIC_CANON,
 'monic_canonical_plus_strip':MONIC_CANON+STRIP_IDEM,
}
matrix={k:run(k,v) for k,v in arms.items()}
for k,v in matrix.items(): print('MSI_V2_ARM',k,json.dumps({'exit':v['exit'],'error_count':v['error_count']}))
cold=matrix['cold']['error_count']
payload={
 'schema':'msi.vero-interface-compilation.v2',
 'matrix':matrix,
 'contractions':{k:cold-v['error_count'] for k,v in matrix.items()},
 'attribution':{
   'monic_nil_gain':cold-matrix['monic_nil']['error_count'],
   'strip_idem_gain':cold-matrix['strip_idem']['error_count'],
   'joint_gain':cold-matrix['joint_v1']['error_count'],
   'second_generation_gain_over_monic':matrix['monic_nil']['error_count']-matrix['monic_canonical_v2']['error_count'],
   'second_generation_gain_over_v1':matrix['joint_v1']['error_count']-matrix['monic_canonical_plus_strip']['error_count'],
 }
}
(OUT/'result.json').write_text(json.dumps(payload,indent=2))
print('VERO_MSI_INTERFACE_COMPILATION_V2',json.dumps(payload['attribution']))
