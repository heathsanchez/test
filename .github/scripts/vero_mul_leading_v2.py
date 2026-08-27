from pathlib import Path
import ast, subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

old = Path('../.github/scripts/vero_mul_leading_v1.py').read_text()
tree = ast.parse(old)
shape = None; suffix = None
for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0], ast.Name):
        name=node.targets[0].id
        if name=='shape' and isinstance(node.value, ast.Constant): shape=node.value.value
        if name=='leading' and isinstance(node.value, ast.BinOp) and isinstance(node.value.right, ast.Constant): suffix=node.value.right.value
assert shape is not None and suffix is not None

shape = shape.replace("""          have htail : Galoistools.zipAddPad p xs ys ≠ [] := by
            intro hz
            have hl := congrArg List.length hz
            rw [zipAddPad_length_local] at hl
            simp at hl
            omega
""", """          have hypos : 0 < ys.length := by
            cases ys with
            | nil => contradiction
            | cons z zs => simp
          have htail : Galoistools.zipAddPad p xs ys ≠ [] := by
            intro hz
            have hl := congrArg List.length hz
            rw [zipAddPad_length_local] at hl
            simp at hl
            omega
""")
shape = shape.replace("simp [last0, htail, ih ys hlen hys', Nat.mod_mod]", "simp [last0, htail, hys', ih ys hlen hys', Nat.mod_mod]")
shape = shape.replace("simp [last0, hcv, cv, ih xs htail ys hys, Nat.mod_mod]", "simp [last0, hcv, cv, htail, ih ys htail hys, Nat.mod_mod]")

leading = shape + suffix
start = """theorem leadCoeff_reverse_eq_last0 (xs : List Nat) (hxs : xs ≠ []) :
    Galoistools.leadCoeff xs.reverse = last0 xs := by
"""
a = leading.index(start)
b = leading.index("\ntheorem gfStrip_self_of_leadCoeff_ne", a)
replacement = """theorem leadCoeff_reverse_eq_last0 (xs : List Nat) (hxs : xs ≠ []) :
    Galoistools.leadCoeff xs.reverse = last0 xs := by
  simpa using (last0_reverse xs.reverse)
"""
leading = leading[:a] + replacement + leading[b:]
leading = leading.replace("""          simp [last0_reverse, Galoistools.leadCoeff] at hmul ⊢
          exact hmul
""", """          have hlf : last0 (a :: as).reverse = a := by
            simpa [Galoistools.leadCoeff] using (last0_reverse (a :: as))
          have hlg : last0 (b :: bs).reverse = b := by
            simpa [Galoistools.leadCoeff] using (last0_reverse (b :: bs))
          rw [hlf, hlg]
          exact hmul
""")

bench=Path('benchmarks/galoistools').resolve(); seed=read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
out=Path('mul_leading_v2/source').resolve(); create_sandbox(bench,out,mode='codeproof',overwrite=True,seed_artifact=seed)
header='''import Galoistools.Proof.Ring\nimport Galoistools.Impl.Ring\nimport Galoistools.Spec.Ring\n\nnamespace GaloistoolsMulLeadingV2\n'''; footer='\nend GaloistoolsMulLeadingV2\n'

gfnon = r'''
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
'''
zero = gfnon + r'''
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
'''
degree = r'''
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
probes={'convolve_last0':shape,'reversed_convolve_lead_nonzero':leading,'gfMul_nonempty':leading+gfnon,'mul_zero_iff_direct':leading+zero,'mul_degree_add_direct':leading+degree}
c=[]
for name,text in probes.items():
 p=out/f'Probe_{name}.lean'; p.write_text(header+text+footer)
 cp=subprocess.run(['lake','lean',p.name],cwd=out,text=True,capture_output=True); raw=cp.stdout+'\n'+cp.stderr
 c.append({'probe':name,'exit':cp.returncode,'raw_tail':'\n'.join(raw.splitlines()[-250:]) if cp.returncode else ''}); print('===',name,'EXIT',cp.returncode,'==='); print(c[-1]['raw_tail'])
Path('mul_leading_v2').mkdir(exist_ok=True); Path('mul_leading_v2/census.json').write_text(json.dumps(c,indent=2))
