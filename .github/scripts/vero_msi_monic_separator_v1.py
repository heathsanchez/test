from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline27/allin_artifact.json').resolve())
out = Path('msi_monic_separator_v6/source').resolve()
create_sandbox(bench, out, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Division

namespace GaloistoolsMSIMonicSeparatorV6
'''
footer = '\nend GaloistoolsMSIMonicSeparatorV6\n'

scalar = r'''
theorem mul_mod_right_modeq (p x c d : Nat) (h : c % p = d % p) :
    (x*c)%p = (x*d)%p := by
  calc
    (x*c)%p = ((x%p)*(c%p))%p := Nat.mul_mod x c p
    _ = ((x%p)*(d%p))%p := by rw [h]
    _ = (x*d)%p := (Nat.mul_mod x d p).symm

theorem add_mod_unreduce (p a b : Nat) :
    ((a%p) + (b%p))%p = (a+b)%p :=
  (Nat.add_mod a b p).symm

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

zip = r'''
theorem zip_scale (p k : Nat) (xs ys : List Nat) :
    Galoistools.zipAddPad p
      (xs.map (fun x => (x*k)%p))
      (ys.map (fun y => (y*k)%p)) =
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

convolve = r'''
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
          _ = ((x*y)*k)%p := by
            congr 1
            ac_rfl
          _ = (((x*y)%p)*k)%p := (mul_left_reduce p (x*y) k).symm
      rw [hhead]
      have htail : (0 :: Galoistools.convolve p xs ys).map (fun z => (z*k)%p) =
          0 :: (Galoistools.convolve p xs ys).map (fun z => (z*k)%p) := by
        simp only [List.map_cons, Nat.zero_mul, Nat.zero_mod]
      rw [← htail]
      exact zip_scale p k _ _
'''

probes = {
  'scalar_kernel': scalar,
  'scale_modeq_exact': scalar + r'''
theorem scale_modeq_exact (p c d : Nat) (f : List Nat)
    (h : NatModEq p c d) :
    Galoistools.scaleP p c f = Galoistools.scaleP p d f := by
  unfold Galoistools.scaleP
  congr 1
  apply List.map_congr_left
  intro x hx
  unfold NatModEq at h
  exact mul_mod_right_modeq p x c d h
''',
  'zip_scale': scalar + zip,
  'convolve_scale_left': scalar + zip + convolve,
}

census=[]
for name,text in probes.items():
    q=out/f'Probe_{name}.lean'; q.write_text(header+text+footer)
    cp=subprocess.run(['lake','lean',q.name],cwd=out,text=True,capture_output=True)
    raw=cp.stdout+'\n'+cp.stderr; lines=raw.splitlines()
    errors=[x for x in lines if 'error:' in x or 'error(' in x or 'unknown identifier' in x]
    goals=[]
    for k,line in enumerate(lines):
        if '⊢ ' in line or line.startswith('case '): goals.append('\n'.join(lines[k:k+120]))
    item={'probe':name,'exit':cp.returncode,'errors':errors[-12:],'residual':goals[-3:],'tail':'\n'.join(lines[-420:]) if cp.returncode else ''}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    if cp.returncode: print(item['tail'])
Path('msi_monic_separator_v6').mkdir(exist_ok=True)
Path('msi_monic_separator_v6/census.json').write_text(json.dumps(census,indent=2))
print('MSI_MONIC_SEPARATOR_V6', json.dumps([{'probe':x['probe'],'exit':x['exit']} for x in census]))
