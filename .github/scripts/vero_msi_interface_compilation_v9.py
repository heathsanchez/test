from pathlib import Path
import ast, json, shutil, subprocess

ROOT=Path.cwd(); SOURCE=(ROOT/'coldcert'/'project').resolve(); OUT=(ROOT/'vero_msi_interface_compilation_v9').resolve()
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(); DIV=Path('Galoistools/Proof/Division.lean')

def literal_assign(path, name):
    tree=ast.parse(path.read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == name:
                    return ast.literal_eval(node.value)
    raise RuntimeError(f'missing {name} in {path}')

v8b=ROOT/'.github/scripts/vero_msi_interface_compilation_v8b.py'
GEN2=literal_assign(v8b,'GEN2'); STRUCT=literal_assign(v8b,'STRUCT')
probes=literal_assign(ROOT/'.github/scripts/vero_div_identity_invariant.py','probes')

QUOTIENT_TERM=probes['quotient_term_mul'].replace('theorem quotient_term_mul','@[simp] theorem msi_quotient_term_mul',1)
PREFIX_SHAPE=probes['completed_prefix_shape'].replace('theorem completed_prefix_shape','theorem msi_completed_prefix_shape',1)
SHIFT_SHAPE=probes['shift_singleton_shape'].replace('theorem shift_singleton_shape','@[simp] theorem msi_shift_singleton_shape',1)
SHAM=r'''@[simp] theorem msi_v9_sham (n : Nat) : n * 1 = n := by simp'''

def inject(src, extra):
    m='-- !benchmark @end global_aux'; i=src.find(m)
    if i<0: raise RuntimeError('global_aux marker missing')
    return src[:i]+'\n'+extra+'\n'+src[i:]

def add_ring_import(src):
    if 'import Galoistools.Proof.Ring\n' in src: return src
    return src.replace('import Galoistools.Spec.Division\n','import Galoistools.Spec.Division\nimport Galoistools.Proof.Ring\n',1)

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

def run(label, ring=False, quotient=False, prefix=False, shift=False, sham=False):
    p=OUT/label; shutil.copytree(SOURCE,p)
    for c in p.rglob('.lake'):
        if c.is_dir(): shutil.rmtree(c)
    pf=p/DIV; s=pf.read_text()
    if ring: s=add_ring_import(s)
    extra=GEN2+STRUCT+(SHIFT_SHAPE if shift else '')+(QUOTIENT_TERM if quotient else '')+(PREFIX_SHAPE if prefix else '')+(SHAM if sham else '')
    s=patch_struct(inject(s,extra)); pf.write_text(s)
    cp=subprocess.run(['lake','build','Galoistools.Proof.Division'],cwd=p,text=True,capture_output=True,timeout=300)
    raw=cp.stdout+'\n'+cp.stderr; errs=[x for x in raw.splitlines() if 'error:' in x]
    infra=[x for x in errs if 'Unknown identifier' in x or 'declaration uses' in x or 'failed to synthesize' in x]
    return {'exit':cp.returncode,'error_count':len(errs),'infra_errors':infra,'error_lines':errs,'tail':raw[-50000:]}

matrix={
  'structural':run('structural'),
  'sham':run('sham',sham=True),
  'ring_import_control':run('ring_import_control',ring=True),
  'shift_shape':run('shift_shape',ring=True,shift=True),
  'quotient_term':run('quotient_term',ring=True,quotient=True),
  'prefix_shape':run('prefix_shape',ring=True,prefix=True),
  'joint_transition':run('joint_transition',ring=True,shift=True,quotient=True,prefix=True),
}
for k,v in matrix.items():
    print('MSI_V9_ARM',k,json.dumps({'exit':v['exit'],'error_count':v['error_count'],'infra_errors':len(v['infra_errors'])}))
base=matrix['ring_import_control']['error_count']
payload={'schema':'msi.vero-interface-compilation.v9','matrix':matrix,
         'gains_vs_import_control':{k:base-v['error_count'] for k,v in matrix.items()}}
(OUT/'result.json').write_text(json.dumps(payload,indent=2))
print('VERO_MSI_INTERFACE_COMPILATION_V9',json.dumps(payload['gains_vs_import_control']))
