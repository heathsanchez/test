from pathlib import Path
import shutil, subprocess, json, re

ROOT=Path.cwd()
SOURCE=(ROOT/'coldcert'/'project').resolve()
OUT=(ROOT/'vero_msi_interface_compilation_v1').resolve()
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir()

DIV=Path('Galoistools/Proof/Division.lean')

WARM = r'''

@[simp] theorem msi_gfMonic_nil (p : Nat) :
    (Galoistools.gfMonic [] p).snd = [] := by
  rfl

@[simp] theorem msi_gfStrip_idem (xs : List Nat) :
    Galoistools.gfStrip (Galoistools.gfStrip xs) = Galoistools.gfStrip xs := by
  induction xs with
  | nil => rfl
  | cons a as ih =>
      by_cases h : a = 0
      · simp [Galoistools.gfStrip, h, ih]
      · simp [Galoistools.gfStrip, h]
'''

SHAM = r'''

@[simp] theorem msi_sham_append_nil (xs : List Nat) : xs ++ [] = xs := by
  simp
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
    if extra:
        pf.write_text(inject(pf.read_text(), extra))
    cp=subprocess.run(['lake','build','Galoistools.Proof.Division'],cwd=p,text=True,capture_output=True,timeout=300)
    raw=cp.stdout+'\n'+cp.stderr
    errs=[x for x in raw.splitlines() if 'error:' in x]
    locs=[]
    for x in errs:
        m=re.search(r'Division\.lean:(\d+):',x)
        if m: locs.append(int(m.group(1)))
    return {'exit':cp.returncode,'error_count':len(errs),'error_lines':errs,'locations':locs,'tail':raw[-18000:]}

matrix={
 'cold':run('cold'),
 'sham':run('sham',SHAM),
 'warm':run('warm',WARM),
}
for k,v in matrix.items(): print('MSI_INTERFACE_ARM',k,json.dumps({'exit':v['exit'],'error_count':v['error_count'],'locations':v['locations']}))
contraction=matrix['cold']['error_count']-matrix['warm']['error_count']
sham_contraction=matrix['cold']['error_count']-matrix['sham']['error_count']
payload={'schema':'msi.vero-interface-compilation.v1','matrix':matrix,'warm_contraction':contraction,'sham_contraction':sham_contraction,'causal_gain':contraction>0 and sham_contraction<=0}
(OUT/'result.json').write_text(json.dumps(payload,indent=2))
print('VERO_MSI_INTERFACE_COMPILATION_V1',json.dumps({'cold':matrix['cold']['error_count'],'warm':matrix['warm']['error_count'],'sham':matrix['sham']['error_count'],'warm_contraction':contraction,'causal_gain':payload['causal_gain']}))
# Measurement experiment: workflow stays green so evidence uploads even if Lean frontier remains open.
