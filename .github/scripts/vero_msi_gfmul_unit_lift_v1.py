from pathlib import Path
import subprocess, json, re
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline27/allin_artifact.json').resolve())
out = Path('msi_gfmul_unit_lift_v1/source').resolve()
create_sandbox(bench, out, mode='codeproof', overwrite=True, seed_artifact=seed)

# Reuse the already-certified lower algebraic block verbatim.
src = Path('../.github/scripts/vero_msi_gfmul_scale_both_v1.py').read_text()
m = re.search(r"probe = r'''(.*)'''\n\np = out", src, re.S)
if not m:
    raise RuntimeError('could not extract certified gfMul block')
base = m.group(1)
# Drop the closing namespace so we can add the local-membership refinement in the same namespace.
base = base.replace('\nend GaloistoolsMSIGfMulScaleBothV1\n', '\n')

extra = r'''

theorem gfStrip_map_scale_mem
    (p k : Nat) (f : List Nat)
    (hzero : ∀ z : Nat, z ∈ f → ((z*k)%p = 0 ↔ z = 0)) :
    Galoistools.gfStrip (f.map (fun z => (z*k)%p)) =
      (Galoistools.gfStrip f).map (fun z => (z*k)%p) := by
  induction f with
  | nil => rfl
  | cons a as ih =>
      simp only [List.map_cons]
      have hza := hzero a (by simp)
      have hzt : ∀ z : Nat, z ∈ as → ((z*k)%p = 0 ↔ z = 0) := by
        intro z hz
        exact hzero z (by simp [hz])
      by_cases ha : a = 0
      · have hs : (a*k)%p = 0 := (hza).2 ha
        simp [Galoistools.gfStrip, ha, hs, ih hzt]
      · have hs : (a*k)%p ≠ 0 := by
          intro h
          exact ha ((hza).1 h)
        simp [Galoistools.gfStrip, ha, hs]

theorem gfMul_scale_both_mem
    (p a b : Nat) (f g : List Nat)
    (hf : f ≠ []) (hg : g ≠ [])
    (hfa : f.map (fun x => (x*a)%p) ≠ [])
    (hgb : g.map (fun y => (y*b)%p) ≠ [])
    (hzero : ∀ z : Nat,
      z ∈ Galoistools.convolve p f.reverse g.reverse →
      ((z*(a*b))%p = 0 ↔ z = 0)) :
    Galoistools.gfMul
      (f.map (fun x => (x*a)%p))
      (g.map (fun y => (y*b)%p)) p =
    (Galoistools.gfMul f g p).map (fun z => (z*(a*b))%p) := by
  simp only [Galoistools.gfMul, hfa, hgb, hf, hg, false_or, if_false]
  rw [reverse_map_scale p a f]
  rw [reverse_map_scale p b g]
  rw [convolve_scale_both p a b f.reverse g.reverse]
  rw [reverse_map_scale p (a*b) (Galoistools.convolve p f.reverse g.reverse)]
  apply gfStrip_map_scale_mem
  intro z hz
  have hz' : z ∈ Galoistools.convolve p f.reverse g.reverse := by
    simpa using hz
  exact hzero z hz'

end GaloistoolsMSIGfMulScaleBothV1
'''

probe = base + extra
p = out/'Probe.lean'; p.write_text(probe)
cp=subprocess.run(['lake','lean',p.name],cwd=out,text=True,capture_output=True)
raw=cp.stdout+'\n'+cp.stderr
print('MSI_GFMUL_UNIT_LIFT_V1_EXIT',cp.returncode)
print(raw[-26000:])
Path('msi_gfmul_unit_lift_v1').mkdir(exist_ok=True)
Path('msi_gfmul_unit_lift_v1/result.json').write_text(json.dumps({'exit':cp.returncode,'tail':raw[-34000:]},indent=2))
