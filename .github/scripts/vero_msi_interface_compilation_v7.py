from pathlib import Path
import shutil, subprocess, json

ROOT=Path.cwd()
SOURCE=(ROOT/'coldcert'/'project').resolve()
OUT=(ROOT/'vero_msi_interface_compilation_v7').resolve()
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

LOW = r'''
@[simp] theorem msi_gfDiv_low_degree (f g : List Nat) (p : Nat)
    (hg : g ≠ []) (hlt : Galoistools.gfDegree f < Galoistools.gfDegree g) :
    Galoistools.gfDiv f g p = ([], Galoistools.gfStrip f) := by
  simp [Galoistools.gfDiv, hg, hlt]

@[simp] theorem msi_gfRem_low_degree (f g : List Nat) (p : Nat)
    (hg : g ≠ []) (hlt : Galoistools.gfDegree f < Galoistools.gfDegree g) :
    Galoistools.gfRem f g p = Galoistools.gfStrip f := by
  simp [Galoistools.gfRem, msi_gfDiv_low_degree f g p hg hlt]
'''

IDEM = r'''
@[simp] theorem msi_gfStrip_idem (xs : List Nat) :
    Galoistools.gfStrip (Galoistools.gfStrip xs) = Galoistools.gfStrip xs := by
  induction xs with
  | nil => rfl
  | cons a as ih =>
      by_cases h : a = 0
      · simp [Galoistools.gfStrip, h, ih]
      · simp [Galoistools.gfStrip, h]

@[simp] theorem msi_gfRem_idem (f g : List Nat) (p : Nat) (hg : g ≠ []) :
    Galoistools.gfRem (Galoistools.gfRem f g p) g p = Galoistools.gfRem f g p := by
  simp [Galoistools.gfRem, Galoistools.gfDiv, hg, msi_gfStrip_idem]
'''

SHAM = r'''
@[simp] theorem msi_v7_sham (n : Nat) : 1 * n = n := by simp
'''

def inject(src, extra):
    marker='-- !benchmark @end global_aux'
    i=src.find(marker)
    if i < 0: raise RuntimeError('global_aux marker missing')
    return src[:i]+'\n'+extra+'\n'+src[i:]

def patch_struct(src):
    reps=[
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
          rcases hda with ⟨k, hk⟩
          rw [hd] at hk
          simp at hk
          exact ha0 hk'''),
    ]
    for old,new in reps:
        if old not in src: raise RuntimeError('missing structural patch pattern')
        src=src.replace(old,new,1)
    return src

def run(label, low=False, idem=False, sham=False):
    p=OUT/label
    shutil.copytree(SOURCE,p)
    for c in p.rglob('.lake'):
        if c.is_dir(): shutil.rmtree(c)
    pf=p/DIV
    extra=GEN2+STRUCT+(LOW if low else '')+(IDEM if idem else '')+(SHAM if sham else '')
    s=inject(pf.read_text(),extra)
    s=patch_struct(s)
    pf.write_text(s)
    cp=subprocess.run(['lake','build','Galoistools.Proof.Division'],cwd=p,text=True,capture_output=True,timeout=300)
    raw=cp.stdout+'\n'+cp.stderr
    errs=[x for x in raw.splitlines() if 'error:' in x]
    return {'exit':cp.returncode,'error_count':len(errs),'error_lines':errs,'tail':raw[-36000:]}

matrix={
 'structural':run('structural'),
 'sham':run('sham',sham=True),
 'low_degree':run('low_degree',low=True),
 'rem_idem':run('rem_idem',idem=True),
 'joint':run('joint',low=True,idem=True),
}
for k,v in matrix.items(): print('MSI_V7_ARM',k,json.dumps({'exit':v['exit'],'error_count':v['error_count']}))
base=matrix['structural']['error_count']
payload={'schema':'msi.vero-interface-compilation.v7','matrix':matrix,
         'gains':{k:base-v['error_count'] for k,v in matrix.items()},
         'joint_gain_over_best_single':min(matrix['low_degree']['error_count'],matrix['rem_idem']['error_count'])-matrix['joint']['error_count']}
(OUT/'result.json').write_text(json.dumps(payload,indent=2))
print('VERO_MSI_INTERFACE_COMPILATION_V7',json.dumps({'gains':payload['gains'],'joint_gain_over_best_single':payload['joint_gain_over_best_single']}))
