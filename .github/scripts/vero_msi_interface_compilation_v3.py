from pathlib import Path
import shutil, subprocess, json

ROOT=Path.cwd()
SOURCE=(ROOT/'coldcert'/'project').resolve()
OUT=(ROOT/'vero_msi_interface_compilation_v3').resolve()
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

LOW_DIV = r'''
@[simp] theorem msi_gfDiv_low_degree (f g : List Nat) (p : Nat)
    (hg : g ≠ []) (hlt : Galoistools.gfDegree f < Galoistools.gfDegree g) :
    Galoistools.gfDiv f g p = ([], Galoistools.gfStrip f) := by
  simp [Galoistools.gfDiv, hg, hlt]
'''

LOW_REM = r'''
@[simp] theorem msi_gfRem_low_degree (f g : List Nat) (p : Nat)
    (hg : g ≠ []) (hlt : Galoistools.gfDegree f < Galoistools.gfDegree g) :
    Galoistools.gfRem f g p = Galoistools.gfStrip f := by
  simp [Galoistools.gfRem, msi_gfDiv_low_degree f g p hg hlt]
'''

REF_BRIDGE = r'''
@[simp] theorem msi_degree_bridge (f : List Nat) :
    Galoistools.gfDegree f = Galoistools.refGfDegree f := by rfl
'''

SHAM = r'''
@[simp] theorem msi_v3_sham (n : Nat) : n + 0 = n := by simp
'''

def inject(src, extra):
    marker='-- !benchmark @end global_aux'
    i=src.find(marker)
    if i < 0: raise RuntimeError('global_aux marker missing')
    return src[:i] + '\n' + extra + '\n' + src[i:]

def run(label, extra):
    p=OUT/label
    shutil.copytree(SOURCE,p)
    for c in p.rglob('.lake'):
        if c.is_dir(): shutil.rmtree(c)
    pf=p/DIV
    pf.write_text(inject(pf.read_text(),extra))
    cp=subprocess.run(['lake','build','Galoistools.Proof.Division'],cwd=p,text=True,capture_output=True,timeout=300)
    raw=cp.stdout+'\n'+cp.stderr
    errs=[x for x in raw.splitlines() if 'error:' in x]
    return {'exit':cp.returncode,'error_count':len(errs),'error_lines':errs,'tail':raw[-26000:]}

arms={
 'gen2':GEN2,
 'sham':GEN2+SHAM,
 'low_div':GEN2+LOW_DIV,
 'low_div_rem':GEN2+LOW_DIV+LOW_REM,
 'low_div_rem_bridge':GEN2+REF_BRIDGE+LOW_DIV+LOW_REM,
}
matrix={k:run(k,v) for k,v in arms.items()}
for k,v in matrix.items(): print('MSI_V3_ARM',k,json.dumps({'exit':v['exit'],'error_count':v['error_count']}))
base=matrix['gen2']['error_count']
payload={'schema':'msi.vero-interface-compilation.v3','matrix':matrix,'gains':{k:base-v['error_count'] for k,v in matrix.items()}}
(OUT/'result.json').write_text(json.dumps(payload,indent=2))
print('VERO_MSI_INTERFACE_COMPILATION_V3',json.dumps(payload['gains']))
