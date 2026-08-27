from pathlib import Path
import subprocess, json

# Reuse the exact V2 capability construction, then change only its final residual.
exec(compile(Path('../.github/scripts/vero_div_add_structure_v2.py').read_text(),
             '.github/scripts/vero_div_add_structure_v2.py', 'exec'), {'__name__':'__main__'})

p = Path('div_add_structure_v2/source/Probe_add_sub_cancel_norm.lean')
text = p.read_text()
old = '  simp [Galoistools.gfAdd, Galoistools.zipAddPad, hstrip]\n'
new = '''  have ht : Galoistools.gfTrunc p cur = cur := by
    rw [Galoistools.gfTrunc, gfStrip_eq_refGfStrip]
    exact hcur
  simpa [Galoistools.gfTrunc, Galoistools.zipAddPad, List.map_reverse] using ht
'''
assert old in text
p.write_text(text.replace(old, new, 1))
cp = subprocess.run(['lake','lean',p.name], cwd=p.parent, text=True, capture_output=True)
raw = cp.stdout + '\n' + cp.stderr
print('ADD_SUB_CANCEL_V3_EXIT', cp.returncode)
if cp.returncode: print(raw[-20000:])
out=Path('div_add_structure_v3'); out.mkdir(exist_ok=True)
(out/'result.json').write_text(json.dumps({'exit':cp.returncode,'tail':raw[-30000:] if cp.returncode else ''}, indent=2))
