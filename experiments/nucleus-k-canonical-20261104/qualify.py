"""Canonical source-derived nullary Prop K, with fresh official differential controls."""
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('qualified_delta', ROOT.parent / 'nucleus-beq-neutral-delta-20261104/qualify.py')
Q = importlib.util.module_from_spec(spec)
spec.loader.exec_module(Q)
OUT = Path('/tmp/nucleus-k-canonical-qualified')
DELTA_SHA = '33e039f3a2fdd9e18b223a428531ca689583a2c9bfb4f8143123f13dc532eaa4'
DELTA_PATCH = 'a788f92fd0471f1dc20cce9f42f8c94f9e3309ea1becb1da1ecd88aa5a9b58a6'
REF_SHA = 'ae92c625e612fff1c90e329344d22e3c3c330383cb335ce28fd41435be3b3b94'

def captured(command, target, timeout=180, **kwargs):
    target.parent.mkdir(parents=True, exist_ok=True)
    result = Q.t.run_group(command, capture_output=True, timeout=timeout, **kwargs)
    target.with_suffix('.stdout').write_bytes(result.stdout)
    target.with_suffix('.stderr').write_bytes(result.stderr)
    return result.returncode

def main(additional_patch=None, additional_gate=None):
    OUT.mkdir(exist_ok=True)
    Q.OUT = OUT
    prior = json.loads(Path('/tmp/delta-qualified/qualification.json').read_text())['candidate']
    assert prior['qualified'] and prior['binary_sha'] == DELTA_SHA
    assert prior['source_patch_sha'] == DELTA_PATCH
    old = Path('/tmp/delta-qualified/candidate/nucleus')
    assert Q.t.digest(old) == DELTA_SHA
    old.chmod(0o755)
    reference = Path('/tmp/k-reference/bundle/kernel')
    assert Q.t.digest(reference) == REF_SHA
    reference.chmod(0o755)
    original_patch, original_build = Q.D.patch_source, Q.source_qualified_candidate

    def composite(kernel, arm):
        original_patch(kernel, arm)
        assert Q.t.digest(arm / 'source.patch') == DELTA_PATCH
        patch = ROOT / 'k-canonical.patch'
        result = Q.t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(patch)], cwd=arm, capture_output=True, timeout=30)
        (arm / 'k-canonical.patch.log').write_bytes(result.stdout + result.stderr)
        assert result.returncode == 0, (result.stdout, result.stderr)
        (arm / 'k-canonical.patch').write_text(patch.read_text())
        with (arm / 'source.patch').open('a') as stream:
            stream.write(patch.read_text())
        if additional_patch is not None:
            patches = [additional_patch] if isinstance(additional_patch, Path) else list(additional_patch)
            for index, patch in enumerate(patches):
                result = Q.t.run_group(['patch','--batch','--fuzz=0','-p1','-i',str(patch)], cwd=arm, capture_output=True, timeout=30)
                (arm / f'additional-{index}.patch.log').write_bytes(result.stdout + result.stderr)
                assert result.returncode == 0, (result.stdout, result.stderr)
                (arm / f'additional-{index}.patch').write_text(patch.read_text())
                with (arm / 'source.patch').open('a') as stream:
                    stream.write(patch.read_text())

    def build_and_protect(baseline):
        kernel, binary, build_env, arm = original_build(baseline)
        env = Q.R.N.runtime(True)
        assert {k:v for k,v in env.items() if k.startswith('NUCLEUS_')} == prior['configuration']
        env['NUCLEUS_TRACE_DOWNSTREAM'] = '1'
        if additional_gate is not None:
            additional_gate(binary, env)
        cases = OUT / 'differential-inputs'
        subprocess.run(['python3', str(ROOT / 'generate.py'), '--source','/tmp/std-prefix.ndjson','--out',str(cases)], check=True)
        manifest = json.loads((cases / 'inputs.json').read_text())
        assert len(manifest) == 10
        closed = cases / 'closed'
        subprocess.run(['python3', str(ROOT / 'generate.py'), '--source','/tmp/std-prefix.ndjson','--out',str(closed),'--closed'], check=True)
        for row in json.loads((closed / 'inputs.json').read_text()):
            row['file'] = 'closed/' + row['file']
            manifest.append(row)
        assert len(manifest) == 12
        red = Q.t.measure(old, Path('/tmp/std-prefix.ndjson'), env, OUT / 'red-std', timeout=180, perf=False)
        assert red['rc'] == 2 and 'Std.LeftIdentity' in (OUT / 'red-std/stderr').read_text()
        rows = []
        for case in manifest:
            source = cases / case['file']
            assert Q.t.digest(source) == case['sha256']
            stem = OUT / 'differential' / case['case']
            parse = captured([str(reference),'--parse-only',str(source)], stem / 'parse')
            ref_rc = captured([str(reference),str(source)], stem / 'reference')
            with source.open('rb') as stream:
                rc = captured([str(binary)], stem / 'nucleus', env=env, stdin=stream)
            passed = parse == 0 and ref_rc == case['expect_reference'] and (rc == 0 if ref_rc == 0 else rc in (1,2))
            rows.append(dict(case, reference_parse_rc=parse, reference_rc=ref_rc, nucleus_rc=rc, pass_=passed))
            Q.t.write_json(OUT / 'differential.json', dict(reference_binary=REF_SHA, candidate_binary=Q.t.digest(binary), rows=rows))
            print('K_CANONICAL_CONTROL', json.dumps(rows[-1]), flush=True)
        assert all(row['pass_'] for row in rows), 'Blocked: source differential controls failed'
        return kernel, binary, build_env, arm

    Q.D.patch_source, Q.source_qualified_candidate = composite, build_and_protect
    try:
        Q.main()
    finally:
        Q.D.patch_source, Q.source_qualified_candidate = original_patch, original_build
    protected = json.loads((OUT / 'qualification.json').read_text())['candidate']
    assert protected['qualified']
    full = json.loads((OUT / 'full.json').read_text())
    Q.t.write_json(OUT / 'canonical_qualification.json', dict(status='WARRANTED_BOUNDED',
        differential_controls=12, native_nonregression=protected['native_nonregression'],
        controls_unchanged=protected['controls_unchanged'], corpus_changes=protected['verdict_changes'],
        extra_unchanged=protected['extra_unchanged'], binary_sha=protected['binary_sha'],
        source_patch_sha=protected['source_patch_sha'], full=full))

if __name__ == '__main__':
    main()
