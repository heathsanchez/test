from pathlib import Path
import subprocess, re, json

root = Path('galoistools_allin/source').resolve()
ring = root / 'Galoistools/Proof/Ring.lean'
text = ring.read_text()
old = '''theorem prove_monic_mul_associate : spec_monic_mul_associate canonical := by
-- !benchmark @start proof def=prove_monic_mul_associate kind=prove target=spec_monic_mul_associate
  sorry
-- !benchmark @end proof def=prove_monic_mul_associate'''
new = '''theorem prove_monic_mul_associate : spec_monic_mul_associate canonical := by
-- !benchmark @start proof def=prove_monic_mul_associate kind=prove target=spec_monic_mul_associate
  simp only [spec_monic_mul_associate, canonical]
  intro f g p hp hnf hng hf hg
  cases f with
  | nil => exact (hf rfl).elim
  | cons a as =>
    cases g with
    | nil => exact (hg rfl).elim
    | cons b bs =>
      simp only [Galoistools.gfMonic]
      simp [Galoistools.gfMul]
-- !benchmark @end proof def=prove_monic_mul_associate'''
assert old in text
ring.write_text(text.replace(old, new, 1))
cp = subprocess.run(['lake','env','lean','Galoistools/Proof/Ring.lean'], cwd=root, text=True, capture_output=True)
raw = cp.stdout + '\n' + cp.stderr
print('MONIC_ASSOC_PROBE_EXIT', cp.returncode)
print(raw[-16000:])
out = Path('monic_assoc_probe'); out.mkdir(exist_ok=True)
(out/'result.json').write_text(json.dumps({'exit':cp.returncode,'tail':raw[-30000:]}, indent=2))
