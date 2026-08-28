from pathlib import Path
import shutil, subprocess, json

ROOT=Path.cwd()
SOURCE=(ROOT/'coldcert'/'project').resolve()
OUT=(ROOT/'vero_msi_interface_compilation_v4').resolve()
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir()
DIV=Path('Galoistools/Proof/Division.lean')

GEN2 = r'''
@[simp] theorem msi_gfMonic_nil (p : Nat) :
    (Galoistools.gfMonic [] p).snd = [] := by rfl

@[simp] theorem msi_gfMonic_if_nil (g : List Nat) (p : Nat) :
    (if g = [] then [] else (Galoistools.gfMonic g p).snd) =
      (Galoistools.gfMonic g p).snd := by
  by_cases h : g = []
  · subst g; simp
  · simp [h]
'''

SHAM = r'''
@[simp] theorem msi_v4_sham (n : Nat) : 0 + n = n := by simp
'''

def inject(src, extra):
    marker='-- !benchmark @end global_aux'
    i=src.find(marker)
    if i < 0: raise RuntimeError('global_aux marker missing')
    return src[:i] + '\n' + extra + '\n' + src[i:]

def patch_infra(src):
    reps = [
      ('exact Nat.mod_lt _ (by omega)', 'exact Nat.mod_lt _ (Nat.zero_lt_of_lt hp.1)'),
      ('have hdlt : d < p := lt_of_le_of_lt hdle hlt', 'have hdlt : d < p := Nat.lt_of_le_of_lt hdle hlt'),
      ('          simp at hdp\n          omega', '          have hp0 : p ≠ 0 := by omega\n          exact hp0 (by simpa using hdp)'),
    ]
    for old,new in reps:
        if old not in src:
            raise RuntimeError('missing patch pattern: '+old)
        src=src.replace(old,new,1)
    return src

def run(label, infra=False, sham=False):
    p=OUT/label
    shutil.copytree(SOURCE,p)
    for c in p.rglob('.lake'):
        if c.is_dir(): shutil.rmtree(c)
    pf=p/DIV
    s=inject(pf.read_text(), GEN2 + (SHAM if sham else ''))
    if infra: s=patch_infra(s)
    pf.write_text(s)
    cp=subprocess.run(['lake','build','Galoistools.Proof.Division'],cwd=p,text=True,capture_output=True,timeout=300)
    raw=cp.stdout+'\n'+cp.stderr
    errs=[x for x in raw.splitlines() if 'error:' in x]
    return {'exit':cp.returncode,'error_count':len(errs),'error_lines':errs,'tail':raw[-30000:]}

matrix={
  'gen2': run('gen2'),
  'sham': run('sham',sham=True),
  'gcd_monic_infra': run('gcd_monic_infra',infra=True),
}
for k,v in matrix.items(): print('MSI_V4_ARM',k,json.dumps({'exit':v['exit'],'error_count':v['error_count']}))
base=matrix['gen2']['error_count']
payload={'schema':'msi.vero-interface-compilation.v4','matrix':matrix,'gains':{k:base-v['error_count'] for k,v in matrix.items()}}
(OUT/'result.json').write_text(json.dumps(payload,indent=2))
print('VERO_MSI_INTERFACE_COMPILATION_V4',json.dumps(payload['gains']))
