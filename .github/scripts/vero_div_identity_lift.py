from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench_dir = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
source = Path('div_identity_lift/source').resolve()
create_sandbox(bench_dir, source, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

namespace GaloistoolsDivIdentityLift
'''
footer = '\nend GaloistoolsDivIdentityLift\n'

probes = {
'gfStrip_append_strip': r'''
theorem gfStrip_append_strip (xs ys : List Nat) :
    Galoistools.gfStrip (xs ++ ys) =
      Galoistools.gfStrip (Galoistools.gfStrip xs ++ ys) := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
      by_cases hx : x = 0
      · simp [Galoistools.gfStrip, hx, ih]
      · simp [Galoistools.gfStrip, hx]
''',
'strip_zipAddPad_append_zero': r'''
theorem strip_zipAddPad_append_zero (p : Nat) (as bs : List Nat) :
    Galoistools.gfStrip (Galoistools.zipAddPad p as bs).reverse =
      Galoistools.gfStrip (Galoistools.zipAddPad p as (bs ++ [0])).reverse := by
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
  | nil =>
      simp [Galoistools.zipAddPad, Galoistools.gfStrip, List.map_append]
  | cons a as ih =>
      cases bs with
      | nil =>
          simp [Galoistools.zipAddPad, hnil]
      | cons b bs =>
          simp only [Galoistools.zipAddPad, List.reverse_cons]
          calc
            Galoistools.gfStrip ((Galoistools.zipAddPad p as bs).reverse ++ [(a + b) % p]) =
                Galoistools.gfStrip (Galoistools.gfStrip (Galoistools.zipAddPad p as bs).reverse ++ [(a + b) % p]) :=
              hstrip _ _
            _ = Galoistools.gfStrip (Galoistools.gfStrip (Galoistools.zipAddPad p as (bs ++ [0])).reverse ++ [(a + b) % p]) := by
              rw [ih bs]
            _ = Galoistools.gfStrip ((Galoistools.zipAddPad p as (bs ++ [0])).reverse ++ [(a + b) % p]) :=
              (hstrip _ _).symm
            _ = Galoistools.gfStrip (Galoistools.zipAddPad p (a :: as) ((b :: bs) ++ [0])).reverse := by
              simp [Galoistools.zipAddPad]
''',
'gfAdd_strip_right': r'''
theorem gfAdd_strip_right (p : Nat) (a b : List Nat) :
    Galoistools.gfAdd a (Galoistools.gfStrip b) p =
      Galoistools.gfAdd a b p := by
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
    | nil =>
        simp [Galoistools.zipAddPad, Galoistools.gfStrip, List.map_append]
    | cons x xs ih =>
        cases bs with
        | nil =>
            simp [Galoistools.zipAddPad, hnil]
        | cons y ys =>
            simp only [Galoistools.zipAddPad, List.reverse_cons]
            calc
              Galoistools.gfStrip ((Galoistools.zipAddPad p xs ys).reverse ++ [(x + y) % p]) =
                  Galoistools.gfStrip (Galoistools.gfStrip (Galoistools.zipAddPad p xs ys).reverse ++ [(x + y) % p]) := hstrip _ _
              _ = Galoistools.gfStrip (Galoistools.gfStrip (Galoistools.zipAddPad p xs (ys ++ [0])).reverse ++ [(x + y) % p]) := by rw [ih ys]
              _ = Galoistools.gfStrip ((Galoistools.zipAddPad p xs (ys ++ [0])).reverse ++ [(x + y) % p]) := (hstrip _ _).symm
              _ = Galoistools.gfStrip (Galoistools.zipAddPad p (x :: xs) ((y :: ys) ++ [0])).reverse := by
                simp [Galoistools.zipAddPad]
  induction b with
  | nil => rfl
  | cons x xs ih =>
      by_cases hx : x = 0
      · simp only [Galoistools.gfStrip, hx, if_pos]
        rw [ih]
        simp only [Galoistools.gfAdd, List.reverse_cons]
        exact hzero a.reverse xs.reverse
      · simp [Galoistools.gfStrip, hx]
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

outdir=Path('div_identity_lift'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('DIV_IDENTITY_LIFT_CENSUS',json.dumps(census))
