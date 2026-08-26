from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench_dir = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
source = Path('divcore_coeff/source').resolve()
create_sandbox(bench_dir, source, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

namespace GaloistoolsDivCoreCoeff
'''
footer = '\nend GaloistoolsDivCoreCoeff\n'

probes = {
'forall_reverse_inventory': r'''
#check List.Forall.reverse
#check List.reverse_mem
#check List.forall_mem
''',
'zipSubPad_all_lt': r'''
theorem zipSubPad_all_lt (p : Nat) (hp : 0 < p) : ∀ xs ys : List Nat,
    (Galoistools.zipSubPad p xs ys).Forall (fun z => z < p) := by
  intro xs
  induction xs with
  | nil =>
      intro ys
      induction ys with
      | nil => simp [Galoistools.zipSubPad]
      | cons y ys ih =>
          simp [Galoistools.zipSubPad, Nat.mod_lt _ hp, ih]
  | cons x xs ih =>
      intro ys
      cases ys with
      | nil =>
          induction xs with
          | nil => simp [Galoistools.zipSubPad, Nat.mod_lt _ hp]
          | cons a as iht =>
              simp [Galoistools.zipSubPad, Nat.mod_lt _ hp, iht]
      | cons y ys =>
          simp [Galoistools.zipSubPad, Nat.mod_lt _ hp, ih ys]
''',
'strip_lead_lt': r'''
theorem strip_lead_lt (p : Nat) (hp : 0 < p) : ∀ xs : List Nat,
    xs.Forall (fun z => z < p) → Galoistools.leadCoeff (Galoistools.gfStrip xs) < p := by
  intro xs
  induction xs with
  | nil => intro h; simpa [Galoistools.gfStrip, Galoistools.leadCoeff] using hp
  | cons a as ih =>
      intro h
      have ha : a < p := h.head
      have has : as.Forall (fun z => z < p) := h.tail
      by_cases hz : a = 0
      · simp [Galoistools.gfStrip, hz]
        exact ih has
      · simp [Galoistools.gfStrip, hz, Galoistools.leadCoeff, ha]
''',
'gfSub_lead_lt': r'''
theorem zipSubPad_all_lt_local (p : Nat) (hp : 0 < p) : ∀ xs ys : List Nat,
    (Galoistools.zipSubPad p xs ys).Forall (fun z => z < p) := by
  intro xs
  induction xs with
  | nil =>
      intro ys
      induction ys with
      | nil => simp [Galoistools.zipSubPad]
      | cons y ys ih => simp [Galoistools.zipSubPad, Nat.mod_lt _ hp, ih]
  | cons x xs ih =>
      intro ys
      cases ys with
      | nil =>
          simp [Galoistools.zipSubPad]
          exact List.forall_mem.2 (by intro z hz; obtain ⟨w, hw, rfl⟩ := List.mem_map.1 hz; exact Nat.mod_lt _ hp)
      | cons y ys => simp [Galoistools.zipSubPad, Nat.mod_lt _ hp, ih ys]

theorem strip_lead_lt_local (p : Nat) (hp : 0 < p) : ∀ xs : List Nat,
    xs.Forall (fun z => z < p) → Galoistools.leadCoeff (Galoistools.gfStrip xs) < p := by
  intro xs
  induction xs with
  | nil => intro h; simpa [Galoistools.gfStrip, Galoistools.leadCoeff] using hp
  | cons a as ih =>
      intro h
      by_cases hz : a = 0
      · simp [Galoistools.gfStrip, hz]
        exact ih h.tail
      · simp [Galoistools.gfStrip, hz, Galoistools.leadCoeff, h.head]

theorem gfSub_lead_lt (f g : List Nat) (p : Nat) (hp : 0 < p) :
    Galoistools.leadCoeff (Galoistools.gfSub f g p) < p := by
  unfold Galoistools.gfSub
  apply strip_lead_lt_local p hp
  apply List.Forall.reverse
  exact zipSubPad_all_lt_local p hp f.reverse g.reverse
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
        if '⊢ ' in line or line.startswith('case '): goals.append('\n'.join(lines[k:k+70]))
    item={'probe':name,'exit':cp.returncode,'errors':errors[-12:],'residual':goals[-3:],'raw_tail':'\n'.join(lines[-320:])}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    if cp.returncode: print(item['raw_tail'])

outdir=Path('divcore_coeff'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('DIVCORE_COEFF_CENSUS',json.dumps(census))
