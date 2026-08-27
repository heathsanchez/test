from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench=Path('benchmarks/galoistools').resolve()
seed=read_artifact(Path('../baseline27/allin_artifact.json').resolve())
out=Path('div_add_structure_v2/source').resolve()
create_sandbox(bench,out,mode='codeproof',overwrite=True,seed_artifact=seed)

header='''import Galoistools.Proof.Ring\nimport Galoistools.Impl.Division\nimport Galoistools.Spec.Division\n\nnamespace GaloistoolsDivAddStructureV2\n'''
footer='\nend GaloistoolsDivAddStructureV2\n'

common=r'''
theorem add_comm_local (a b : List Nat) (p : Nat) :
    Galoistools.gfAdd a b p = Galoistools.gfAdd b a p := by
  have h := prove_add_comm
  simp only [spec_add_comm, canonical] at h
  exact h a b p

theorem add_neg_cancel_local (a : List Nat) (p : Nat) (hp : 1 < p) :
    Galoistools.gfAdd a (Galoistools.gfNeg a p) p = [] := by
  have h := prove_add_neg_cancel
  simp only [spec_add_neg_cancel, canonical] at h
  exact h a p hp

theorem sub_eq_add_neg_local (a b : List Nat) (p : Nat) (hp : 1 < p) :
    Galoistools.gfSub a b p = Galoistools.gfAdd a (Galoistools.gfNeg b p) p := by
  have h := prove_sub_eq_add_neg
  simp only [spec_sub_eq_add_neg, canonical] at h
  exact h a b p hp

theorem gfAdd_strip_right_local (p : Nat) (a b : List Nat) :
    Galoistools.gfAdd a (Galoistools.gfStrip b) p = Galoistools.gfAdd a b p := by
  have hzero : ∀ as bs : List Nat,
      Galoistools.gfStrip (Galoistools.zipAddPad p as bs).reverse =
        Galoistools.gfStrip (Galoistools.zipAddPad p as (bs ++ [0])).reverse := by
    intro as bs
    have hstrip : ∀ xs ys : List Nat,
        Galoistools.gfStrip (xs ++ ys) =
          Galoistools.gfStrip (Galoistools.gfStrip xs ++ ys) := by
      intro xs ys
      induction xs with
      | nil => rfl
      | cons x xs ih =>
        by_cases hx : x = 0
        · simp [Galoistools.gfStrip, hx, ih]
        · simp [Galoistools.gfStrip, hx]
    have hnil : ∀ xs : List Nat,
        Galoistools.zipAddPad p xs [] = xs.map (· % p) := by
      intro xs
      cases xs <;> rfl
    induction as generalizing bs with
    | nil => simp [Galoistools.zipAddPad, Galoistools.gfStrip, List.map_append]
    | cons x xs ih =>
      cases bs with
      | nil => simp [Galoistools.zipAddPad, hnil]
      | cons y ys =>
        simp only [Galoistools.zipAddPad, List.reverse_cons]
        calc
          Galoistools.gfStrip ((Galoistools.zipAddPad p xs ys).reverse ++ [(x+y)%p]) =
              Galoistools.gfStrip (Galoistools.gfStrip (Galoistools.zipAddPad p xs ys).reverse ++ [(x+y)%p]) := hstrip _ _
          _ = Galoistools.gfStrip (Galoistools.gfStrip (Galoistools.zipAddPad p xs (ys ++ [0])).reverse ++ [(x+y)%p]) := by rw [ih ys]
          _ = Galoistools.gfStrip ((Galoistools.zipAddPad p xs (ys ++ [0])).reverse ++ [(x+y)%p]) := (hstrip _ _).symm
          _ = Galoistools.gfStrip (Galoistools.zipAddPad p (x::xs) ((y::ys) ++ [0])).reverse := by simp [Galoistools.zipAddPad]
  induction b with
  | nil => rfl
  | cons x xs ih =>
    by_cases hx : x = 0
    · simp only [Galoistools.gfStrip, hx, if_pos]
      rw [ih]
      simp only [Galoistools.gfAdd, List.reverse_cons]
      exact hzero a.reverse xs.reverse
    · simp [Galoistools.gfStrip, hx]

theorem gfAdd_strip_left_local (p : Nat) (a b : List Nat) :
    Galoistools.gfAdd (Galoistools.gfStrip a) b p = Galoistools.gfAdd a b p := by
  calc
    Galoistools.gfAdd (Galoistools.gfStrip a) b p = Galoistools.gfAdd b (Galoistools.gfStrip a) p := add_comm_local _ _ _
    _ = Galoistools.gfAdd b a p := gfAdd_strip_right_local p b a
    _ = Galoistools.gfAdd a b p := add_comm_local _ _ _

theorem zipAddPad_assoc_local (p : Nat) (xs ys zs : List Nat) :
    Galoistools.zipAddPad p (Galoistools.zipAddPad p xs ys) zs =
      Galoistools.zipAddPad p xs (Galoistools.zipAddPad p ys zs) := by
  have hleft : ∀ as bs : List Nat,
      Galoistools.zipAddPad p (List.map (fun x => x % p) as) bs = Galoistools.zipAddPad p as bs := by
    intro as bs
    induction as generalizing bs with
    | nil => cases bs <;> simp [Galoistools.zipAddPad, Nat.mod_mod]
    | cons a as ih => cases bs <;> simp [Galoistools.zipAddPad, Nat.mod_mod, ih]
  have hright : ∀ as bs : List Nat,
      Galoistools.zipAddPad p as (List.map (fun x => x % p) bs) = Galoistools.zipAddPad p as bs := by
    intro as bs
    induction as generalizing bs with
    | nil => cases bs <;> simp [Galoistools.zipAddPad, Nat.mod_mod]
    | cons a as ih => cases bs <;> simp [Galoistools.zipAddPad, Nat.mod_mod, ih]
  have hmod : ∀ as bs : List Nat,
      List.map (fun x => x % p) (Galoistools.zipAddPad p as bs) = Galoistools.zipAddPad p as bs := by
    intro as bs
    induction as generalizing bs with
    | nil => cases bs <;> simp [Galoistools.zipAddPad, Nat.mod_mod]
    | cons a as ih => cases bs <;> simp [Galoistools.zipAddPad, Nat.mod_mod, ih]
  have hscalar : ∀ a b c : Nat,
      (((a%p+b%p)%p+c%p)%p) = ((a%p+(b%p+c%p)%p)%p) := by
    intro a b c
    calc
      (((a%p+b%p)%p+c%p)%p) = ((a+b+c)%p) := by rw [← Nat.add_mod a b p, ← Nat.add_mod (a+b) c p]
      _ = ((a+(b+c))%p) := by rw [Nat.add_assoc]
      _ = ((a%p+(b%p+c%p)%p)%p) := by rw [Nat.add_mod a (b+c) p, Nat.add_mod b c p]
  induction xs generalizing ys zs with
  | nil => cases ys <;> cases zs <;> simp [Galoistools.zipAddPad, hleft, hright, hmod]
  | cons x xs ih =>
    cases ys with
    | nil => cases zs <;> simp [Galoistools.zipAddPad, hleft, hright, hmod, ih]
    | cons y ys => cases zs <;> simp [Galoistools.zipAddPad, hleft, hright, hmod, hscalar, ih, Nat.add_assoc]

theorem gfAdd_assoc_exact_local (a b c : List Nat) (p : Nat) :
    Galoistools.gfAdd (Galoistools.gfAdd a b p) c p =
      Galoistools.gfAdd a (Galoistools.gfAdd b c p) p := by
  simp only [Galoistools.gfAdd]
  rw [show Galoistools.gfStrip (Galoistools.zipAddPad p a.reverse b.reverse).reverse =
      Galoistools.gfStrip ((Galoistools.zipAddPad p a.reverse b.reverse).reverse) by rfl]
  change Galoistools.gfAdd
      (Galoistools.gfStrip ((Galoistools.zipAddPad p a.reverse b.reverse).reverse)) c p =
    Galoistools.gfAdd a
      (Galoistools.gfStrip ((Galoistools.zipAddPad p b.reverse c.reverse).reverse)) p
  rw [gfAdd_strip_left_local p ((Galoistools.zipAddPad p a.reverse b.reverse).reverse) c]
  rw [gfAdd_strip_right_local p a ((Galoistools.zipAddPad p b.reverse c.reverse).reverse)]
  simp only [Galoistools.gfAdd, List.reverse_reverse]
  rw [zipAddPad_assoc_local]
'''

