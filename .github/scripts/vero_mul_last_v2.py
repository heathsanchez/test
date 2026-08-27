from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench_dir = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
source = Path('mul_last_v2/source').resolve()
create_sandbox(bench_dir, source, mode='codeproof', overwrite=True, seed_artifact=seed)

code = r'''import Galoistools.Proof.Ring
import Galoistools.Impl.Ring
import Galoistools.Spec.Ring

namespace GaloistoolsMulLastV2

def last0 : List Nat → Nat
  | [] => 0
  | x :: xs => if xs = [] then x else last0 xs

theorem last0_map (f : Nat → Nat) (xs : List Nat) (hxs : xs ≠ []) :
    last0 (xs.map f) = f (last0 xs) := by
  induction xs with
  | nil => contradiction
  | cons x xs ih =>
      by_cases htail : xs = []
      · subst xs
        rfl
      · simp [last0, htail, ih htail]

theorem zipAddPad_length (p : Nat) : ∀ xs ys : List Nat,
    (Galoistools.zipAddPad p xs ys).length = Nat.max xs.length ys.length := by
  intro xs
  induction xs with
  | nil => intro ys; simp [Galoistools.zipAddPad]
  | cons x xs ih =>
      intro ys
      cases ys with
      | nil => simp [Galoistools.zipAddPad]
      | cons y ys =>
          simp only [Galoistools.zipAddPad, List.length_cons]
          rw [ih ys]
          by_cases h : xs.length ≤ ys.length
          · have h1 : Nat.max xs.length ys.length = ys.length := Nat.max_eq_right h
            have h2 : Nat.max (xs.length + 1) (ys.length + 1) = ys.length + 1 :=
              Nat.max_eq_right (by omega)
            rw [h1, h2]
          · have hle : ys.length ≤ xs.length := by omega
            have h1 : Nat.max xs.length ys.length = xs.length := Nat.max_eq_left hle
            have h2 : Nat.max (xs.length + 1) (ys.length + 1) = xs.length + 1 :=
              Nat.max_eq_left (by omega)
            rw [h1, h2]

theorem convolve_length (p : Nat) (xs ys : List Nat)
    (hxs : xs ≠ []) (hys : ys ≠ []) :
    (Galoistools.convolve p xs ys).length = xs.length + ys.length - 1 := by
  induction xs with
  | nil => contradiction
  | cons x xs ih =>
      rw [Galoistools.convolve, zipAddPad_length]
      simp only [List.length_map, List.length_cons]
      by_cases htail : xs = []
      · subst xs
        simp [Galoistools.convolve]
        have hyl : 1 ≤ ys.length := by
          cases ys with
          | nil => contradiction
          | cons y ys => simp
        have hm : Nat.max ys.length 1 = ys.length := Nat.max_eq_left hyl
        rw [hm]
      · have iht := ih htail
        rw [iht]
        have hxl : 0 < xs.length := by cases xs with | nil => contradiction | cons y ys => simp
        have hyl : 0 < ys.length := by cases ys with | nil => contradiction | cons y ys => simp
        have hle : ys.length ≤ xs.length + ys.length - 1 + 1 := by omega
        have hm : Nat.max ys.length (xs.length + ys.length - 1 + 1) =
            xs.length + ys.length - 1 + 1 := Nat.max_eq_right hle
        rw [hm]
        omega

theorem zipAddPad_last_right (p : Nat) : ∀ xs ys : List Nat,
    xs.length < ys.length → ys ≠ [] →
    last0 (Galoistools.zipAddPad p xs ys) = last0 ys % p := by
  intro xs
  induction xs with
  | nil =>
      intro ys hlen hys
      simp only [Galoistools.zipAddPad]
      simpa using last0_map (fun y => y % p) ys hys
  | cons x xs ih =>
      intro ys hlen hys
      cases ys with
      | nil => contradiction
      | cons y ys =>
          simp only [List.length_cons, Nat.succ_lt_succ_iff] at hlen
          have hys' : ys ≠ [] := by
            intro hz
            subst ys
            simp at hlen
          have htail : Galoistools.zipAddPad p xs ys ≠ [] := by
            intro hz
            have hl := congrArg List.length hz
            rw [zipAddPad_length] at hl
            simp at hl
            have hmax := Nat.le_max_right xs.length ys.length
            omega
          simp only [Galoistools.zipAddPad]
          simp [last0, htail, hys', ih ys hlen hys']

theorem convolve_last0 (p : Nat) : ∀ xs ys : List Nat,
    xs ≠ [] → ys ≠ [] →
    last0 (Galoistools.convolve p xs ys) = (last0 xs * last0 ys) % p := by
  intro xs
  induction xs with
  | nil => intro ys hxs hys; contradiction
  | cons x xs ih =>
      intro ys hxs hys
      by_cases htail : xs = []
      · subst xs
        have hsingle : Galoistools.convolve p [x] ys =
            ys.map (fun y => (x * y) % p) := by
          have hnil : ∀ zs : List Nat,
              Galoistools.zipAddPad p zs [] = zs.map (· % p) := by
            intro zs
            cases zs <;> rfl
          cases ys with
          | nil => contradiction
          | cons y ys =>
              simp [Galoistools.convolve, Galoistools.zipAddPad, hnil, Nat.mod_mod]
        rw [hsingle]
        simpa [last0] using last0_map (fun y => (x * y) % p) ys hys
      · rw [Galoistools.convolve]
        let hd := ys.map (fun y => (x * y) % p)
        let cv := Galoistools.convolve p xs ys
        have hcvlen := convolve_length p xs ys htail hys
        have hyslen : 0 < ys.length := by cases ys with | nil => contradiction | cons y ys => simp
        have hxslen : 0 < xs.length := by cases xs with | nil => contradiction | cons y ys => simp
        have hlt : hd.length < (0 :: cv).length := by
          simp only [hd, cv, List.length_map, List.length_cons]
          rw [hcvlen]
          omega
        have hcv : cv ≠ [] := by
          intro hz
          have hl := congrArg List.length hz
          rw [hcvlen] at hl
          simp at hl
          omega
        rw [zipAddPad_last_right p hd (0 :: cv) hlt (by simp)]
        have iht := ih ys htail hys
        simp [last0, hcv, cv, htail, iht, Nat.mod_mod]

theorem probe (p : Nat) (xs ys : List Nat) (hxs : xs ≠ []) (hys : ys ≠ []) :
    last0 (Galoistools.convolve p xs ys) = (last0 xs * last0 ys) % p :=
  convolve_last0 p xs ys hxs hys

end GaloistoolsMulLastV2
'''

probe=source/'Probe_mul_last_v2.lean'
probe.write_text(code)
cp=subprocess.run(['lake','lean',probe.name],cwd=source,text=True,capture_output=True)
raw=cp.stdout+'\n'+cp.stderr
lines=raw.splitlines()
item={'probe':'mul_last_v2','exit':cp.returncode,
      'errors':[x for x in lines if 'error:' in x or 'error(' in x or 'unknown identifier' in x][-20:],
      'raw_tail':'\n'.join(lines[-500:]) if cp.returncode else ''}
outdir=Path('mul_last_v2'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps([item],indent=2))
print('MUL_LAST_V2_CENSUS',json.dumps([item]))
if cp.returncode: print(item['raw_tail'])
