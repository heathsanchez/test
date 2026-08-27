from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench_dir = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
source = Path('mul_leading_v1/source').resolve()
create_sandbox(bench_dir, source, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Ring
import Galoistools.Spec.Ring

namespace GaloistoolsMulLeadingV1
'''
footer = '\nend GaloistoolsMulLeadingV1\n'

shape = r'''
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

theorem last0_append_singleton (xs : List Nat) (x : Nat) :
    last0 (xs ++ [x]) = x := by
  induction xs with
  | nil => rfl
  | cons a xs ih =>
      simp only [List.cons_append]
      by_cases h : xs ++ [x] = []
      · simp at h
      · simp [last0, h, ih]

theorem last0_reverse (xs : List Nat) :
    last0 xs.reverse = Galoistools.leadCoeff xs := by
  cases xs with
  | nil => rfl
  | cons x xs =>
      simp [List.reverse_cons, last0_append_singleton, Galoistools.leadCoeff]

theorem zipAddPad_length_local (p : Nat) : ∀ xs ys : List Nat,
    (Galoistools.zipAddPad p xs ys).length = Nat.max xs.length ys.length := by
  intro xs
  induction xs with
  | nil =>
      intro ys
      simp [Galoistools.zipAddPad]
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

theorem convolve_length_local (p : Nat) (xs ys : List Nat)
    (hxs : xs ≠ []) (hys : ys ≠ []) :
    (Galoistools.convolve p xs ys).length = xs.length + ys.length - 1 := by
  induction xs with
  | nil => contradiction
  | cons x xs ih =>
      rw [Galoistools.convolve]
      rw [zipAddPad_length_local]
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
        have hyl : 0 < ys.length := by
          cases ys with
          | nil => contradiction
          | cons y ys => simp
        have hle : ys.length ≤ xs.length + ys.length - 1 + 1 := by
          have hxl : 0 < xs.length := by
            cases xs with
            | nil => contradiction
            | cons y ys => simp
          omega
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
            rw [zipAddPad_length_local] at hl
            simp at hl
            omega
          simp only [Galoistools.zipAddPad]
          simp [last0, htail, ih ys hlen hys', Nat.mod_mod]

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
        have hcvlen := convolve_length_local p xs ys htail hys
        have hyslen : 0 < ys.length := by
          cases ys with
          | nil => contradiction
          | cons y ys => simp
        have hxslen : 0 < xs.length := by
          cases xs with
          | nil => contradiction
          | cons y ys => simp
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
        simp [last0, hcv, cv, ih xs htail ys hys, Nat.mod_mod]
'''

leading = shape + r'''
theorem ref_strip_ne_zero_head_local (xs ys : List Nat) :
    Galoistools.refGfStrip xs ≠ 0 :: ys := by
  induction xs with
  | nil => simp [Galoistools.refGfStrip]
  | cons a as ih =>
      simp only [Galoistools.refGfStrip]
      by_cases h : a = 0
      · simp [h, ih]
      · simp [h]

theorem norm_head_nonzero_local (p a : Nat) (as : List Nat)
    (hn : Galoistools.IsNorm p (a :: as)) : a ≠ 0 := by
  intro ha
  subst a
  have h : Galoistools.refGfTrunc p (0 :: as) = 0 :: as := hn
  simp only [Galoistools.refGfTrunc, List.map_cons, Nat.zero_mod] at h
  exact ref_strip_ne_zero_head_local (0 :: as.map (fun x => x % p)) as h

theorem strip_len_local (xs : List Nat) :
    (Galoistools.refGfStrip xs).length ≤ xs.length := by
  induction xs with
  | nil => simp [Galoistools.refGfStrip]
  | cons a as ih =>
      simp only [Galoistools.refGfStrip]
      by_cases ha : a = 0
      · simp [ha]
        omega
      · simp [ha]

theorem norm_head_mod_eq_local (p a : Nat) (as : List Nat)
    (hn : Galoistools.IsNorm p (a :: as)) : a % p = a := by
  change Galoistools.refGfStrip ((a % p) :: as.map (fun x => x % p)) = a :: as at hn
  by_cases hz : a % p = 0
  · have hlen := congrArg List.length hn
    have hle := strip_len_local (as.map (fun x => x % p))
    simp [Galoistools.refGfStrip, hz] at hlen
    simp at hle
    omega
  · have heq : (a % p) :: as.map (fun x => x % p) = a :: as := by
      simpa [Galoistools.refGfStrip, hz] using hn
    exact (List.cons.inj heq).1

theorem primefield_coprime_lt_local2 (p a : Nat) (hp : Galoistools.PrimeField p)
    (ha0 : a ≠ 0) (ha : a < p) : p.Coprime a := by
  have hgcd : Nat.gcd a p = 1 := by
    let d := Nat.gcd a p
    have hda : d ∣ a := Nat.gcd_dvd_left a p
    have hdp : d ∣ p := Nat.gcd_dvd_right a p
    have hdle : d ≤ a := Nat.le_of_dvd (Nat.pos_of_ne_zero ha0) hda
    have hdlt : d < p := by omega
    by_cases hd1 : d = 1
    · exact hd1
    · have hd2 : 2 ≤ d := by
        have hdpos : 0 < d := Nat.pos_of_dvd_of_pos hdp (by omega)
        omega
      have hnot := hp.2 d hd2 hdlt
      exact (hnot (Nat.mod_eq_zero_of_dvd hdp)).elim
  rw [Nat.coprime_comm]
  exact hgcd

theorem mul_mod_nonzero_local (p a b : Nat) (hp : Galoistools.PrimeField p)
    (ha0 : a ≠ 0) (hb0 : b ≠ 0) (ha : a < p) (hb : b < p) :
    (a * b) % p ≠ 0 := by
  intro hz
  have hcop : p.Coprime a := primefield_coprime_lt_local2 p a hp ha0 ha
  have hdvd : p ∣ a * b := Nat.dvd_of_mod_eq_zero hz
  have hpb : p ∣ b := hcop.dvd_of_dvd_mul_left hdvd
  have hle : p ≤ b := Nat.le_of_dvd (Nat.pos_of_ne_zero hb0) hpb
  omega

theorem norm_head_bounds_local (p a : Nat) (as : List Nat)
    (hp : Galoistools.PrimeField p) (hn : Galoistools.IsNorm p (a :: as)) :
    a ≠ 0 ∧ a < p := by
  have ha0 := norm_head_nonzero_local p a as hn
  have hmod := norm_head_mod_eq_local p a as hn
  have hp1 : 1 < p := hp.1
  have hp0 : 0 < p := by omega
  constructor
  · exact ha0
  · rw [← hmod]
    exact Nat.mod_lt _ hp0

theorem leadCoeff_reverse_eq_last0 (xs : List Nat) (hxs : xs ≠ []) :
    Galoistools.leadCoeff xs.reverse = last0 xs := by
  induction xs with
  | nil => contradiction
  | cons x xs ih =>
      by_cases htail : xs = []
      · subst xs
        rfl
      · have ihx := ih htail
        cases hrev : xs.reverse with
        | nil =>
            have := List.reverse_ne_nil.mpr htail
            contradiction
        | cons y ys =>
            rw [hrev] at ihx
            simp [Galoistools.leadCoeff] at ihx
            simp [List.reverse_cons, hrev, Galoistools.leadCoeff, last0, htail, ihx]

theorem gfStrip_self_of_leadCoeff_ne (xs : List Nat)
    (h : Galoistools.leadCoeff xs ≠ 0) :
    Galoistools.gfStrip xs = xs := by
  cases xs with
  | nil => simp [Galoistools.leadCoeff] at h
  | cons a as =>
      simp [Galoistools.leadCoeff] at h
      simp [Galoistools.gfStrip, h]

theorem reversed_convolve_lead_nonzero (p : Nat) (f g : List Nat)
    (hp : Galoistools.PrimeField p) (hnf : Galoistools.IsNorm p f)
    (hng : Galoistools.IsNorm p g) (hf : f ≠ []) (hg : g ≠ []) :
    Galoistools.leadCoeff (Galoistools.convolve p f.reverse g.reverse).reverse ≠ 0 := by
  cases f with
  | nil => contradiction
  | cons a as =>
      cases g with
      | nil => contradiction
      | cons b bs =>
          have hfa := norm_head_bounds_local p a as hp hnf
          have hgb := norm_head_bounds_local p b bs hp hng
          have hmul := mul_mod_nonzero_local p a b hp hfa.1 hgb.1 hfa.2 hgb.2
          have hfr : (a :: as).reverse ≠ [] := by simp
          have hgr : (b :: bs).reverse ≠ [] := by simp
          have hconvlen := convolve_length_local p (a :: as).reverse (b :: bs).reverse hfr hgr
          have hconvne : Galoistools.convolve p (a :: as).reverse (b :: bs).reverse ≠ [] := by
            intro hz
            have hl := congrArg List.length hz
            rw [hconvlen] at hl
            simp at hl
          rw [leadCoeff_reverse_eq_last0 _ hconvne]
          rw [convolve_last0 p _ _ hfr hgr]
          simp [last0_reverse, Galoistools.leadCoeff] at hmul ⊢
          exact hmul
'''

probes = {
'convolve_last0': shape + r'''
theorem convolve_last0_probe (p : Nat) (xs ys : List Nat)
    (hxs : xs ≠ []) (hys : ys ≠ []) :
    last0 (Galoistools.convolve p xs ys) = (last0 xs * last0 ys) % p :=
  convolve_last0 p xs ys hxs hys
''',
'reversed_convolve_lead_nonzero': leading + r'''
theorem reversed_convolve_lead_nonzero_probe (p : Nat) (f g : List Nat)
    (hp : Galoistools.PrimeField p) (hnf : Galoistools.IsNorm p f)
    (hng : Galoistools.IsNorm p g) (hf : f ≠ []) (hg : g ≠ []) :
    Galoistools.leadCoeff (Galoistools.convolve p f.reverse g.reverse).reverse ≠ 0 :=
  reversed_convolve_lead_nonzero p f g hp hnf hng hf hg
''',
'gfMul_nonempty': leading + r'''
theorem gfMul_nonempty (p : Nat) (f g : List Nat)
    (hp : Galoistools.PrimeField p) (hnf : Galoistools.IsNorm p f)
    (hng : Galoistools.IsNorm p g) (hf : f ≠ []) (hg : g ≠ []) :
    Galoistools.gfMul f g p ≠ [] := by
  simp only [Galoistools.gfMul, hf, hg, false_or, if_false]
  have hlead := reversed_convolve_lead_nonzero p f g hp hnf hng hf hg
  rw [gfStrip_self_of_leadCoeff_ne _ hlead]
  intro hz
  have hrev := congrArg List.reverse hz
  simp at hrev
  have hfr : f.reverse ≠ [] := by simpa using hf
  have hgr : g.reverse ≠ [] := by simpa using hg
  have hlen := convolve_length_local p f.reverse g.reverse hfr hgr
  rw [hrev] at hlen
  simp at hlen
''',
'mul_zero_iff_direct': leading + r'''
theorem mul_zero_iff_direct (p : Nat) (f g : List Nat)
    (hp : Galoistools.PrimeField p) (hnf : Galoistools.IsNorm p f)
    (hng : Galoistools.IsNorm p g) :
    (Galoistools.gfMul f g p = [] ↔ (f = [] ∨ g = [])) := by
  constructor
  · intro h
    by_contra hn
    push_neg at hn
    exact (gfMul_nonempty p f g hp hnf hng hn.1 hn.2) h
  · intro h
    simp [Galoistools.gfMul, h]
''',
'mul_degree_add_direct': leading + r'''
theorem mul_degree_add_direct (p : Nat) (f g : List Nat)
    (hp : Galoistools.PrimeField p) (hnf : Galoistools.IsNorm p f)
    (hng : Galoistools.IsNorm p g) (hf : f ≠ []) (hg : g ≠ []) :
    Galoistools.refGfDegree (Galoistools.gfMul f g p) =
      Galoistools.refGfDegree f + Galoistools.refGfDegree g := by
  simp only [Galoistools.gfMul, hf, hg, false_or, if_false]
  have hlead := reversed_convolve_lead_nonzero p f g hp hnf hng hf hg
  rw [gfStrip_self_of_leadCoeff_ne _ hlead]
  simp only [Galoistools.refGfDegree, List.length_reverse]
  have hfr : f.reverse ≠ [] := by simpa using hf
  have hgr : g.reverse ≠ [] := by simpa using hg
  rw [convolve_length_local p f.reverse g.reverse hfr hgr]
  simp only [List.length_reverse]
  have hfl : 0 < f.length := by cases f <;> simp_all
  have hgl : 0 < g.length := by cases g <;> simp_all
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
    item={'probe':name,'exit':cp.returncode,'errors':errors[-16:],'residual':goals[-4:],'raw_tail':'\n'.join(lines[-500:]) if cp.returncode else ''}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    if cp.returncode: print(item['raw_tail'])

outdir=Path('mul_leading_v1'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('MUL_LEADING_V1_CENSUS',json.dumps(census))
