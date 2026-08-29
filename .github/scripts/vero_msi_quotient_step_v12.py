from pathlib import Path
import ast, json, shutil, subprocess

ROOT=Path.cwd(); SOURCE=(ROOT/'coldcert'/'project').resolve(); OUT=(ROOT/'vero_msi_quotient_step_v12').resolve()
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(); DIV=Path('Galoistools/Proof/Division.lean')

def literal_assign(path, name):
    tree=ast.parse(path.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    return ast.literal_eval(node.value)
    raise RuntimeError(f'missing {name}')

v8b=ROOT/'.github/scripts/vero_msi_interface_compilation_v8b.py'
GEN2=literal_assign(v8b,'GEN2'); STRUCT=literal_assign(v8b,'STRUCT')
probes=literal_assign(ROOT/'.github/scripts/vero_div_identity_invariant.py','probes')
QUOTIENT_STEP=probes['quotient_term_mul'].replace('theorem quotient_term_mul','@[simp] theorem msi_quotient_step_mul',1)

def add_ring_import(src):
    if 'import Galoistools.Proof.Ring\n' in src: return src
    return src.replace('import Galoistools.Spec.Division\n','import Galoistools.Spec.Division\nimport Galoistools.Proof.Ring\n',1)

def inject(src,extra):
    m='-- !benchmark @end global_aux'; i=src.find(m)
    if i<0: raise RuntimeError('global_aux marker missing')
    return src[:i]+'\n'+extra+'\n'+src[i:]

def patch_struct(src):
    reps=[
      ('exact Nat.mod_lt _ (by omega)','exact Nat.mod_lt _ (Nat.zero_lt_of_lt hp.1)'),
      ('have hdlt : d < p := lt_of_le_of_lt hdle hlt','have hdlt : d < p := Nat.lt_of_le_of_lt hdle hlt'),
      ('''        have ha0 : a ≠ 0 := by\n          intro ha\n          subst a\n          simp at hmod\n          omega''','''        have ha0 : a ≠ 0 := by\n          exact msi_norm_cons_head_ne_zero p a as hn'''),
      ('''        have hd0 : d ≠ 0 := by\n          intro hd\n          subst d\n          simp at hdp\n          omega''','''        have hd0 : d ≠ 0 := by\n          intro hd\n          rcases hda with ⟨k, hk⟩\n          rw [hd] at hk\n          simp at hk\n          exact ha0 hk''')]
    for a,b in reps:
        if a not in src: raise RuntimeError('missing structural patch')
        src=src.replace(a,b,1)
    return src

# Hard proof gate: exact historical theorem, isolated from benchmark residuals.
gate=OUT/'proof_gate'; shutil.copytree(SOURCE,gate)
for c in gate.rglob('.lake'):
    if c.is_dir(): shutil.rmtree(c)
probe=gate/'QuotientStepV12.lean'
probe.write_text('import Galoistools.Proof.Ring\nimport Galoistools.Impl.Division\nimport Galoistools.Spec.Division\n\n'+QUOTIENT_STEP)
# Build the complete explicit import closure before invoking lean directly.
build=subprocess.run(['lake','build','Galoistools.Proof.Ring','Galoistools.Impl.Division','Galoistools.Spec.Division'],cwd=gate,text=True,capture_output=True,timeout=300)
if build.returncode:
    raw=build.stdout+'\n'+build.stderr
    print('V12_PROOF_GATE',json.dumps({'stage':'import_build','exit':build.returncode,'tail':raw[-5000:]})); raise SystemExit(1)
cp=subprocess.run(['lake','env','lean','QuotientStepV12.lean'],cwd=gate,text=True,capture_output=True,timeout=300)
raw=cp.stdout+'\n'+cp.stderr
print('V12_PROOF_GATE',json.dumps({'stage':'lemma','exit':cp.returncode,'tail':raw[-9000:]}))
if cp.returncode:
    (OUT/'result.json').write_text(json.dumps({'proof_gate':{'exit':cp.returncode,'tail':raw[-30000:]}},indent=2)); raise SystemExit(1)

def run(label, quotient=False, sham=False):
    p=OUT/label; shutil.copytree(SOURCE,p)
    for c in p.rglob('.lake'):
        if c.is_dir(): shutil.rmtree(c)
    pf=p/DIV; s=add_ring_import(pf.read_text())
    extra=GEN2+STRUCT+(QUOTIENT_STEP if quotient else '')+(r'@[simp] theorem msi_v12_sham (n : Nat) : n + 0 = n := by simp' if sham else '')
    s=patch_struct(inject(s,extra)); pf.write_text(s)
    cp=subprocess.run(['lake','build','Galoistools.Proof.Division'],cwd=p,text=True,capture_output=True,timeout=300)
    raw=cp.stdout+'\n'+cp.stderr; errs=[x for x in raw.splitlines() if 'error:' in x]
    return {'exit':cp.returncode,'error_count':len(errs),'error_lines':errs,'tail':raw[-50000:]}

matrix={'control':run('control'),'sham':run('sham',sham=True),'quotient_step':run('quotient_step',quotient=True)}
for k,v in matrix.items(): print('MSI_V12_ARM',k,json.dumps({'exit':v['exit'],'error_count':v['error_count']}))
base=matrix['control']['error_count']; gains={k:base-v['error_count'] for k,v in matrix.items()}
payload={'schema':'msi.vero-quotient-step.v12','proof_gate':'passed','matrix':matrix,'gains':gains}
(OUT/'result.json').write_text(json.dumps(payload,indent=2))
print('VERO_MSI_QUOTIENT_STEP_V12',json.dumps(gains))
