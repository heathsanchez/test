from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline27/allin_artifact.json').resolve())
out = Path('msi_gfstrip_separator_v2/source').resolve()
create_sandbox(bench, out, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Division

namespace GaloistoolsMSIGfStripSeparatorV2
'''
footer = '\nend GaloistoolsMSIGfStripSeparatorV2\n'

core = r'''
theorem gfStrip_map_scale
    (p k : Nat) (f : List Nat)
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
      · have hs : (a*k)%p ≠ 0 := by
          intro h
          exact ha ((hzero a).1 h)
        simp [Galoistools.gfStrip, ha, hs]
'''

reverse = core + r'''
theorem reverse_map_scale (p k : Nat) (f : List Nat) :
    (f.map (fun z => (z*k)%p)).reverse =
      f.reverse.map (fun z => (z*k)%p) := by
  induction f with
  | nil => rfl
  | cons a as ih =>
      simp only [List.map_cons, List.reverse_cons, List.map_append, ih]
'''

probes = {
  'gfstrip_map_scale': core,
  'reverse_map_scale': reverse,
}

census=[]
for name,text in probes.items():
    q=out/f'Probe_{name}.lean'; q.write_text(header+text+footer)
    cp=subprocess.run(['lake','lean',q.name],cwd=out,text=True,capture_output=True)
    raw=cp.stdout+'\n'+cp.stderr; lines=raw.splitlines()
    errors=[x for x in lines if 'error:' in x or 'error(' in x or 'unknown identifier' in x]
    goals=[]
    for i,line in enumerate(lines):
        if '⊢ ' in line or line.startswith('case '): goals.append('\n'.join(lines[i:i+120]))
    item={'probe':name,'exit':cp.returncode,'errors':errors[-12:],'residual':goals[-3:],'tail':'\n'.join(lines[-420:]) if cp.returncode else ''}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    if cp.returncode: print(item['tail'])
Path('msi_gfstrip_separator_v2').mkdir(exist_ok=True)
Path('msi_gfstrip_separator_v2/census.json').write_text(json.dumps(census,indent=2))
print('MSI_GFSTRIP_SEPARATOR_V2', json.dumps([{'probe':x['probe'],'exit':x['exit']} for x in census]))
