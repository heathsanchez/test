from pathlib import Path
import subprocess, json, re
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline27/allin_artifact.json').resolve())
out = Path('monic_mul_associate_direct_v1/source').resolve()
create_sandbox(bench, out, mode='codeproof', overwrite=True, seed_artifact=seed)

def strip_imports(s: str) -> str:
    return '\n'.join(line for line in s.splitlines() if not line.startswith('import '))

src = Path('../.github/scripts/vero_msi_gfmul_unit_lift_v1.py').read_text()
m = re.search(r"base = m.group\(1\).*?extra = r'''(.*)'''\n\nprobe = base \+ extra", src, re.S)
if not m:
    raise RuntimeError('could not extract unit-lift extra')
src0 = Path('../.github/scripts/vero_msi_gfmul_scale_both_v1.py').read_text()
m0 = re.search(r"probe = r'''(.*)'''\n\np = out", src0, re.S)
if not m0:
    raise RuntimeError('could not extract gfMul base')
base = m0.group(1).replace('\nend GaloistoolsMSIGfMulScaleBothV1\n', '\n')
extra = strip_imports(m.group(1)).replace('\nend GaloistoolsMSIGfMulScaleBothV1\n', '\n')

su = Path('../.github/scripts/vero_msi_unit_zero_bridge_v1.py').read_text()
mu = re.search(r"probe = r'''(.*)'''\n\np = out", su, re.S)
if not mu:
    raise RuntimeError('could not extract unit-zero block')
unit = strip_imports(mu.group(1))
unit = unit.replace('namespace GaloistoolsMSIUnitZeroBridgeV2', 'namespace GaloistoolsMSIGfMulScaleBothV1')
unit = unit.replace('end GaloistoolsMSIUnitZeroBridgeV2', '')
unit = unit.replace('theorem mul_left_reduce (p a k : Nat) :', 'theorem unit_mul_left_reduce (p a k : Nat) :')
unit = unit.replace('(mul_left_reduce p (z*k) c).symm', '(unit_mul_left_reduce p (z*k) c).symm')

ss = Path('../.github/scripts/vero_monic_scalar_probe_v4.py').read_text()
ms = re.search(r"probe = r'''(.*)'''\n\np = out", ss, re.S)
if not ms:
    raise RuntimeError('could not extract scalar block')
scalar = strip_imports(ms.group(1))

sel_src = Path('../.github/scripts/vero_selected_unit_mul_modeq_v1.py').read_text()
msel = re.search(r"extra = r'''(.*)'''\n\nprobe = scalar \+ extra", sel_src, re.S)
if not msel:
    raise RuntimeError('could not extract selected-unit block')
selected = strip_imports(msel.group(1))

