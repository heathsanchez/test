from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline27/allin_artifact.json').resolve())
out = Path('monic_mul_separator_v1/source').resolve()
create_sandbox(bench, out, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Ring
import Galoistools.Spec.Ring
\nnamespace GaloistoolsMonicMulSeparatorV1\n'''
footer = '\nend GaloistoolsMonicMulSeparatorV1\n'

probes = {
  'monic_mul_unfold': r'''
theorem monic_mul_unfold : Galoistools.spec_monic_mul_associate Galoistools.canonical := by
  simp only [Galoistools.spec_monic_mul_associate, Galoistools.canonical]
  intro f g p hp hnf hng hf hg
  cases f with
  | nil => contradiction
  | cons a as =>
      cases g with
      | nil => contradiction
      | cons b bs =>
          simp only [Galoistools.gfMonic]
          by_cases ha : a = 1
          · simp [ha]
          · by_cases hb : b = 1
            · simp [hb]
            · simp [ha, hb]
''',
  'monic_mul_using_lead': r'''
theorem monic_mul_using_lead : Galoistools.spec_monic_mul_associate Galoistools.canonical := by
  simp only [Galoistools.spec_monic_mul_associate, Galoistools.canonical]
  intro f g p hp hnf hng hf hg
  have hprod := GaloistoolsMulLeadingV1.reversed_convolve_lead_nonzero p f g hp hnf hng hf hg
  simp only [Galoistools.gfMul, hf, hg, false_or, if_false]
  rw [GaloistoolsMulLeadingV1.gfStrip_self_of_leadCoeff_ne _ hprod]
  cases f with
  | nil => contradiction
  | cons a as =>
      cases g with
      | nil => contradiction
      | cons b bs =>
          simp only [Galoistools.gfMonic]
          simp [Galoistools.leadCoeff]
'''
}

census=[]
for name,text in probes.items():
    p=out/f'Probe_{name}.lean'; p.write_text(header+text+footer)
    cp=subprocess.run(['lake','lean',p.name],cwd=out,text=True,capture_output=True)
    raw=cp.stdout+'\n'+cp.stderr; lines=raw.splitlines()
    errors=[x for x in lines if 'error:' in x or 'error(' in x or 'unknown identifier' in x]
    goals=[]
    for k,line in enumerate(lines):
        if '⊢ ' in line or line.startswith('case '): goals.append('\n'.join(lines[k:k+80]))
    item={'probe':name,'exit':cp.returncode,'errors':errors[-10:],'residual':goals[-3:],'raw_tail':'\n'.join(lines[-350:]) if cp.returncode else ''}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    if cp.returncode: print(item['raw_tail'])
Path('monic_mul_separator_v1').mkdir(exist_ok=True)
Path('monic_mul_separator_v1/census.json').write_text(json.dumps(census,indent=2))
