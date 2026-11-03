"""Source-derived max(1,u) record qualification on canonical K and p1 record gates.

Prior canonical-K and AC.Context official differential controls run fresh.  This
new gate must pass its own pinned source RED/GREEN, official Lean comparisons,
and then the unchanged native/Arena/full Mathlib qualification.  No proof-result
cache, named-declaration whitelist, or preaccepted theorem is installed.
"""

import importlib.util
import difflib
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


def extend_max_one_source(kernel, arm):
    """Select source max(1,u) records without changing the signature verifier."""
    path = kernel / 'src/checker.rs'
    before = path.read_text()
    helper = '''// Exact source universe form for records in Sort (max 1 u).
// Constructor, recursor and field obligations remain fully checked below.
fn is_sort_max_one_parameter(export:&ResolvedExport,expression:ExprId,parameter:NameId)->bool {
    let Some(Expr::Sort(level))=export.exprs.get(expression) else{return false;};
    let Some(Level::Max(one,carrier))=export.levels.get(*level) else{return false;};
    matches!(export.levels.get(*one),Some(Level::Succ(zero)) if matches!(export.levels.get(*zero),Some(Level::Zero)))
        && matches!(export.levels.get(*carrier),Some(Level::Param(name)) if *name==parameter)
}

'''
    scope_start = 'fn parameter_record_scope(export:&ResolvedExport,block:&InductiveBlock)->bool {'
    candidate_start = 'fn parameter_record_candidate(export:&ResolvedExport,block:&InductiveBlock)->bool {'
    assert before.count(scope_start) == before.count(candidate_start) == 1
    start, stop = before.index(scope_start), before.index(candidate_start)
    scope = before[start:stop]
    old_scope = '        && is_sort_succ_parameter(export,result,inductive.level_params[0])'
    assert scope.count(old_scope) == 1
    scope = scope.replace(old_scope,
        '        && (is_sort_succ_parameter(export,result,inductive.level_params[0])\n'
        '            || (inductive.num_params==1 && is_sort_parameter(export,parameters[0],inductive.level_params[0])\n'
        '                && is_sort_max_one_parameter(export,result,inductive.level_params[0])))', 1)
    after = before[:start] + helper + scope + before[stop:]
    candidate = after.index(candidate_start)
    candidate_end = after.find('\nfn ', candidate + 1)
    assert candidate_end > candidate
    section = after[candidate:candidate_end]
    old_candidate = 'is_sort_succ_parameter(export,result,universe)'
    assert section.count(old_candidate) == 1
    section = section.replace(old_candidate,
        '(is_sort_succ_parameter(export,result,universe)\n'
        '            || (p==1 && is_sort_parameter(export,parameters[0],universe)\n'
        '                && is_sort_max_one_parameter(export,result,universe)))', 1)
    after = after[:candidate] + section + after[candidate_end:]
    assert before != after
    path.write_text(after)
    diff = ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
        fromfile='a/metatron-kernel/src/checker.rs',
        tofile='b/metatron-kernel/src/checker.rs'))
    (arm / 'max-one-source.patch').write_text(diff)
    with (arm / 'source.patch').open('a') as stream:
        stream.write(diff)


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
    # Apply p1's previously qualified source diff, then derive one extra
    # patch with exact anchors in that already patched source. Mismatched
    # anchors abort before any checker is built or a verdict is issued.
    C.main(additional_patch=[source_patch, extend_max_one_source],
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
