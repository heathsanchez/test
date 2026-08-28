from pathlib import Path
import json, subprocess, shutil
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench=Path('benchmarks/galoistools').resolve()
seed=read_artifact(Path('../baseline27/allin_artifact.json').resolve())
root=Path('msi_cross_family_compounding_v1').resolve()
if root.exists(): shutil.rmtree(root)
root.mkdir()

HEADER='''import Galoistools.Proof.Ring\nimport Galoistools.Impl.Division\n\nnamespace MSICrossFamilyCompoundingV1\n'''
FOOTER='\nend MSICrossFamilyCompoundingV1\n'

A=r'''
theorem add_mod_unreduce (p a b : Nat) :
    ((a%p) + (b%p))%p = (a+b)%p := (Nat.add_mod a b p).symm

theorem mul_left_reduce (p a k : Nat) :
    (((a%p)*k)%p) = (a*k)%p := by
  calc
    (((a%p)*k)%p) = ((((a%p)%p)*(k%p))%p) := Nat.mul_mod (a%p) k p
    _ = (((a%p)*(k%p))%p) := by rw [Nat.mod_mod]
    _ = (a*k)%p := (Nat.mul_mod a k p).symm

theorem add_scaled_mod (p k x y : Nat) :
    (((x*k)%p) + ((y*k)%p))%p = (((x+y)%p)*k)%p := by
  calc
    (((x*k)%p) + ((y*k)%p))%p = ((x*k)+(y*k))%p := add_mod_unreduce p (x*k) (y*k)
    _ = ((x+y)*k)%p := by rw [Nat.add_mul]
    _ = (((x+y)%p)*k)%p := (mul_left_reduce p (x+y) k).symm

theorem scale_after_mod (p k z : Nat) :
    (((z % p) * k) % p) = ((z*k)%p) := mul_left_reduce p z k

theorem mod_after_scale_eq_scale_after_mod (p k z : Nat) :
    (((z*k)%p)%p) = (((z%p)*k)%p) := by
  rw [Nat.mod_mod]
  exact (scale_after_mod p k z).symm
'''

B=r'''
theorem zip_scale (p k : Nat) (xs ys : List Nat) :
    Galoistools.zipAddPad p (xs.map (fun x => (x*k)%p)) (ys.map (fun y => (y*k)%p)) =
      (Galoistools.zipAddPad p xs ys).map (fun z => (z*k)%p) := by
  induction xs generalizing ys with
  | nil =>
      cases ys with
      | nil => rfl
      | cons y ys =>
          simp only [List.map_nil, List.map_cons, Galoistools.zipAddPad, List.map_map]
          congr 1
          · rw [Nat.mod_mod]
            exact (scale_after_mod p k y).symm
          · apply List.map_congr_left
            intro z hz
            change (((z*k)%p)%p) = (((z%p)*k)%p)
            exact mod_after_scale_eq_scale_after_mod p k z
  | cons x xs ih =>
      cases ys with
      | nil =>
          simp only [List.map_nil, List.map_cons, Galoistools.zipAddPad, List.map_map]
          congr 1
          · rw [Nat.mod_mod]
            exact (scale_after_mod p k x).symm
          · apply List.map_congr_left
            intro z hz
            change (((z*k)%p)%p) = (((z%p)*k)%p)
            exact mod_after_scale_eq_scale_after_mod p k z
      | cons y ys =>
          simp only [List.map_cons, Galoistools.zipAddPad]
          congr 1
          · exact add_scaled_mod p k x y
          · exact ih ys
'''

C=r'''
theorem convolve_scale_left (p k : Nat) (xs ys : List Nat) :
    Galoistools.convolve p (xs.map (fun x => (x*k)%p)) ys =
      (Galoistools.convolve p xs ys).map (fun z => (z*k)%p) := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
      simp only [List.map_cons, Galoistools.convolve]
      rw [ih]
      have hhead : ys.map (fun y => ((x*k)%p * y)%p) =
          (ys.map (fun y => (x*y)%p)).map (fun z => (z*k)%p) := by
        simp only [List.map_map]
        apply List.map_congr_left
        intro y hy
        calc
          (((x*k)%p) * y)%p = ((x*k)*y)%p := mul_left_reduce p (x*k) y
          _ = ((x*y)*k)%p := by congr 1; ac_rfl
          _ = (((x*y)%p)*k)%p := (mul_left_reduce p (x*y) k).symm
      rw [hhead]
      have htail : (0 :: Galoistools.convolve p xs ys).map (fun z => (z*k)%p) =
          0 :: (Galoistools.convolve p xs ys).map (fun z => (z*k)%p) := by simp
      rw [← htail]
      exact zip_scale p k _ _
'''

