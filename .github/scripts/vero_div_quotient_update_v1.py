from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench=Path('benchmarks/galoistools').resolve()
seed=read_artifact(Path('../baseline27/allin_artifact.json').resolve())
out=Path('div_quotient_update_v1/source').resolve()
create_sandbox(bench,out,mode='codeproof',overwrite=True,seed_artifact=seed)

header='''import Galoistools.Proof.Ring\nimport Galoistools.Impl.Division\nimport Galoistools.Spec.Division\n\nnamespace DivQuotientUpdateV1\n'''
footer='\nend DivQuotientUpdateV1\n'

common=r'''
theorem shift_singleton_shape (s c : Nat) :
    Galoistools.shiftUp s [c] = [c] ++ List.replicate s 0 := by
  simp [Galoistools.shiftUp]

theorem zipAddPad_zero_slot (p : Nat) (q : List Nat) (gap s : Nat) (c : Nat)
    (hq : q.map (fun x => x % p) = q) (hc : c < p) :
    Galoistools.zipAddPad p
      (q ++ List.replicate (gap + 1 + s) 0).reverse
      (Galoistools.shiftUp s [c]).reverse =
    (q ++ List.replicate gap 0 ++ [c] ++ List.replicate s 0).reverse := by
  simp only [shift_singleton_shape, List.reverse_append, List.reverse_replicate,
    List.reverse_singleton]
  -- expose alignment from the low-degree end
  induction s with
  | zero =>
      simp only [List.replicate_zero, List.nil_append, List.append_nil]
      simp [Galoistools.zipAddPad, hc, hq]
  | succ s ih =>
      simp only [List.replicate_succ, List.cons_append, List.reverse_cons]
      simp [Galoistools.zipAddPad, ih, hc, hq]
'''

probes={
'zip_zero_slot': common,
'completed_update': common+r'''
theorem completed_update (p : Nat) (q : List Nat) (e s : Int) (c : Nat)
    (hs0 : 0 ≤ s) (hse : s ≤ e)
    (hq : q.map (fun x => x % p) = q) (hc : c < p)
    (hhead : q = [] ∨ Galoistools.leadCoeff q ≠ 0) :
    Galoistools.gfAdd
      (q ++ List.replicate (e + 1).toNat 0)
      (Galoistools.shiftUp s.toNat [c]) p =
    q ++ List.replicate (e - s).toNat 0 ++ [c] ++ List.replicate s.toNat 0 := by
  have hcount : (e + 1).toNat = (e - s).toNat + 1 + s.toNat := by omega
  rw [hcount]
  simp only [Galoistools.gfAdd]
  rw [zipAddPad_zero_slot p q (e-s).toNat s.toNat c hq hc]
  simp only [List.reverse_reverse]
  -- strip should be inert because either q already starts nonzero or c is the first term
  rcases hhead with hq0 | hqhead
  · subst q
    simp [Galoistools.gfStrip]
  · have hqne : q ≠ [] := by
      intro hz
      subst q
      simp [Galoistools.leadCoeff] at hqhead
    cases q with
    | nil => contradiction
    | cons a as =>
      have ha : a ≠ 0 := by simpa [Galoistools.leadCoeff] using hqhead
      simp [Galoistools.gfStrip, ha]
'''
}

res=[]
for name,text in probes.items():
 p=out/f'Probe_{name}.lean'; p.write_text(header+text+footer)
 cp=subprocess.run(['lake','lean',p.name],cwd=out,text=True,capture_output=True)
 raw=cp.stdout+'\n'+cp.stderr; ls=raw.splitlines(); goals=[]
 for k,l in enumerate(ls):
  if '⊢ ' in l or l.startswith('case '): goals.append('\n'.join(ls[k:k+100]))
 item={'probe':name,'exit':cp.returncode,'errors':[l for l in ls if 'error:' in l or 'unknown identifier' in l][-12:],'residual':goals[-3:],'raw_tail':'\n'.join(ls[-400:]) if cp.returncode else ''}
 res.append(item); print('===',name,'EXIT',cp.returncode,'===');
 if cp.returncode: print(item['raw_tail'])
Path('div_quotient_update_v1').mkdir(exist_ok=True)
Path('div_quotient_update_v1/census.json').write_text(json.dumps(res,indent=2))
