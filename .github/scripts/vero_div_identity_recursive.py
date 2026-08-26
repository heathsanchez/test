from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench_dir = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
source = Path('div_identity_recursive/source').resolve()
create_sandbox(bench_dir, source, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

namespace GaloistoolsDivIdentityRecursive
'''
footer = '\nend GaloistoolsDivIdentityRecursive\n'

probes = {
'zipAddPad_mod_left': r'''
theorem zipAddPad_mod_left (p : Nat) (xs ys : List Nat) :
    Galoistools.zipAddPad p (List.map (fun x => x % p) xs) ys =
      Galoistools.zipAddPad p xs ys := by
  induction xs generalizing ys with
  | nil =>
      cases ys <;> simp [Galoistools.zipAddPad, Nat.mod_mod]
  | cons x xs ih =>
      cases ys with
      | nil => simp [Galoistools.zipAddPad, Nat.mod_mod]
      | cons y ys => simp [Galoistools.zipAddPad, Nat.mod_mod, ih]
''',
'zipAddPad_mod_right': r'''
theorem zipAddPad_mod_right (p : Nat) (xs ys : List Nat) :
    Galoistools.zipAddPad p xs (List.map (fun y => y % p) ys) =
      Galoistools.zipAddPad p xs ys := by
  induction xs generalizing ys with
  | nil =>
      cases ys <;> simp [Galoistools.zipAddPad, Nat.mod_mod]
  | cons x xs ih =>
      cases ys with
      | nil => simp [Galoistools.zipAddPad, Nat.mod_mod]
      | cons y ys => simp [Galoistools.zipAddPad, Nat.mod_mod, ih]
''',
'mod_add_assoc': r'''
theorem mod_add_assoc (p a b c : Nat) :
    (((a % p + b % p) % p + c % p) % p) =
      ((a % p + (b % p + c % p) % p) % p) := by
  calc
    (((a % p + b % p) % p + c % p) % p) = ((a + b + c) % p) := by
      rw [← Nat.add_mod a b p]
      rw [← Nat.add_mod (a + b) c p]
    _ = ((a + (b + c)) % p) := by rw [Nat.add_assoc]
    _ = ((a % p + (b % p + c % p) % p) % p) := by
      rw [Nat.add_mod a (b + c) p]
      rw [Nat.add_mod b c p]
''',
'zipAddPad_assoc': r'''
theorem zipAddPad_assoc (p : Nat) (xs ys zs : List Nat) :
    Galoistools.zipAddPad p (Galoistools.zipAddPad p xs ys) zs =
      Galoistools.zipAddPad p xs (Galoistools.zipAddPad p ys zs) := by
  have hleft : ∀ as bs : List Nat,
      Galoistools.zipAddPad p (List.map (fun x => x % p) as) bs =
        Galoistools.zipAddPad p as bs := by
    intro as bs
    induction as generalizing bs with
    | nil => cases bs <;> simp [Galoistools.zipAddPad, Nat.mod_mod]
    | cons a as ih =>
        cases bs with
        | nil => simp [Galoistools.zipAddPad, Nat.mod_mod]
        | cons b bs => simp [Galoistools.zipAddPad, Nat.mod_mod, ih]
  have hright : ∀ as bs : List Nat,
      Galoistools.zipAddPad p as (List.map (fun x => x % p) bs) =
        Galoistools.zipAddPad p as bs := by
    intro as bs
    induction as generalizing bs with
    | nil => cases bs <;> simp [Galoistools.zipAddPad, Nat.mod_mod]
    | cons a as ih =>
        cases bs with
        | nil => simp [Galoistools.zipAddPad, Nat.mod_mod]
        | cons b bs => simp [Galoistools.zipAddPad, Nat.mod_mod, ih]
  have hmod : ∀ as bs : List Nat,
      List.map (fun x => x % p) (Galoistools.zipAddPad p as bs) =
        Galoistools.zipAddPad p as bs := by
    intro as bs
    induction as generalizing bs with
    | nil =>
        cases bs <;> simp [Galoistools.zipAddPad, Nat.mod_mod]
    | cons a as ih =>
        cases bs with
        | nil => simp [Galoistools.zipAddPad, Nat.mod_mod]
        | cons b bs => simp [Galoistools.zipAddPad, Nat.mod_mod, ih]
  have hscalar : ∀ a b c : Nat,
      (((a % p + b % p) % p + c % p) % p) =
        ((a % p + (b % p + c % p) % p) % p) := by
    intro a b c
    calc
      (((a % p + b % p) % p + c % p) % p) = ((a + b + c) % p) := by
        rw [← Nat.add_mod a b p]
        rw [← Nat.add_mod (a + b) c p]
      _ = ((a + (b + c)) % p) := by rw [Nat.add_assoc]
      _ = ((a % p + (b % p + c % p) % p) % p) := by
        rw [Nat.add_mod a (b + c) p]
        rw [Nat.add_mod b c p]
  induction xs generalizing ys zs with
  | nil =>
      cases ys <;> cases zs <;>
        simp [Galoistools.zipAddPad, hleft, hright, hmod]
  | cons x xs ih =>
      cases ys with
      | nil =>
          cases zs <;>
            simp [Galoistools.zipAddPad, hleft, hright, hmod, ih]
      | cons y ys =>
          cases zs <;>
            simp [Galoistools.zipAddPad, hleft, hright, hmod, hscalar, ih, Nat.add_assoc]
'''
}

census=[]
for name, text in probes.items():
    probe=source/f'Probe_{name}.lean'
    probe.write_text(header+text+footer)
    cp=subprocess.run(['lake','lean',probe.name],cwd=source,text=True,capture_output=True)
    raw=cp.stdout+'\n'+cp.stderr
    lines=raw.splitlines()
    errors=[x for x in lines if 'error:' in x or 'error(' in x or 'unknown identifier' in x]
    goals=[]
    for k,line in enumerate(lines):
        if '⊢ ' in line or line.startswith('case '): goals.append('\n'.join(lines[k:k+100]))
    item={'probe':name,'exit':cp.returncode,'errors':errors[-12:],'residual':goals[-3:],'raw_tail':'\n'.join(lines[-440:]) if cp.returncode else ''}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    if cp.returncode: print(item['raw_tail'])

outdir=Path('div_identity_recursive'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('DIV_IDENTITY_RECURSIVE_CENSUS',json.dumps(census))
