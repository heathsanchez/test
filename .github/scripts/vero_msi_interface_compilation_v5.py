from pathlib import Path
import shutil, subprocess, json

ROOT=Path.cwd()
SOURCE=(ROOT/'coldcert'/'project').resolve()
OUT=(ROOT/'vero_msi_interface_compilation_v5').resolve()
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

STRUCT = r'''
theorem msi_refGfStrip_ne_zero_cons : ∀ xs ys : List Nat,
    Galoistools.refGfStrip xs ≠ 0 :: ys := by
  intro xs ys
  induction xs with
  | nil => simp [Galoistools.refGfStrip]
  | cons a as ih =>
      simp only [Galoistools.refGfStrip]
      by_cases h : a = 0
      · simp [h, ih]
      · simp [h]

 theorem msi_norm_cons_head_ne_zero (p a : Nat) (as : List Nat)
    (hn : Galoistools.IsNorm p (a :: as)) : a ≠ 0 := by
  intro ha
  subst a
  unfold Galoistools.IsNorm Galoistools.refGfTrunc at hn
  simp only [List.map_cons, Nat.zero_mod, Galoistools.refGfStrip] at hn
  exact msi_refGfStrip_ne_zero_cons (as.map (fun x => x % p)) as hn
'''

SHAM = r'''
@[simp] theorem msi_v5_sham (n : Nat) : n * 1 = n := by simp
'''

def inject(src, extra):
    marker='-- !benchmark @end global_aux'
    i=src.find(marker)
    if i < 0: raise RuntimeError('global_aux marker missing')
    return src[:i] + '\n' + extra + '\n' + src[i:]

def patch_v5(src):
    reps = [
      ('exact Nat.mod_lt _ (by omega)', 'exact Nat.mod_lt _ (Nat.zero_lt_of_lt hp.1)'),
      ('have hdlt : d < p := lt_of_le_of_lt hdle hlt', 'have hdlt : d < p := Nat.lt_of_le_of_lt hdle hlt'),
      ('''        have ha0 : a ≠ 0 := by
          intro ha
          subst a
          simp at hmod
          omega''', '''        have ha0 : a ≠ 0 := by
          exact msi_norm_cons_head_ne_zero p a as hn'''),
      ('''        have hd0 : d ≠ 0 := by
          intro hd
          subst d
          simp at hdp
          omega''', '''        have hd0 : d ≠ 0 := by
          intro hd
          subst d
          rcases hdp with ⟨k, hk⟩
          have hp0 : p ≠ 0 := by omega
          apply hp0
          simpa using hk'''),
    ]
    # Accept V4-mutated alternatives too, because source is frozen cold and exact text is known.
    alts = {
      reps[2][0]: reps[2][1],
      reps[3][0]: reps[3][1],
    }
    for old,new in reps[:2]:
        if old not in src: raise RuntimeError('missing patch pattern: '+old)
        src=src.replace(old,new,1)
    # structural a != 0 block
    old=reps[2][0]
    if old not in src: raise RuntimeError('missing ha0 block')
    src=src.replace(old,reps[2][1],1)
    # frozen source has original hd0 block
    old=reps[3][0]
    if old not in src: raise RuntimeError('missing hd0 block')
    src=src.replace(old,reps[3][1],1)
    return src

def run(label, repair=False, sham=False):
    p=OUT/label
    shutil.copytree(SOURCE,p)
    for c in p.rglob('.lake'):
        if c.is_dir(): shutil.rmtree(c)
    pf=p/DIV
    s=inject(pf.read_text(), GEN2 + (STRUCT if repair else '') + (SHAM if sham else ''))
    if repair: s=patch_v5(s)
    pf.write_text(s)
    cp=subprocess.run(['lake','build','Galoistools.Proof.Division'],cwd=p,text=True,capture_output=True,timeout=300)
    raw=cp.stdout+'\n'+cp.stderr
    errs=[x for x in raw.splitlines() if 'error:' in x]
    return {'exit':cp.returncode,'error_count':len(errs),'error_lines':errs,'tail':raw[-32000:]}

matrix={
 'gen2':run('gen2'),
 'sham':run('sham',sham=True),
 'structural_gcd_infra':run('structural_gcd_infra',repair=True),
}
for k,v in matrix.items(): print('MSI_V5_ARM',k,json.dumps({'exit':v['exit'],'error_count':v['error_count']}))
base=matrix['gen2']['error_count']
payload={'schema':'msi.vero-interface-compilation.v5','matrix':matrix,'gains':{k:base-v['error_count'] for k,v in matrix.items()}}
(OUT/'result.json').write_text(json.dumps(payload,indent=2))
print('VERO_MSI_INTERFACE_COMPILATION_V5',json.dumps(payload['gains']))
