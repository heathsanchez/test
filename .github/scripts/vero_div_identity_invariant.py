from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench_dir = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
source = Path('div_identity_invariant/source').resolve()
create_sandbox(bench_dir, source, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

namespace GaloistoolsDivIdentityInvariant
'''
footer = '\nend GaloistoolsDivIdentityInvariant\n'

probes = {
'shift_singleton_shape': r'''
theorem shift_singleton_shape (s c : Nat) :
    Galoistools.shiftUp s [c] = [c] ++ List.replicate s 0 := by
  simp [Galoistools.shiftUp]
''',
'quotient_term_mul': r'''
theorem quotient_term_mul (p c s : Nat) (g : List Nat) :
    Galoistools.gfMul (Galoistools.shiftUp s [c]) g p =
      Galoistools.shiftUp s (Galoistools.scaleP p c g) := by
  simp [Galoistools.shiftUp, Galoistools.scaleP, Galoistools.gfMul,
    Galoistools.convolve, Galoistools.zipAddPad, Galoistools.gfStrip]
''',
'completed_prefix_shape': r'''
theorem completed_prefix_shape (q : List Nat) (e s : Int) (c : Nat)
    (hs0 : 0 <= s) (hse : s <= e) :
    let oldQ := q ++ List.replicate (e + 1).toNat 0
    let gap := List.replicate (e - s).toNat 0
    let newQ := q ++ gap ++ [c] ++ List.replicate s.toNat 0
    oldQ.length = newQ.length := by
  simp [Int.toNat_of_nonneg hs0]
  omega
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
        if '⊢ ' in line or line.startswith('case '): goals.append('\n'.join(lines[k:k+120]))
    item={'probe':name,'exit':cp.returncode,'errors':errors[-12:],'residual':goals[-3:],'raw_tail':'\n'.join(lines[-500:]) if cp.returncode else ''}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    if cp.returncode: print(item['raw_tail'])

outdir=Path('div_identity_invariant'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('DIV_IDENTITY_INVARIANT_CENSUS',json.dumps(census))
