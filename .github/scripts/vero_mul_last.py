from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench_dir = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
source = Path('mul_last/source').resolve()
create_sandbox(bench_dir, source, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Ring
import Galoistools.Spec.Ring

namespace GaloistoolsMulLast
'''
footer = '\nend GaloistoolsMulLast\n'

core = r'''
def last0 : List Nat → Nat
  | [] => 0
  | x :: xs => match xs with
    | [] => x
    | y :: ys => last0 (y :: ys)

theorem last0_append_singleton (xs : List Nat) (a : Nat) :
    last0 (xs ++ [a]) = a := by
  induction xs with
  | nil => simp [last0]
  | cons x xs ih =>
      cases xs with
      | nil => simp [last0]
      | cons y ys =>
          simp only [List.cons_append]
          simp [last0] at ih ⊢
          exact ih

theorem last0_reverse_cons (a : Nat) (as : List Nat) :
    last0 ((a :: as).reverse) = a := by
  simp [List.reverse_cons, last0_append_singleton]

theorem last0_map_mulmod (p c : Nat) : ∀ ys : List Nat,
    last0 (ys.map (fun y => (c * y) % p)) = (c * last0 ys) % p := by
  intro ys
  induction ys with
  | nil => simp [last0]
  | cons y ys ih =>
      cases ys with
      | nil => simp [last0]
      | cons z zs =>
          simp [last0] at ih ⊢
          exact ih

theorem last0_map_mod (p : Nat) : ∀ ys : List Nat,
    last0 (ys.map (fun y => y % p)) = last0 ys % p := by
  intro ys
  induction ys with
  | nil => simp [last0]
  | cons y ys ih =>
      cases ys with
      | nil => simp [last0]
      | cons z zs =>
          simp [last0] at ih ⊢
          exact ih

theorem zipAddPad_last_right_longer (p : Nat) : ∀ xs ys : List Nat,
    xs.length < ys.length →
    last0 (Galoistools.zipAddPad p xs ys) = last0 ys % p := by
  intro xs
  induction xs with
  | nil =>
      intro ys h
      simpa [Galoistools.zipAddPad] using last0_map_mod p ys
  | cons x xs ih =>
      intro ys h
      cases ys with
      | nil => simp at h
      | cons y ys =>
          simp only [List.length_cons, Nat.succ_lt_succ_iff] at h
          simp only [Galoistools.zipAddPad]
          have hrec := ih ys h
          have hys0 : ys ≠ [] := by
            intro hz
            subst ys
            simp at h
          have hz0 : Galoistools.zipAddPad p xs ys ≠ [] := by
            cases xs <;> cases ys <;> simp_all [Galoistools.zipAddPad]
          cases hrecList : Galoistools.zipAddPad p xs ys with
          | nil => exact (hz0 hrecList).elim
          | cons z zs =>
              rw [hrecList] at hrec
              simp [last0, hrecList]
              exact hrec

theorem zipAddPad_last_left_longer (p : Nat) : ∀ xs ys : List Nat,
    ys.length < xs.length →
    last0 (Galoistools.zipAddPad p xs ys) = last0 xs % p := by
  intro xs
  induction xs with
  | nil => intro ys h; simp at h
  | cons x xs ih =>
      intro ys h
      cases ys with
      | nil =>
          simp [Galoistools.zipAddPad]
          exact last0_map_mod p (x :: xs)
      | cons y ys =>
          simp only [List.length_cons, Nat.succ_lt_succ_iff] at h
          simp only [Galoistools.zipAddPad]
          have hrec := ih ys h
          have hxs0 : xs ≠ [] := by
            intro hz
            subst xs
            simp at h
          have hz0 : Galoistools.zipAddPad p xs ys ≠ [] := by
            cases xs <;> cases ys <;> simp_all [Galoistools.zipAddPad]
          cases hrecList : Galoistools.zipAddPad p xs ys with
          | nil => exact (hz0 hrecList).elim
          | cons z zs =>
              rw [hrecList] at hrec
              simp [last0, hrecList]
              have hxlast : last0 (x :: xs) = last0 xs := by
                cases xs <;> simp_all [last0]
              rw [hxlast]
              exact hrec

theorem zipAddPad_last_equal (p : Nat) : ∀ xs ys : List Nat,
    xs.length = ys.length →
    last0 (Galoistools.zipAddPad p xs ys) = (last0 xs + last0 ys) % p := by
  intro xs
  induction xs with
  | nil =>
      intro ys h
      have : ys = [] := by simpa using h
      subst ys
      simp [Galoistools.zipAddPad, last0]
  | cons x xs ih =>
      intro ys h
      cases ys with
      | nil => simp at h
      | cons y ys =>
          simp only [List.length_cons, Nat.succ.injEq] at h
          simp only [Galoistools.zipAddPad]
          by_cases htail : xs = []
          · subst xs
            have hy : ys = [] := by simpa using h
            subst ys
            simp [last0]
          · have hys0 : ys ≠ [] := by
              intro hy
              subst ys
              simp at h htail
            have hrec := ih ys h
            have hz0 : Galoistools.zipAddPad p xs ys ≠ [] := by
              cases xs <;> cases ys <;> simp_all [Galoistools.zipAddPad]
            cases hrecList : Galoistools.zipAddPad p xs ys with
            | nil => exact (hz0 hrecList).elim
            | cons z zs =>
                rw [hrecList] at hrec
                simp [last0, hrecList]
                have hxlast : last0 (x :: xs) = last0 xs := by
                  cases xs <;> simp_all [last0]
                have hylast : last0 (y :: ys) = last0 ys := by
                  cases ys <;> simp_all [last0]
                rw [hxlast, hylast]
                exact hrec

theorem zipAddPad_length_local (p : Nat) : ∀ xs ys : List Nat,
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
            have h2 : Nat.max (xs.length + 1) (ys.length + 1) = ys.length + 1 := Nat.max_eq_right (by omega)
            rw [h1, h2]
          · have hle : ys.length ≤ xs.length := by omega
            have h1 : Nat.max xs.length ys.length = xs.length := Nat.max_eq_left hle
            have h2 : Nat.max (xs.length + 1) (ys.length + 1) = xs.length + 1 := Nat.max_eq_left (by omega)
            rw [h1, h2]

theorem convolve_length_local (p : Nat) (xs ys : List Nat)
    (hxs : xs ≠ []) (hys : ys ≠ []) :
    (Galoistools.convolve p xs ys).length = xs.length + ys.length - 1 := by
  induction xs with
  | nil => contradiction
  | cons x xs ih =>
      rw [Galoistools.convolve, zipAddPad_length_local]
      simp only [List.length_map, List.length_cons]
      by_cases htail : xs = []
      · subst xs
        simp [Galoistools.convolve]
        have hyl : 1 ≤ ys.length := by cases ys <;> simp_all
        have hm : Nat.max ys.length 1 = ys.length := Nat.max_eq_left hyl
        rw [hm]
      · rw [ih htail]
        have hyl : 0 < ys.length := by cases ys <;> simp_all
        have hxl : 0 < xs.length := by cases xs <;> simp_all
        have hle : ys.length ≤ xs.length + ys.length - 1 + 1 := by omega
        have hm : Nat.max ys.length (xs.length + ys.length - 1 + 1) = xs.length + ys.length - 1 + 1 := Nat.max_eq_right hle
        rw [hm]
        omega
'''

probes = {
'last0_reverse_cons': core + r'''
theorem probe (a : Nat) (as : List Nat) : last0 ((a :: as).reverse) = a :=
  last0_reverse_cons a as
''',
'zip_last_cases': core + r'''
theorem probeR (p : Nat) (xs ys : List Nat) (h : xs.length < ys.length) :
    last0 (Galoistools.zipAddPad p xs ys) = last0 ys % p :=
  zipAddPad_last_right_longer p xs ys h

theorem probeL (p : Nat) (xs ys : List Nat) (h : ys.length < xs.length) :
    last0 (Galoistools.zipAddPad p xs ys) = last0 xs % p :=
  zipAddPad_last_left_longer p xs ys h

theorem probeE (p : Nat) (xs ys : List Nat) (h : xs.length = ys.length) :
    last0 (Galoistools.zipAddPad p xs ys) = (last0 xs + last0 ys) % p :=
  zipAddPad_last_equal p xs ys h
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
        if '⊢ ' in line or line.startswith('case '): goals.append('\n'.join(lines[k:k+100]))
    item={'probe':name,'exit':cp.returncode,'errors':errors[-20:],'residual':goals[-5:],'raw_tail':'\n'.join(lines[-500:]) if cp.returncode else ''}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    if cp.returncode: print(item['raw_tail'])

outdir=Path('mul_last'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('MUL_LAST_CENSUS',json.dumps(census))