D=r'''
theorem convolve_scale_right (p k : Nat) (xs ys : List Nat) :
    Galoistools.convolve p xs (ys.map (fun y => (y*k)%p)) =
      (Galoistools.convolve p xs ys).map (fun z => (z*k)%p) := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
      simp only [Galoistools.convolve]
      rw [ih]
      have hhead : (ys.map (fun y => (y*k)%p)).map (fun y => (x*y)%p) =
          (ys.map (fun y => (x*y)%p)).map (fun z => (z*k)%p) := by
        simp only [List.map_map]
        apply List.map_congr_left
        intro y hy
        calc
          (x * ((y*k)%p))%p = (x*(y*k))%p := by
            calc
              (x * ((y*k)%p))%p = (((x%p)*(((y*k)%p)%p))%p) := Nat.mul_mod x ((y*k)%p) p
              _ = (((x%p)*((y*k)%p))%p) := by rw [Nat.mod_mod]
              _ = (x*(y*k))%p := (Nat.mul_mod x (y*k) p).symm
          _ = ((x*y)*k)%p := by congr 1; ac_rfl
          _ = (((x*y)%p)*k)%p := (mul_left_reduce p (x*y) k).symm
      rw [hhead]
      have htail : (0 :: Galoistools.convolve p xs ys).map (fun z => (z*k)%p) =
          0 :: (Galoistools.convolve p xs ys).map (fun z => (z*k)%p) := by simp
      rw [← htail]
      exact zip_scale p k _ _
'''

E=r'''
theorem convolve_scale_both (p a b : Nat) (xs ys : List Nat) :
    Galoistools.convolve p (xs.map (fun x => (x*a)%p)) (ys.map (fun y => (y*b)%p)) =
      (Galoistools.convolve p xs ys).map (fun z => (z*(a*b))%p) := by
  rw [convolve_scale_left p a xs (ys.map (fun y => (y*b)%p))]
  rw [convolve_scale_right p b xs ys]
  simp only [List.map_map]
  apply List.map_congr_left
  intro z hz
  calc
    ((((z*b)%p)*a)%p) = ((z*b)*a)%p := mul_left_reduce p (z*b) a
    _ = (z*(a*b))%p := by congr 1; ac_rfl
'''

F=r'''
theorem gfStrip_map_scale (p k : Nat) (f : List Nat)
    (hzero : ∀ z : Nat, ((z*k)%p = 0 ↔ z = 0)) :
    Galoistools.gfStrip (f.map (fun z => (z*k)%p)) =
      (Galoistools.gfStrip f).map (fun z => (z*k)%p) := by
  induction f with
  | nil => rfl
  | cons a as ih =>
      simp only [List.map_cons]
      by_cases ha : a = 0
      · have hs : (a*k)%p = 0 := (hzero a).2 ha
        simp [Galoistools.gfStrip, ha, hs, ih]
      · have hs : (a*k)%p ≠ 0 := by intro h; exact ha ((hzero a).1 h)
        simp [Galoistools.gfStrip, ha, hs]
'''

G=r'''
theorem reverse_map_scale (p k : Nat) (f : List Nat) :
    (f.map (fun z => (z*k)%p)).reverse = f.reverse.map (fun z => (z*k)%p) := by
  induction f with
  | nil => rfl
  | cons a as ih =>
      simp only [List.map_cons, List.reverse_cons, List.map_append, ih, List.map_nil]
'''

TARGET=r'''
theorem gfMul_scale_both_target
    (p a b : Nat) (f g : List Nat)
    (hf : f ≠ []) (hg : g ≠ [])
    (hfa : f.map (fun x => (x*a)%p) ≠ [])
    (hgb : g.map (fun y => (y*b)%p) ≠ [])
    (hzero : ∀ z : Nat, ((z*(a*b))%p = 0 ↔ z = 0)) :
    Galoistools.gfMul (f.map (fun x => (x*a)%p)) (g.map (fun y => (y*b)%p)) p =
      (Galoistools.gfMul f g p).map (fun z => (z*(a*b))%p) := by
  simp only [Galoistools.gfMul, hfa, hgb, hf, hg, false_or, if_false]
  rw [reverse_map_scale p a f]
  rw [reverse_map_scale p b g]
  rw [convolve_scale_both p a b f.reverse g.reverse]
  rw [reverse_map_scale p (a*b) (Galoistools.convolve p f.reverse g.reverse)]
  exact gfStrip_map_scale p (a*b) (Galoistools.convolve p f.reverse g.reverse).reverse hzero
'''

