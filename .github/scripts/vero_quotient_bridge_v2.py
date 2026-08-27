from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench_dir = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
source = Path('quotient_bridge_v2/source').resolve()
create_sandbox(bench_dir, source, mode='codeproof', overwrite=True, seed_artifact=seed)

header = 'import Galoistools.Proof.Ring\nimport Galoistools.Impl.Division\nimport Galoistools.Spec.Division\n\nnamespace GaloistoolsQuotientBridgeV2\n'
footer = '\nend GaloistoolsQuotientBridgeV2\n'

convolve = 'theorem convolve_zero_prefix_reuse (p c s : Nat) (ys : List Nat) (hys : ys ≠ []) :\n    Galoistools.convolve p (List.replicate s 0 ++ [c]) ys =\n      List.replicate s 0 ++ ys.map (fun y => (c * y) % p) := by\n  have hnil : ∀ xs : List Nat,\n      Galoistools.zipAddPad p xs [] = xs.map (· % p) := by\n    intro xs\n    cases xs <;> rfl\n  have hzeros : ∀ n : Nat, ∀ xs : List Nat,\n      xs.map (· % p) = xs → n ≤ xs.length →\n      Galoistools.zipAddPad p (List.replicate n 0) xs = xs := by\n    intro n xs hred hlen\n    induction n generalizing xs with\n    | zero => simpa [Galoistools.zipAddPad] using hred\n    | succ n ih =>\n        cases xs with\n        | nil => simp at hlen\n        | cons x xs =>\n          simp only [List.length_cons, Nat.succ_le_succ_iff] at hlen\n          simp only [List.map_cons] at hred\n          injection hred with hx hxs\n          simp [List.replicate_succ, Galoistools.zipAddPad, hx, ih xs hxs hlen]\n  have hmap0 : ∀ zs : List Nat,\n      zs.map (fun _ => 0) = List.replicate zs.length 0 := by\n    intro zs\n    induction zs with\n    | nil => rfl\n    | cons z zs ihz =>\n      simp only [List.map_cons, List.length_cons, List.replicate_succ]\n      rw [ihz]\n  induction s with\n  | zero =>\n    simp only [List.replicate_zero, List.nil_append]\n    cases ys with\n    | nil => contradiction\n    | cons y ys =>\n      simp [Galoistools.convolve, Galoistools.zipAddPad, hnil]\n  | succ s ih =>\n    simp only [List.replicate_succ, List.cons_append, Galoistools.convolve]\n    rw [ih]\n    simp only [Nat.zero_mul, Nat.zero_mod]\n    rw [hmap0 ys]\n    apply hzeros ys.length\n    · simp\n    · simp only [List.length_cons, List.length_append, List.length_replicate, List.length_map]\n      omega\n'
quotient = '\ntheorem quotient_term_mul_reuse (p c s : Nat) (g : List Nat) :\n    Galoistools.gfMul (Galoistools.shiftUp s [c]) g p =\n      Galoistools.shiftUp s (Galoistools.scaleP p c g) := by\n  have hz : ∀ n : Nat, Galoistools.gfStrip (List.replicate n 0) = [] := by\n    intro n\n    induction n with\n    | zero => rfl\n    | succ n ih => simp [List.replicate_succ, Galoistools.gfStrip, ih]\n  have hstrip : ∀ xs : List Nat, ∀ n : Nat,\n      Galoistools.gfStrip (xs ++ List.replicate n 0) =\n        if Galoistools.gfStrip xs = [] then []\n        else Galoistools.gfStrip xs ++ List.replicate n 0 := by\n    intro xs n\n    induction xs with\n    | nil => simpa [Galoistools.gfStrip] using hz n\n    | cons x xs ih =>\n        by_cases hx : x = 0\n        · simp [Galoistools.gfStrip, hx, ih]\n        · simp [Galoistools.gfStrip, hx]\n  by_cases hg : g = []\n  · subst g\n    simp [Galoistools.shiftUp, Galoistools.scaleP, Galoistools.gfMul, Galoistools.gfStrip]\n  · have hgr : g.reverse ≠ [] := by\n      intro h\n      apply hg\n      have hh := congrArg List.reverse h\n      simpa using hh\n    simp [Galoistools.gfMul, Galoistools.shiftUp, Galoistools.scaleP, hg]\n    rw [convolve_zero_prefix_reuse p c s g.reverse hgr]\n    simp only [List.reverse_append, List.map_reverse, List.reverse_replicate,\n      List.reverse_reverse]\n    rw [hstrip (g.map (fun y => (c * y) % p)) s]\n    simp [Nat.mul_comm]\n'

probes = {
    'convolve_zero_prefix_reuse': convolve,
    'quotient_term_mul_reuse': convolve + quotient,
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
    item={'probe':name,'exit':cp.returncode,'errors':errors[-12:],'residual':goals[-3:],'raw_tail':'\n'.join(lines[-400:]) if cp.returncode else ''}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    if cp.returncode: print(item['raw_tail'])

outdir=Path('quotient_bridge_v2'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('QUOTIENT_BRIDGE_V2_CENSUS',json.dumps(census))
