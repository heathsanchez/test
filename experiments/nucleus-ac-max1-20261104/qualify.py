"""Source-derived max(1,u) record qualification on canonical K and p1 record gates.

Prior canonical-K and AC.Context official differential controls run fresh.  This
new gate must pass its own pinned source RED/GREEN, official Lean comparisons,
and then the unchanged native/Arena/full Mathlib qualification.  No proof-result
cache, named-declaration whitelist, or preaccepted theorem is installed.
"""

import importlib.util
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    'ac_sort_qualification', ROOT.parent / 'nucleus-ac-sort-20261104/qualify.py')
AC = importlib.util.module_from_spec(spec)
spec.loader.exec_module(AC)
C, Q = AC.C, AC.Q
OUT = Path('/tmp/nucleus-ac-max1-qualified')
SOURCE_SHA = 'e7daddaf05fa799dc248bb3f10a502fd5ab5569561a4502d9f48de63256f3113'
PRIOR_BIN_SHA = '582dd0ac17d664202a39ee7daa69b640f33916374fc44dbefdc96a37e8bcb238'
PRIOR_PATCH_SHA = 'c25db576b5b52ed6e76711b9e83e66731bd40c68b7aa6627d45ad751c769ba69'
PRIOR_ZIP_SHA = 'a891c75dbcabd6fddfbbcc5b9ea6826a68b53cf51ae1fbc6e50fdae5d23c104e'


def new_gate(binary, env):
    # Re-qualify both earlier source-family tests against *this* candidate.
    AC.gate(binary, env)
    source = Path('/tmp/contextinfo-prefix.ndjson')
    assert Q.t.digest(source) == SOURCE_SHA
    prior = json.loads(Path('/tmp/ac-sort-prior/qualification.json').read_text())['candidate']
    assert prior['qualified'] and prior['binary_sha'] == PRIOR_BIN_SHA
    assert prior['source_patch_sha'] == PRIOR_PATCH_SHA
    old = Path('/tmp/ac-sort-prior/candidate/nucleus')
    assert Q.t.digest(old) == PRIOR_BIN_SHA
    old.chmod(0o755)
    red = Q.t.measure(old, source, env, OUT / 'red-max1', timeout=180, perf=False)
    assert red['rc'] == 2 and 'Lean.Data.AC.ContextInformation' in (
        OUT / 'red-max1/stderr').read_text()
    cases = OUT / 'max1-inputs'
    subprocess.run([
        'python3', str(C.ROOT / 'generate.py'), '--source', str(source),
        '--out', str(cases), '--max1'], check=True)
    manifest = json.loads((cases / 'inputs.json').read_text())
    assert len(manifest) == 9
    reference = Path('/tmp/k-reference/bundle/kernel')
    assert Q.t.digest(reference) == C.REF_SHA
    rows = []
    for case in manifest:
        fixture = cases / case['file']
        assert Q.t.digest(fixture) == case['sha256']
        stem = OUT / 'max1-differential' / case['case']
        parse = C.captured([str(reference), '--parse-only', str(fixture)], stem / 'parse')
        ref_rc = C.captured([str(reference), str(fixture)], stem / 'reference')
        with fixture.open('rb') as stream:
            rc = C.captured([str(binary)], stem / 'nucleus', env=env, stdin=stream)
        passed = (parse == 0 and ref_rc == case['expect_reference']
                  and (rc == 0 if ref_rc == 0 else rc in (1, 2)))
        rows.append(dict(case, reference_parse_rc=parse,
                         reference_rc=ref_rc, nucleus_rc=rc, pass_=passed))
        Q.t.write_json(OUT / 'max1_gate.json', dict(
            source_sha=SOURCE_SHA, prior_binary=PRIOR_BIN_SHA, red=red,
            candidate_binary=Q.t.digest(binary), rows=rows))
        print('MAX1_SOURCE_CONTROL', json.dumps(rows[-1]), flush=True)
        assert passed, 'Source-derived max-one differential control failed'


def main():
    OUT.mkdir(exist_ok=True)
    C.OUT = OUT
    source_patch = ROOT.parent / 'nucleus-ac-sort-20261104/sort-carrier.patch'
    # Apply in two fail-closed patch invocations: the second diff is defined
    # against the already-extended one-parameter source tree.
    C.main(additional_patch=[source_patch, ROOT / 'max1.patch'],
           additional_gate=new_gate)
    protected = json.loads((OUT / 'qualification.json').read_text())['candidate']
    full = json.loads((OUT / 'full.json').read_text())
    source = json.loads((OUT / 'max1_gate.json').read_text())
    assert protected['qualified'] and full['qualified']
    assert len(source['rows']) == 9 and all(row['pass_'] for row in source['rows'])
    summary = dict(status='WARRANTED_BOUNDED', prior_binary_sha=PRIOR_BIN_SHA,
                   source_sha=SOURCE_SHA, official_max_one_controls=9,
                   retained_ac_controls=9, retained_canonical_k_controls=12,
                   candidate_binary_sha=protected['binary_sha'],
                   candidate_patch_sha=protected['source_patch_sha'],
                   native_nonregression=protected['native_nonregression'],
                   source_controls_unchanged=protected['controls_unchanged'],
                   arena_verdict_changes=protected['verdict_changes'],
                   complete_mathlib_accept=full['complete_mathlib_accept'],
                   terminal=full['terminal'], next_frontier=full['next_frontier'])
    Q.t.write_json(OUT / 'max1_qualification.json', summary)
    print('MAX1_PROTECTED_QUALIFICATION', json.dumps(summary), flush=True)


if __name__ == '__main__':
    main()