probes={
'strip_left': common,
'add_assoc_exact': common,
'add_sub_cancel_norm': common+r'''
theorem add_sub_cancel_norm (cur sub : List Nat) (p : Nat)
    (hp : 1 < p) (hcur : Galoistools.IsNorm p cur) :
    Galoistools.gfAdd (Galoistools.gfSub cur sub p) sub p = cur := by
  rw [sub_eq_add_neg_local cur sub p hp]
  rw [gfAdd_assoc_exact_local]
  rw [add_comm_local (Galoistools.gfNeg sub p) sub p]
  rw [add_neg_cancel_local sub p hp]
  have hstrip : Galoistools.gfStrip cur = cur := by
    have bridge : ∀ xs : List Nat, Galoistools.gfStrip xs = Galoistools.refGfStrip xs := by
      intro xs; induction xs with
      | nil => rfl
      | cons x xs ih => simp only [Galoistools.gfStrip, Galoistools.refGfStrip]; by_cases hx:x=0 <;> simp [hx,ih]
    rw [bridge]
    cases cur with
    | nil => rfl
    | cons x xs =>
      have hx : x ≠ 0 := by
        intro hz; subst x
        have ht : Galoistools.refGfTrunc p (0::xs) = 0::xs := hcur
        simp only [Galoistools.refGfTrunc, List.map_cons, Nat.zero_mod] at ht
        have nozero : ∀ as bs : List Nat, Galoistools.refGfStrip as ≠ 0::bs := by
          intro as bs; induction as with
          | nil => simp [Galoistools.refGfStrip]
          | cons y ys ih => simp only [Galoistools.refGfStrip]; by_cases hy:y=0 <;> simp [hy,ih]
        exact nozero (0 :: xs.map (fun z => z % p)) xs ht
      simp [Galoistools.refGfStrip, hx]
  simp [Galoistools.gfAdd, Galoistools.zipAddPad, hstrip]
'''
}

res=[]
for name,text in probes.items():
 p=out/f'Probe_{name}.lean'; p.write_text(header+text+footer)
 cp=subprocess.run(['lake','lean',p.name],cwd=out,text=True,capture_output=True)
 raw=cp.stdout+'\n'+cp.stderr; ls=raw.splitlines(); goals=[]
 for k,l in enumerate(ls):
  if '⊢ ' in l or l.startswith('case '): goals.append('\n'.join(ls[k:k+100]))
 item={'probe':name,'exit':cp.returncode,'errors':[l for l in ls if 'error:' in l or 'unknown identifier' in l][-12:],'residual':goals[-3:],'raw_tail':'\n'.join(ls[-400:]) if cp.returncode else ''}
 res.append(item); print('===',name,'EXIT',cp.returncode,'==='); print(item['raw_tail'] if cp.returncode else '')
Path('div_add_structure_v2').mkdir(exist_ok=True)
Path('div_add_structure_v2/census.json').write_text(json.dumps(res,indent=2))
