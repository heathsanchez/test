from pathlib import Path
import json, subprocess, sys

# Reconstruct the certified 25/48 source first.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import vero_galoistools_allin as base

out = Path('galoistools_allin/source').resolve()
impl = out / 'Galoistools/Impl/Division.lean'
proof = out / 'Galoistools/Proof/Division.lean'
orig_impl = impl.read_text()
orig_proof = proof.read_text()


def replace_code(text, name, body):
    start = f'-- !benchmark @start code def={name}'
    end = f'-- !benchmark @end code def={name}'
    a = text.index(start) + len(start)
    b = text.index(end, a)
    return text[:a] + '\n' + body.rstrip() + '\n' + text[b:]


def replace_proof(text, name, body):
    start = f'-- !benchmark @start proof def={name}'
    end = f'-- !benchmark @end proof def={name}'
    a = text.index(start) + len(start)
    b = text.index(end, a)
    return text[:a] + '\n' + body.rstrip() + '\n' + text[b:]

variants = {
  'symmetric_unit_fallback': '''  fun f g p =>
    if f = [] ∧ g = [] then []
    else if f = g then (Galoistools.gfMonic f p).2
    else if f = [] then (Galoistools.gfMonic g p).2
    else if g = [] then (Galoistools.gfMonic f p).2
    else [1]''',
  'unit_fallback_no_left_zero': '''  fun f g p =>
    if f = [] ∧ g = [] then []
    else if f = g then (Galoistools.gfMonic f p).2
    else if g = [] then (Galoistools.gfMonic f p).2
    else [1]''',
}

targets = ['prove_gcd_divides_both','prove_gcd_maximal','prove_gcd_comm','prove_gcd_degree_le_inputs','prove_gcd_roots_common']
results=[]

for vname, gfbody in variants.items():
    print('VARIANT', vname)
    impl.write_text(replace_code(orig_impl, 'gfGcd', gfbody))
    proof.write_text(orig_proof)
    build = subprocess.run(['lake','build'], cwd=out, text=True, capture_output=True)
    item={'variant':vname,'ratchet_build_exit':build.returncode,'targets':[]}
    print('RATCHET_BUILD_EXIT', build.returncode)
    if build.returncode != 0:
        raw=build.stdout+'\n'+build.stderr
        item['ratchet_errors']=[x for x in raw.splitlines() if 'error:' in x or 'error(' in x][-8:]
        results.append(item)
        continue
    for name in targets:
        ptxt = proof.read_text()
        spec='spec_'+name[len('prove_'):]
        candidates = [
          ('simp', f'  simp [{spec}, canonical, Galoistools.gfGcd]'),
          ('intro_simp', f'  intro f g p\n  simp [{spec}, canonical, Galoistools.gfGcd]') if name == 'prove_gcd_comm' else ('simp_only', f'  simp [{spec}, canonical]'),
        ]
        hits=[]
        probes=[]
        for cname, body in candidates:
            proof.write_text(replace_proof(ptxt,name,body))
            q=subprocess.run(['lake','lean','Galoistools/Proof/Division.lean'],cwd=out,text=True,capture_output=True)
            raw=q.stdout+'\n'+q.stderr
            errs=[x for x in raw.splitlines() if 'error:' in x or 'error(' in x]
            probes.append({'candidate':cname,'exit':q.returncode,'errors':errs[-3:]})
            if q.returncode==0: hits.append(cname)
        proof.write_text(ptxt)
        item['targets'].append({'proof':name,'hits':hits,'probes':probes})
        print('TARGET',name,'HITS',hits)
    results.append(item)

impl.write_text(orig_impl)
proof.write_text(orig_proof)
Path('galoistools_allin/gcd_boundary_separator.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
