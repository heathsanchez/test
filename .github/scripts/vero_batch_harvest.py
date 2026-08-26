from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench_dir = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
source = Path('batch_harvest/source').resolve()
create_sandbox(bench_dir, source, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

namespace GaloistoolsBatch
'''
footer = '\nend GaloistoolsBatch\n'

common = r'''
theorem egcd_second_step (n : Nat) :
    (Galoistools.egcdInt (n + 3) (Int.ofNat (n + 2)) 1).2.2 = 1 := by
  simp [Galoistools.egcdInt]
'''

probes = {
'egcd_compose': common + r'''
theorem egcd_one_shape (n : Nat) :
    (Galoistools.egcdInt (n + 4) 1 (Int.ofNat (n + 2))).2.1 = 1 := by
  rw [Galoistools.egcdInt]
  have hp0 : (Int.ofNat (n + 2)) ≠ 0 := by omega
  simp only [hp0, if_false]
  have hmod : (1 : Int) % (Int.ofNat (n + 2)) = 1 := by omega
  rw [hmod]
  exact egcd_second_step n
''',
'inv_one_from_shape': common + r'''
theorem egcd_one_shape (n : Nat) :
    (Galoistools.egcdInt (n + 4) 1 (Int.ofNat (n + 2))).2.1 = 1 := by
  rw [Galoistools.egcdInt]
  have hp0 : (Int.ofNat (n + 2)) ≠ 0 := by omega
  simp only [hp0, if_false]
  have hmod : (1 : Int) % (Int.ofNat (n + 2)) = 1 := by omega
  rw [hmod]
  exact egcd_second_step n

theorem invMod_one (n : Nat) : Galoistools.invMod 1 (n + 2) % (n + 2) = 1 := by
  unfold Galoistools.invMod
  have hnmod : 1 % (n + 2) = 1 := by omega
  rw [hnmod]
  have hs := egcd_one_shape n
  rw [hs]
  omega
''',
'inv_one_general': common + r'''
theorem egcd_one_shape (n : Nat) :
    (Galoistools.egcdInt (n + 4) 1 (Int.ofNat (n + 2))).2.1 = 1 := by
  rw [Galoistools.egcdInt]
  have hp0 : (Int.ofNat (n + 2)) ≠ 0 := by omega
  simp only [hp0, if_false]
  have hmod : (1 : Int) % (Int.ofNat (n + 2)) = 1 := by omega
  rw [hmod]
  exact egcd_second_step n

theorem invMod_one_exact (n : Nat) : Galoistools.invMod 1 (n + 2) % (n + 2) = 1 := by
  unfold Galoistools.invMod
  have hnmod : 1 % (n + 2) = 1 := by omega
  rw [hnmod]
  have hs := egcd_one_shape n
  rw [hs]
  omega

example (p : Nat) (hp : 1 < p) : Galoistools.invMod 1 p % p = 1 := by
  cases p with
  | zero => simp at hp
  | succ p =>
    cases p with
    | zero => simp at hp
    | succ n =>
      simpa [Nat.add_assoc] using invMod_one_exact n
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
        if '⊢ ' in line or line.startswith('case '): goals.append('\n'.join(lines[k:k+32]))
    item={'probe':name,'exit':cp.returncode,'errors':errors[-12:],'residual':goals[-3:],'raw_tail':'\n'.join(lines[-160:]) if cp.returncode else ''}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    for e in errors[-12:]: print(e)
    for g in goals[-3:]: print(g)
    if cp.returncode: print(item['raw_tail'])

outdir=Path('batch_harvest'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('BATCH_CENSUS',json.dumps(census))
