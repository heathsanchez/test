from pathlib import Path
import shutil, subprocess, json

ROOT=Path.cwd()
SOURCE=(ROOT/'coldcert'/'project').resolve()
OUT=(ROOT/'vero_msi_interface_compilation_v6').resolve()
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

FALLBACK = r'''
theorem msi_gcd_fallback_shape (xs : List Nat) (p : Nat) :
    let m := (Galoistools.gfMonic xs p).snd
    (if m = [] then [1]
      else if Galoistools.leadCoeff m = 1 then m else [1]) = [] ∨
    Galoistools.refLeadCoeff
      (if m = [] then [1]
       else if Galoistools.leadCoeff m = 1 then m else [1]) = 1 := by
  dsimp
  by_cases h0 : (Galoistools.gfMonic xs p).snd = []
  · simp [h0, Galoistools.refLeadCoeff]
  · by_cases h1 : Galoistools.leadCoeff (Galoistools.gfMonic xs p).snd = 1
    · right
      simpa [h0, h1, Galoistools.leadCoeff] using h1
    · simp [h0, h1, Galoistools.refLeadCoeff]
'''

SHAM = r'''
@[simp] theorem msi_v6_sham (n : Nat) : n ^ 1 = n := by simp
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
        if old not in src: raise RuntimeError('missing patch pattern')
        src=src.replace(old,new,1)
    return src

def patch_gcd_consumer(src):
    marker='-- !benchmark @start proof def=prove_gcd_monic'
    a=src.index(marker)
    old='simp [Galoistools.gfGcd, hboth, heq, hg0]'
    i=src.index(old,a)
    new='''simpa [Galoistools.gfGcd, hboth, heq, hg0] using
      msi_gcd_fallback_shape (Galoistools.gcdLoop p (f.length + g.length + 1) f g) p'''
    return src[:i]+new+src[i+len(old):]

def run(label, repair=False, fallback=False, sham=False):
    p=OUT/label
    shutil.copytree(SOURCE,p)
    for c in p.rglob('.lake'):
        if c.is_dir(): shutil.rmtree(c)
    pf=p/DIV
    extra=GEN2+(STRUCT if repair else '')+(FALLBACK if fallback else '')+(SHAM if sham else '')
    s=inject(pf.read_text(),extra)
    if repair: s=patch_struct(s)
    if fallback: s=patch_gcd_consumer(s)
    pf.write_text(s)
    cp=subprocess.run(['lake','build','Galoistools.Proof.Division'],cwd=p,text=True,capture_output=True,timeout=300)
    raw=cp.stdout+'\n'+cp.stderr
    errs=[x for x in raw.splitlines() if 'error:' in x]
    return {'exit':cp.returncode,'error_count':len(errs),'error_lines':errs,'tail':raw[-34000:]}

matrix={
 'gen2':run('gen2'),
 'sham':run('sham',sham=True),
 'structural_fixed':run('structural_fixed',repair=True),
 'gcd_fallback_interface':run('gcd_fallback_interface',repair=True,fallback=True),
}
for k,v in matrix.items(): print('MSI_V6_ARM',k,json.dumps({'exit':v['exit'],'error_count':v['error_count']}))
base=matrix['gen2']['error_count']
payload={'schema':'msi.vero-interface-compilation.v6','matrix':matrix,'gains':{k:base-v['error_count'] for k,v in matrix.items()},'fallback_gain_over_structural':matrix['structural_fixed']['error_count']-matrix['gcd_fallback_interface']['error_count']}
(OUT/'result.json').write_text(json.dumps(payload,indent=2))
print('VERO_MSI_INTERFACE_COMPILATION_V6',json.dumps({'gains':payload['gains'],'fallback_gain_over_structural':payload['fallback_gain_over_structural']}))