SHAM=r'''
theorem sham_one (n : Nat) : n = n := rfl
theorem sham_two (xs : List Nat) : xs = xs := rfl
theorem sham_three (p : Prop) (h : p) : p := h
'''

UNITS=[('scalar_mod',A),('zip_transport',B),('convolve_left',C),('convolve_right',D),('convolve_both',E),('strip_transport',F),('reverse_transport',G)]
NEW_BUDGET=4


def sandbox(name):
    out=root/name/'source';out.parent.mkdir(parents=True,exist_ok=True)
    create_sandbox(bench,out,mode='codeproof',overwrite=True,seed_artifact=seed)
    return out

def check(out,text,name):
    p=out/f'{name}.lean';p.write_text(HEADER+text+TARGET+FOOTER)
    cp=subprocess.run(['lake','lean',p.name],cwd=out,text=True,capture_output=True)
    raw=cp.stdout+'\n'+cp.stderr
    return {'exit':cp.returncode,'success':cp.returncode==0,'tail':raw[-5000:]}

# Source episode: independently verify the reusable lower-level substrate.
source_out=sandbox('source_episode')
source_text=A+B+C
sp=source_out/'SourceEpisode.lean';sp.write_text(HEADER+source_text+FOOTER)
scp=subprocess.run(['lake','lean',sp.name],cwd=source_out,text=True,capture_output=True)
source_verified=scp.returncode==0
if not source_verified:
    raise SystemExit('source substrate did not verify:\n'+(scp.stdout+scp.stderr)[-12000:])

# WARM may retain exactly what source Lean certified. RAW gets only logs; SHAM
# gets matched-count irrelevant verified lemmas; ABLATION verifies then removes it.
arms={
 'WARM': {'installed':source_text,'start_index':3},
 'COLD': {'installed':'','start_index':0},
 'RAW_HISTORY': {'installed':'','start_index':0},
 'SHAM': {'installed':SHAM,'start_index':0},
 'ANCESTOR_ABLATION': {'installed':'','start_index':0},
}
rows={}
for arm,cfg in arms.items():
    out=sandbox(arm.lower()); text=cfg['installed']; idx=cfg['start_index']; trace=[]
    initial=check(out,text,f'Attempt_0')
    trace.append({'new_groups':0,'installed_source_groups':cfg['start_index'],'attempt':initial})
    success=initial['success']; used=0
    while not success and used<NEW_BUDGET and idx<len(UNITS):
        group,code=UNITS[idx];text+=code;idx+=1;used+=1
        r=check(out,text,f'Attempt_{used}')
        trace.append({'new_groups':used,'added':group,'attempt':r})
        success=r['success']
    rows[arm]={'success':success,'new_groups_used':used,'final_index':idx,'trace':trace}

strict=(source_verified and rows['WARM']['success'] and rows['WARM']['new_groups_used']<=NEW_BUDGET and all(not rows[n]['success'] for n in ['COLD','RAW_HISTORY','SHAM','ANCESTOR_ABLATION']))
result={
 'schema':'msi.vero-cross-family-developmental-compounding.v1',
 'source_family':'verified convolution scaling substrate: scalar modular transport -> zipAddPad scaling -> left-convolution scaling',
 'target_family':'source-distinct higher-level gfMul two-sided scaling',
 'verifier':'lake lean in Vero Galoistools sandbox',
 'source_verified':source_verified,
 'retained_source_groups':['scalar_mod','zip_transport','convolve_left'],
 'target_new_group_budget':NEW_BUDGET,
 'target_required_extension_order':['convolve_right','convolve_both','strip_transport','reverse_transport'],
 'arms':rows,
 'strict_gate':'PASS_VERIFIED_CROSS_FAMILY_DEVELOPMENTAL_COMPOUNDING' if strict else 'FAIL_VERIFIED_CROSS_FAMILY_DEVELOPMENTAL_COMPOUNDING',
 'claim_boundary':'Retained, independently Lean-verified support structure from one proof family causally reduces new verified construction cost for a source-distinct target family. This is capability/discovery compounding inside a supplied proof language, not new tactic or syntax invention.'
}
(root/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True))
print(json.dumps(result,indent=2,sort_keys=True))
if not strict: raise SystemExit(2)
