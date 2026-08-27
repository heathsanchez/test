from pathlib import Path
import subprocess, json

# Reuse the exact V2 capability construction, then change only its final residual.
exec(compile(Path('../.github/scripts/vero_div_add_structure_v2.py').read_text(),
             '.github/scripts/vero_div_add_structure_v2.py', 'exec'), {'__name__':'__main__'})

p = Path('div_add_structure_v2/source/Probe_add_sub_cancel_norm.lean')
text = p.read_text()
old = '  simp [Galoistools.gfAdd, Galoistools.zipAddPad, hstrip]\n'
new = '''  have hnil : ∀ xs : List Nat,
      Galoistools.zipAddPad p xs [] = xs.map (fun x => x % p) := by
    intro xs
    cases xs <;> rfl
  have bridge : ∀ xs : List Nat,
      Galoistools.gfStrip xs = Galoistools.refGfStrip xs := by
    intro xs
    induction xs with
    | nil => rfl
    | cons x xs ih =>
      simp only [Galoistools.gfStrip, Galoistools.refGfStrip]
      by_cases hx : x = 0 <;> simp [hx, ih]
  simp only [Galoistools.gfAdd]
  rw [hnil cur.reverse]
  rw [List.map_reverse]
  simp only [List.reverse_reverse]
  rw [bridge]
  exact hcur
'''
assert old in text
p.write_text(text.replace(old, new, 1))
cp = subprocess.run(['lake','lean',p.name], cwd=p.parent, text=True,capture_output=True)
raw = cp.stdout + '\n' + cp.stderr
print('ADD_SUB_CANCEL_V3_EXIT', cp.returncode)
if cp.returncode: print(raw[-20000:])
out=Path('div_add_structure_v3'); out.mkdir(exist_ok=True)
(out/'result.json').write_text(json.dumps({'exit':cp.returncode,'tail':raw[-30000:] if cp.returncode else ''}, indent=2))
