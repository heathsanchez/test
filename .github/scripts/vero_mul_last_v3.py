from pathlib import Path
import ast, subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

src = Path('../.github/scripts/vero_mul_last_v2.py').read_text()
tree = ast.parse(src)
code = None
for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='code':
        code = node.value.value
assert code
old = """          have htail : Galoistools.zipAddPad p xs ys ≠ [] := by
            intro hz
            have hl := congrArg List.length hz
            rw [zipAddPad_length] at hl
            simp at hl
            have hmax := Nat.le_max_right xs.length ys.length
            omega
"""
new = """          have htail : Galoistools.zipAddPad p xs ys ≠ [] := by
            cases xs <;> cases ys <;> simp_all [Galoistools.zipAddPad]
"""
code = code.replace(old,new)
bench=Path('benchmarks/galoistools').resolve(); seed=read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
out=Path('mul_last_v3/source').resolve(); create_sandbox(bench,out,mode='codeproof',overwrite=True,seed_artifact=seed)
p=out/'Probe.lean'; p.write_text(code)
cp=subprocess.run(['lake','lean',p.name],cwd=out,text=True,capture_output=True); raw=cp.stdout+'\n'+cp.stderr
Path('mul_last_v3').mkdir(exist_ok=True); Path('mul_last_v3/census.json').write_text(json.dumps([{'exit':cp.returncode,'raw_tail':'\n'.join(raw.splitlines()[-300:]) if cp.returncode else ''}],indent=2))
print('MUL_LAST_V3_EXIT',cp.returncode); print(raw if cp.returncode else '')
