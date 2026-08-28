from pathlib import Path
import shutil, subprocess, json

ROOT=Path.cwd()
SOURCE=(ROOT/'coldcert'/'project').resolve()
OUT=(ROOT/'vero_msi_interface_compilation_v8').resolve()
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

EVAL_REDUCED = r'''
@[simp] theorem msi_eval_reduced (p x : Nat) (hp : 0 < p) : ∀ xs : List Nat,
    Galoistools.refPolyEval p xs x % p = Galoistools.refPolyEval p xs x := by
  intro xs
  unfold Galoistools.refPolyEval
  induction xs.reverse with
  | nil => simp [Galoistools.refPolyEvalRevAux]
  | cons a as ih => simp [Galoistools.refPolyEvalRevAux, Nat.mod_mod]
'''

EVAL_PADDING = r'''
@[simp] theorem msi_eval_append_zero (p x : Nat) (f : List Nat) :
    Galoistools.refPolyEval p (f ++ [0]) x =
      (Galoistools.refPolyEval p f x * x) % p := by
  simp [Galoistools.refPolyEval, Galoistools.refPolyEvalRevAux, Nat.mul_comm]

theorem msi_eval_append_zeros (p x n : Nat) (f : List Nat) (hp : 0 < p) :
    Galoistools.refPolyEval p (f ++ List.replicate n 0) x =
      (Galoistools.refPolyEval p f x * x^n) % p := by
  induction n generalizing f with
  | zero =>
      simp only [List.replicate_zero, List.append_nil, Nat.pow_zero, Nat.mul_one]
      exact (msi_eval_reduced p x hp f).symm
  | succ n ih =>
      simp only [List.replicate_succ]
      rw [show f ++ 0 :: List.replicate n 0 = (f ++ [0]) ++ List.replicate n 0 by simp]
      rw [ih (f := f ++ [0])]
      rw [msi_eval_append_zero]
      rw [Nat.pow_succ]
      have hmod : NatModEq p
          (((Galoistools.refPolyEval p f x * x) % p) * x^n)
          ((Galoistools.refPolyEval p f x * x) * x^n) := by
        apply natModEq_mul
        · exact natModEq_mod_left (by rfl)
        · rfl
      unfold NatModEq at hmod
      simpa [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm] using hmod
'''

MUL_EVAL = r'''
theorem msi_mul_eval_hom (p x : Nat) (u v : List Nat) :
    Galoistools.refPolyEval p (Galoistools.gfMul u v p) x =
      (Galoistools.refPolyEval p u x * Galoistools.refPolyEval p v x) % p := by
  simp only [Galoistools.gfMul]
  by_cases hzero : u = [] ∨ v = []
  · rw [if_pos hzero]
    rcases hzero with rfl | rfl <;> simp [Galoistools.refPolyEval, Galoistools.refPolyEvalRevAux]
  · rw [if_neg hzero, refPolyEval_gfStrip]
    simp only [Galoistools.refPolyEval, List.reverse_reverse]
    have hconv := natModEq_refPolyEvalRevAux_convolve p x u.reverse v.reverse
    unfold NatModEq at hconv
    have hevalmod :
        Galoistools.refPolyEvalRevAux p x (Galoistools.convolve p u.reverse v.reverse) % p =
          Galoistools.refPolyEvalRevAux p x (Galoistools.convolve p u.reverse v.reverse) := by
      cases Galoistools.convolve p u.reverse v.reverse <;>
        simp [Galoistools.refPolyEvalRevAux]
    calc
      Galoistools.refPolyEvalRevAux p x (Galoistools.convolve p u.reverse v.reverse) =
          Galoistools.refPolyEvalRevAux p x (Galoistools.convolve p u.reverse v.reverse) % p := hevalmod.symm
      _ = (Galoistools.refPolyEvalRevAux p x u.reverse *
            Galoistools.refPolyEvalRevAux p x v.reverse) % p := hconv
'''

SHAM = r'''
@[simp] theorem msi_v8_sham (n : Nat) : n + 0 = n := by simp
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

def run(label, reduced=False, padding=False, mul=False, sham=False):
    p=OUT/label
    shutil.copytree(SOURCE,p)
    for c in p.rglob('.lake'):
        if c.is_dir(): shutil.rmtree(c)
    pf=p/DIV
    extra=GEN2+STRUCT+(EVAL_REDUCED if reduced or padding else '')+(EVAL_PADDING if padding else '')+(MUL_EVAL if mul else '')+(SHAM if sham else '')
    s=inject(pf.read_text(),extra)
    s=patch_struct(s)
    pf.write_text(s)
    cp=subprocess.run(['lake','build','Galoistools.Proof.Division'],cwd=p,text=True,capture_output=True,timeout=300)
    raw=cp.stdout+'\n'+cp.stderr
    errs=[x for x in raw.splitlines() if 'error:' in x]
    return {'exit':cp.returncode,'error_count':len(errs),'error_lines':errs,'tail':raw[-42000:]}

matrix={
 'structural':run('structural'),
 'sham':run('sham',sham=True),
 'eval_reduced':run('eval_reduced',reduced=True),
 'eval_padding':run('eval_padding',padding=True),
 'mul_eval':run('mul_eval',mul=True),
 'joint_eval':run('joint_eval',padding=True,mul=True),
}
for k,v in matrix.items(): print('MSI_V8_ARM',k,json.dumps({'exit':v['exit'],'error_count':v['error_count']}))
base=matrix['structural']['error_count']
payload={'schema':'msi.vero-interface-compilation.v8','matrix':matrix,
         'gains':{k:base-v['error_count'] for k,v in matrix.items()}}
(OUT/'result.json').write_text(json.dumps(payload,indent=2))
print('VERO_MSI_INTERFACE_COMPILATION_V8',json.dumps(payload['gains']))
