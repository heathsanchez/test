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

probes = {
'sub_self': r'''
theorem probe_sub_self (f : List Nat) (p : Nat) (hp : 1 < p) :
    Galoistools.gfSub f f p = [] := by
  unfold Galoistools.gfSub
  rw [Galoistools.Proof.zipSubPad_eq_add_neg]
  rw [Galoistools.Proof.zipAddPad_neg_self p hp]
  simp [Galoistools.Proof.gfStrip_map_zero]
''',
'norm_impl_identity': r'''
theorem probe_norm_impl_identity (f : List Nat) (p : Nat)
    (hf : Galoistools.IsNorm p f) :
    Galoistools.gfStrip (f.map (fun a => a % p)) = f := by
  unfold Galoistools.IsNorm Galoistools.refGfTrunc at hf
  rw [Galoistools.Proof.ring_gfStrip_eq_ref]
  exact hf
''',
'rem_self': r'''
theorem probe_sub_self (f : List Nat) (p : Nat) (hp : 1 < p) :
    Galoistools.gfSub f f p = [] := by
  unfold Galoistools.gfSub
  rw [Galoistools.Proof.zipSubPad_eq_add_neg]
  rw [Galoistools.Proof.zipAddPad_neg_self p hp]
  simp [Galoistools.Proof.gfStrip_map_zero]

theorem probe_norm_impl_identity (f : List Nat) (p : Nat)
    (hf : Galoistools.IsNorm p f) :
    Galoistools.gfStrip (f.map (fun a => a % p)) = f := by
  unfold Galoistools.IsNorm Galoistools.refGfTrunc at hf
  rw [Galoistools.Proof.ring_gfStrip_eq_ref]
  exact hf

theorem probe_rem_self (f : List Nat) (p : Nat)
    (hp : Galoistools.PrimeField p) (hf : Galoistools.IsNorm p f)
    (hinv : (Galoistools.leadCoeff f * Galoistools.invMod (Galoistools.leadCoeff f) p) % p = 1) :
    Galoistools.gfRem f f p = [] := by
  have hp1 : 1 < p := hp.1
  have hnorm := probe_norm_impl_identity f p hf
  have hsub := probe_sub_self f p hp1
  unfold Galoistools.gfRem Galoistools.gfDiv
  by_cases hz : f = []
  · simp [hz]
  · simp [hz]
    simp only [Galoistools.divCore]
    rw [hnorm]
    simp only [lt_self_iff_false, if_false, sub_self, Int.toNat_zero,
      List.replicate_zero, List.append_nil, hinv]
    simp [Galoistools.shiftUp, Galoistools.scaleP, hnorm, hsub]
''',
'gcd_self_from_rem': r'''
theorem probe_gcdloop_zero_right (p fuel : Nat) (f : List Nat) :
    Galoistools.gcdLoop p fuel f [] = f := by
  cases fuel with
  | zero => rfl
  | succ n => simp [Galoistools.gcdLoop]

theorem probe_gcd_self_from_rem (f : List Nat) (p : Nat)
    (hrem : Galoistools.gfRem f f p = []) :
    Galoistools.gfGcd f f p = (Galoistools.gfMonic f p).2 := by
  unfold Galoistools.gfGcd
  simp only [Galoistools.gcdLoop]
  rw [hrem]
  rw [probe_gcdloop_zero_right]
''',
'gcdloop_norm_from_remnorm': r'''
theorem probe_gcdloop_norm_from_remnorm (f g : List Nat) (p fuel : Nat)
    (hf : Galoistools.IsNorm p f) (hg : Galoistools.IsNorm p g)
    (hremnorm : ∀ a b, Galoistools.IsNorm p a → Galoistools.IsNorm p b → b ≠ [] →
      Galoistools.IsNorm p (Galoistools.gfRem a b p)) :
    Galoistools.IsNorm p (Galoistools.gcdLoop p fuel f g) := by
  induction fuel generalizing f g with
  | zero => exact hf
  | succ fuel ih =>
      unfold Galoistools.gcdLoop
      by_cases hz : g = []
      · simp [hz, hf]
      · simp [hz]
        apply ih
        · exact hg
        · exact hremnorm f g hf hg hz
''',
}

census = []
for name, theorem_text in probes.items():
    probe = source / f'Probe_{name}.lean'
    probe.write_text(header + theorem_text + footer)
    cp = subprocess.run(['lake','lean', probe.name], cwd=source, text=True, capture_output=True)
    out = cp.stdout + '\n' + cp.stderr
    lines = out.splitlines()
    errors = [line for line in lines if 'error:' in line or line.startswith('error:')]
    states = []
    for k, line in enumerate(lines):
        if line.startswith('case ') or '⊢ ' in line:
            states.append('\n'.join(lines[k:k+24]))
    item = {'probe': name, 'exit': cp.returncode, 'errors': errors[-8:], 'residual': states[-3:]}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    for e in errors[-8:]: print(e)
    for st in states[-3:]: print(st)

outdir = Path('batch_harvest')
outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census, indent=2))
print('BATCH_CENSUS', json.dumps(census))
