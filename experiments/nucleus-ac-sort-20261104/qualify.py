"""Sort-parameter record admission, reusing canonical-K qualification gates."""
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('canonical_k', ROOT.parent / 'nucleus-k-canonical-20261104/qualify.py')
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)
C.OUT = Path('/tmp/nucleus-ac-sort-qualified')
Q = C.Q
SOURCE_SHA = 'e08afe0a4ce9c0cd64308ee6eef52d0952316784d72175c843846762e2eb4d0b'

def gate(binary, env):
    source = Path('/tmp/ac-prefix.ndjson')
    assert Q.t.digest(source) == SOURCE_SHA
    prior = json.loads(Path('/tmp/k-qualified/qualification.json').read_text())['candidate']
    assert prior['qualified']
    pins = json.loads((ROOT / 'canonical-pins.json').read_text())
    assert prior['source_patch_sha'] == pins['source_patch_sha']
    assert prior['binary_sha'] == pins['binary_sha']
    baseline = Path('/tmp/k-qualified/candidate/nucleus')
    assert Q.t.digest(baseline) == pins['binary_sha']
    baseline.chmod(0o755)
    earlier = json.loads(Path('/tmp/k-qualified/differential.json').read_text())
    assert len(earlier['rows']) == 12 and all(row['pass_'] for row in earlier['rows'])
    red = Q.t.measure(baseline, source, env, C.OUT / 'red-ac', timeout=180, perf=False)
    assert red['rc'] == 2 and 'Lean.Data.AC.Context' in (C.OUT / 'red-ac/stderr').read_text()
    cases = C.OUT / 'ac-inputs'
    subprocess.run(['python3',str(C.ROOT / 'generate.py'),'--source',str(source),'--out',str(cases),'--record'],check=True)
    manifest = json.loads((cases / 'inputs.json').read_text())
    assert len(manifest) == 9
    reference = Path('/tmp/k-reference/bundle/kernel')
    assert Q.t.digest(reference) == C.REF_SHA
    C.check_controls(binary,manifest,cases,env,'ac_gate.json','ac-differential',dict(baseline_pins=pins,red=red))

if __name__ == '__main__':
    C.main(additional_patch=ROOT / 'sort-carrier.patch', additional_gate=gate)
    protected = json.loads((C.OUT / 'qualification.json').read_text())['candidate']
    controls = json.loads((C.OUT / 'ac_gate.json').read_text())
    assert len(controls['rows']) == 9 and all(row['pass_'] for row in controls['rows'])
    Q.t.write_json(C.OUT / 'ac_qualification.json', dict(status='WARRANTED_BOUNDED',
        ac_controls=9, retained_k_controls=12, qualified=protected['qualified'],
        binary_sha=protected['binary_sha'], source_patch_sha=protected['source_patch_sha'],
        full=json.loads((C.OUT / 'full.json').read_text())))