final = r'''

namespace GaloistoolsMSIGfMulScaleBothV1

theorem norm_map_mod_self_nonempty
    (p a : Nat) (as : List Nat)
    (hn : Galoistools.IsNorm p (a :: as)) :
    (a :: as).map (fun x => x % p) = a :: as := by
  have ha0 := norm_head_nonzero_local p a as hn
  have hamod := norm_head_mod_eq_local p a as hn
  have hamod0 : a % p ≠ 0 := by
    rw [hamod]
    exact ha0
  change Galoistools.refGfStrip ((a % p) :: as.map (fun x => x % p)) = a :: as at hn
  simpa [Galoistools.refGfStrip, hamod0] using hn

theorem gfMonic_second_as_selected_scale
    (p a : Nat) (as : List Nat)
    (hn : Galoistools.IsNorm p (a :: as)) :
    (Galoistools.gfMonic (a :: as) p).2 =
      (a :: as).map (fun x => (x * selectedUnit p a) % p) := by
  by_cases ha1 : a = 1
  · have hmap := norm_map_mod_self_nonempty p a as hn
    simpa [Galoistools.gfMonic, selectedUnit, ha1, Nat.mul_one] using hmap.symm
  · simp [Galoistools.gfMonic, Galoistools.gfQuoGround, selectedUnit, ha1]

theorem map_mod_self_of_all_lt (p : Nat) (xs : List Nat)
    (hlt : ∀ z ∈ xs, z < p) :
    xs.map (fun z => z % p) = xs := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
      have hx : x < p := hlt x (by simp)
      have hxs : ∀ z ∈ xs, z < p := by
        intro z hz
        exact hlt z (by simp [hz])
      simp [Nat.mod_eq_of_lt hx, ih hxs]

theorem gfMonic_second_as_selected_scale_of_all_lt
    (p c : Nat) (cs : List Nat)
    (hlt : ∀ z ∈ (c :: cs), z < p) :
    (Galoistools.gfMonic (c :: cs) p).2 =
      (c :: cs).map (fun x => (x * selectedUnit p c) % p) := by
  by_cases hc1 : c = 1
  · have hmap := map_mod_self_of_all_lt p (c :: cs) hlt
    simpa [Galoistools.gfMonic, selectedUnit, hc1, Nat.mul_one] using hmap.symm
  · simp [Galoistools.gfMonic, Galoistools.gfQuoGround, selectedUnit, hc1]

theorem selectedUnit_is_unit
    (p a : Nat) (hp : Galoistools.PrimeField p)
    (ha0 : a ≠ 0) (ha : a < p) :
    (a * selectedUnit p a) % p = 1 := by
  unfold selectedUnit
  by_cases ha1 : a = 1
  · subst a
    simp [Nat.mod_eq_of_lt hp.1]
  · have hcopA : Nat.gcd a p = 1 := by
      have h := primefield_coprime_lt_local2 p a hp ha0 ha
      simpa [Nat.coprime_comm] using h
    simpa [ha1] using inv_correct_nonone p a hp.1 ha1 hcopA

theorem prove_monic_mul_associate_msi_v8 : spec_monic_mul_associate canonical := by
  simp only [spec_monic_mul_associate, canonical]
  intro f g p hp hnf hng hf hg
  cases f with
  | nil => exact (hf rfl).elim
  | cons a as =>
    cases g with
    | nil => exact (hg rfl).elim
    | cons b bs =>
      have hfa := norm_head_bounds_local p a as hp hnf
      have hgb := norm_head_bounds_local p b bs hp hng
      let ua := selectedUnit p a
      let ub := selectedUnit p b
      let c := (a*b)%p
      let uc := selectedUnit p c
      have hlead := reversed_convolve_lead_nonzero p (a :: as) (b :: bs) hp hnf hng (by simp) (by simp)
      have hmulform :
          Galoistools.gfMul (a :: as) (b :: bs) p =
            (Galoistools.convolve p (a :: as).reverse (b :: bs).reverse).reverse := by
        simp only [Galoistools.gfMul, List.cons_ne_nil, false_or, if_false]
        exact gfStrip_self_of_leadCoeff_ne _ hlead
      have hfr : (a :: as).reverse ≠ [] := by simp
      have hgr : (b :: bs).reverse ≠ [] := by simp
      have hconvlen := convolve_length_local p (a :: as).reverse (b :: bs).reverse hfr hgr
      have hconvne : Galoistools.convolve p (a :: as).reverse (b :: bs).reverse ≠ [] := by
        intro hz
        have hl := congrArg List.length hz
        rw [hconvlen] at hl
        simp at hl
      have hprodhead :
          Galoistools.leadCoeff (Galoistools.gfMul (a :: as) (b :: bs) p) = c := by
        dsimp [c]
        rw [hmulform]
        rw [leadCoeff_reverse_eq_last0 _ hconvne]
        rw [convolve_last0 p _ _ hfr hgr]
        simp only [List.reverse_cons]
        rw [last0_append_singleton, last0_append_singleton]
      have hmulne : Galoistools.gfMul (a :: as) (b :: bs) p ≠ [] := by
        rw [hmulform]
        simpa using hconvne
      have hp0 : 0 < p := by omega
      have hconvlt := convolve_all_lt p hp0 (a :: as).reverse (b :: bs).reverse
      have hmult : ∀ z ∈ Galoistools.gfMul (a :: as) (b :: bs) p, z < p := by
        intro z hz
        rw [hmulform] at hz
        exact hconvlt z (by simpa using hz)
      have hc0 : c ≠ 0 := by
        dsimp [c]
        exact mul_mod_nonzero_local p a b hp hfa.1 hgb.1 hfa.2 hgb.2
      have hc_lt : c < p := by
        dsimp [c]
        exact Nat.mod_lt _ hp0
      have hsel : NatModEq p uc (ua*ub) := by
        dsimp [uc, ua, ub, c]
        exact selectedUnit_mul_modeq p a b hp hfa.1 hgb.1 hfa.2 hgb.2
      have hcunit : (c * uc) % p = 1 := by
        dsimp [uc]
        exact selectedUnit_is_unit p c hp hc0 hc_lt
      have hkunit : (c * (ua*ub)) % p = 1 := by
        unfold NatModEq at hsel
        calc
          (c * (ua*ub)) % p = ((c%p) * ((ua*ub)%p)) % p := by rw [Nat.mul_mod]
          _ = ((c%p) * (uc%p)) % p := by rw [hsel]
          _ = (c * uc) % p := by simpa [Nat.mod_mod] using (Nat.mul_mod c uc p).symm
          _ = 1 := hcunit
      have hzero : ∀ z : Nat,
          z ∈ Galoistools.convolve p (a :: as).reverse (b :: bs).reverse →
          ((z*(ua*ub))%p = 0 ↔ z = 0) := by
        intro z hz
        have hzlt := hconvlt z hz
        exact unit_zero_exact_of_lt p (ua*ub) c z hp0 hzlt (by simpa [Nat.mul_comm] using hkunit)
      have hfa_ne : (a :: as).map (fun x => (x*ua)%p) ≠ [] := by simp
      have hgb_ne : (b :: bs).map (fun x => (x*ub)%p) ≠ [] := by simp
      have hscale := gfMul_scale_both_mem p ua ub (a :: as) (b :: bs)
        (by simp) (by simp) hfa_ne hgb_ne hzero
      rw [gfMonic_second_as_selected_scale p a as hnf]
      rw [gfMonic_second_as_selected_scale p b bs hng]
      change (Galoistools.gfMonic (Galoistools.gfMul (a :: as) (b :: bs) p) p).2 =
        Galoistools.gfMul
          ((a :: as).map (fun x => (x*ua)%p))
          ((b :: bs).map (fun x => (x*ub)%p)) p
      rw [hscale]
      cases hP : Galoistools.gfMul (a :: as) (b :: bs) p with
      | nil => exact (hmulne hP).elim
      | cons d ds =>
        have hd : d = c := by
          rw [hP] at hprodhead
          simpa [Galoistools.leadCoeff] using hprodhead
        subst d
        have hltP : ∀ z ∈ (c :: ds), z < p := by
          intro z hz
          apply hmult z
          simpa [hP] using hz
        rw [gfMonic_second_as_selected_scale_of_all_lt p c ds hltP]
        have hmapEq :
            (c :: ds).map (fun z => (z*uc)%p) =
            (c :: ds).map (fun z => (z*(ua*ub))%p) := by
          apply List.map_congr_left
          intro z hz
          unfold NatModEq at hsel
          calc
            (z*uc)%p = ((z%p)*(uc%p))%p := by rw [Nat.mul_mod]
            _ = ((z%p)*((ua*ub)%p))%p := by rw [hsel]
            _ = (z*(ua*ub))%p := by simpa [Nat.mod_mod] using (Nat.mul_mod z (ua*ub) p).symm
        simpa [hP] using hmapEq

end GaloistoolsMSIGfMulScaleBothV1
'''

probe = base + extra + unit + '\nend GaloistoolsMSIGfMulScaleBothV1\n\n' + scalar + selected + final
p = out/'Probe.lean'; p.write_text(probe)
cp=subprocess.run(['lake','lean',p.name],cwd=out,text=True,capture_output=True)
raw=cp.stdout+'\n'+cp.stderr
print('MONIC_MUL_ASSOCIATE_DIRECT_V8_EXIT',cp.returncode)
print(raw[-50000:])
Path('monic_mul_associate_direct_v1').mkdir(exist_ok=True)
Path('monic_mul_associate_direct_v1/result.json').write_text(json.dumps({'exit':cp.returncode,'tail':raw[-60000:]},indent=2))
