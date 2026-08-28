from pathlib import Path
import ast, json, hashlib, re, subprocess
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench = Path('benchmarks/galoistools').resolve()
basep = Path('../baseline28/allin_artifact.json').resolve()
d = json.loads(basep.read_text())

def set_slot(file, key, def_name, body):
    for s in d['slots']:
        if s['file'] == file and s['key'] == key and s.get('def_name') == def_name:
            lines = body.splitlines()
            s['body_lines'] = lines
            s['body_hash'] = hashlib.sha1(('\n'.join(lines)).encode()).hexdigest()
            s['is_empty'] = False
            s['contains_sorry'] = 'sorry' in body
            s['contains_axiom'] = 'axiom' in body
            s['contains_admit'] = 'admit' in body
            print('PATCHED', file, key, def_name)
            return
    raise RuntimeError((file, key, def_name))

def literal_assignment(path, name):
    tree = ast.parse(Path(path).read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == name:
            return ast.literal_eval(node.value)
    raise RuntimeError((path, name))

def strip_imports(s):
    return '\n'.join(line for line in s.splitlines() if not line.startswith('import '))

def strip_namespace_lines(s):
    out = []
    for line in s.splitlines():
        t = line.strip()
        if t.startswith('namespace '):
            continue
        if t.startswith('end ') and len(t.split()) == 2:
            continue
        out.append(line)
    return '\n'.join(out)

# Reassemble exactly the helper stack used by the green V8 probe.
src = Path('../.github/scripts/vero_msi_gfmul_unit_lift_v1.py').read_text()
m = re.search(r"base = m.group\(1\).*?extra = r'''(.*)'''\n\nprobe = base \+ extra", src, re.S)
if not m:
    raise RuntimeError('could not extract unit-lift extra')
extra = strip_imports(m.group(1)).replace('\nend GaloistoolsMSIGfMulScaleBothV1\n', '\n')

src0 = Path('../.github/scripts/vero_msi_gfmul_scale_both_v1.py').read_text()
m0 = re.search(r"probe = r'''(.*)'''\n\np = out", src0, re.S)
if not m0:
    raise RuntimeError('could not extract gfMul base')
base = m0.group(1).replace('\nend GaloistoolsMSIGfMulScaleBothV1\n', '\n')

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

direct_src = Path('../.github/scripts/vero_monic_mul_associate_direct_v1.py').read_text()
direct_tree = ast.parse(direct_src)
final = None
for node in direct_tree.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'final':
        final = ast.literal_eval(node.value)
        break
if final is None:
    raise RuntimeError('could not extract V8 final block')

mt = re.search(r"theorem prove_monic_mul_associate_msi_v8 : spec_monic_mul_associate canonical := by\n(.*?)\n\nend GaloistoolsMSIGfMulScaleBothV1", final, re.S)
if not mt:
    raise RuntimeError('could not extract V8 theorem body')
proof_body = mt.group(1)
final_aux = final[:mt.start()] + '\n'

# Put every focused helper in one fresh namespace, avoiding collisions with the
# already-promoted 27-proof baseline. Unqualified references remain valid inside
# this namespace; opening it at the end exposes them to the target theorem.
helper_stack = base + extra + unit + '\nend GaloistoolsMSIGfMulScaleBothV1\n\n' + scalar + selected + final_aux
helper_stack = strip_imports(helper_stack)
helper_stack = strip_namespace_lines(helper_stack)
proof_aux = 'namespace MonicMulAssociateV8\n' + helper_stack + '\nend MonicMulAssociateV8\nopen MonicMulAssociateV8\n'

set_slot('Galoistools/Proof/Ring.lean', 'proof_aux', 'prove_monic_mul_associate', proof_aux)
set_slot('Galoistools/Proof/Ring.lean', 'proof', 'prove_monic_mul_associate', proof_body)

patched = Path('allin28_artifact.json').resolve()
patched.write_text(json.dumps(d, indent=2))
seed = read_artifact(patched)
out = Path('galoistools_allin28').resolve()
create_sandbox(bench, out, mode='codeproof', overwrite=True, seed_artifact=seed)

cp = subprocess.run(['lake', 'build'], cwd=out, text=True, capture_output=True)
raw = cp.stdout + '\n' + cp.stderr
print('MONIC_MUL_ASSOCIATE_PROMOTE_V1_EXIT', cp.returncode)
print(raw[-50000:])

filled = sum(1 for s in d['slots'] if not s.get('is_empty', True))
proof_filled = sum(1 for s in d['slots'] if s.get('key') == 'proof' and not s.get('is_empty', True))
print('FILLED_SLOTS', filled)
print('PROOF_SLOTS_FILLED', proof_filled)
Path('promotion_result.json').write_text(json.dumps({'exit': cp.returncode, 'filled_slots': filled, 'proof_slots_filled': proof_filled, 'tail': raw[-60000:]}, indent=2))
