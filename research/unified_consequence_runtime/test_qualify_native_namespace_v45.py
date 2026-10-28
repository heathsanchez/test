"""Fail-closed qualification controls; no fixture-native result is supplied."""
from __future__ import annotations

import copy
import base64
import importlib
import json
import shutil
from pathlib import Path

import pytest

from .native_v45_test_support import project_factory, modern_environment


HERE = Path(__file__).resolve().parent


def qualifier():
    name = 'research.unified_consequence_runtime.qualify_native_namespace_v45'
    assert (HERE/'qualify_native_namespace_v45.py').is_file(), 'V45 qualifier is not implemented'
    return importlib.import_module(name)


def baseline():
    # The final entry represents files added after the old V44 2628-file guard.
    return {f'original/{number}': {'mode': '100644', 'kind': 'blob', 'oid': f'{number:040x}'}
            for number in range(3011)}


def test_complete_baseline_allows_only_new_paths():
    current = qualifier()
    before = baseline()
    after = {**before, 'new/extension.py': {'mode': '100644', 'kind': 'blob', 'oid': 'f'*40}}
    assert current._preserve_baseline(before, after) == 3011


@pytest.mark.parametrize('change', ('delete', 'bytes', 'mode'))
def test_complete_baseline_rejects_late_file_loss_or_change(change):
    current = qualifier()
    before = baseline()
    after = copy.deepcopy(before)
    if change == 'delete':
        after.pop('original/3010')
    else:
        after['original/3010']['mode' if change == 'mode' else 'oid'] = '100755' if change == 'mode' else 'f'*40
    with pytest.raises(ValueError, match='3011|baseline'):
        current._preserve_baseline(before, after)


def test_shorter_historical_baseline_cannot_claim_current_preservation():
    current = qualifier()
    before = baseline()
    before.pop('original/3010')
    with pytest.raises(ValueError, match='3011|baseline'):
        current._preserve_baseline(before, before)


def test_exact_independently_sealed_pack_is_accepted():
    current = qualifier()
    value = current.sealed_controls(HERE/'archaeology/native-namespace-v45/control-freeze')
    assert value['seal_sha256'] == '48584499e067742a877b0ebf3c662ab96004e4ed628ebdc88a68bb42dbed2cce'
    assert len(value['files']) == 257
    assert value['source_cases'] == 30 and value['replay_controls'] == 18


@pytest.mark.parametrize('change', ('seal', 'fixture', 'extra', 'symlink', 'mode'))
def test_changed_sealed_control_pack_is_rejected(tmp_path, change):
    current = qualifier()
    pack = tmp_path/'pack'
    shutil.copytree(HERE/'archaeology/native-namespace-v45/control-freeze', pack)
    fixture = pack/'fixtures/W01_production_constant_wildcard/augmented/library/constants.py'
    if not fixture.exists():
        fixture = next((pack/'fixtures').rglob('constants.py'))
    if change == 'seal':
        with (pack/'FINAL_SEAL.json').open('ab') as stream:
            stream.write(b' ')
    elif change == 'fixture':
        fixture.write_bytes(fixture.read_bytes()+b'\n')
    elif change == 'extra':
        (pack/'unsealed.py').write_text('VALUE = 1\n')
    elif change == 'mode':
        fixture.chmod(fixture.stat().st_mode | 0o111)
    else:
        raw = fixture.read_bytes()
        target = tmp_path/'redirect.py'
        target.write_bytes(raw)
        fixture.unlink()
        fixture.symlink_to(target)
    with pytest.raises(ValueError, match='seal|control|fixture'):
        current.sealed_controls(pack)


@pytest.mark.parametrize('field', ('source_commit', 'files', 'source_tree', 'baseline_commit'))
def test_freeze_rejects_changed_source_identity(field):
    current = qualifier()
    source = {'source_commit': 'a'*40, 'files': {'a.py': 'b'*64},
              'source_tree': {'a.py': {'mode': '100644', 'oid': 'c'*40}},
              'baseline_commit': current.BASE}
    frozen = copy.deepcopy(source)
    frozen[field] = 'forged'
    with pytest.raises(ValueError, match='source|freeze'):
        current._check_source_identity(frozen, source)


def test_dynamic_inventory_requires_exact_complete_execution():
    current = qualifier()
    nodes = ['suite.py::test_a', 'suite.py::test_b']
    reports = [{'nodeid': node, 'when': phase, 'outcome': 'passed', 'wasxfail': ''}
               for node in nodes for phase in ('setup', 'call', 'teardown')]
    record = {'collection': nodes, 'reports': reports,
              'junit': {'tests': 2, 'passed': 2, 'failures': 0, 'errors': 0, 'skipped': 0},
              'pytest_exit_code': 0}
    current._validate_contracts(record, nodes, ['suite.py'])
    changed = copy.deepcopy(record)
    changed['collection'].pop()
    with pytest.raises(ValueError, match='collection|inventory'):
        current._validate_contracts(changed, nodes, ['suite.py'])
    changed = copy.deepcopy(record)
    changed['reports'][1]['wasxfail'] = 'expected failure'
    with pytest.raises(ValueError, match='report|execution'):
        current._validate_contracts(changed, nodes, ['suite.py'])


@pytest.mark.parametrize('claim', ('scope', 'verdict', 'native', 'replay', 'compiler', 'index'))
def test_qualification_claims_require_real_complete_bounded_evidence(claim):
    current = qualifier()
    record = {'scope': current.SCOPE, 'verdicts': {f'G{i}': 'UNKNOWN' for i in range(2, 7)},
              'prospective_task_sources_accessed': False, 'coding_agent_executed': False,
              'native_attempts': {'delta': {'native_calls': 2, 'collection_calls': 1}},
              'compilation_attempts': {'delta': {'compilation_calls': 1, 'compilation_seconds': 0.5}},
              'raw_native_audit': {'native_passes': 1, 'native_failures': 1, 'independent_replays': 1},
              'index_audit': {'changes': []}}
    if claim == 'scope':
        record['scope'] = 'DEVELOPMENTAL_DISCOVERY'
    elif claim == 'verdict':
        record['verdicts']['G2'] = 'PASS'
    elif claim == 'native':
        record['raw_native_audit']['native_failures'] = 0
    elif claim == 'replay':
        record['raw_native_audit']['independent_replays'] = 0
    elif claim == 'compiler':
        record['compilation_attempts']['delta']['compilation_calls'] = 0
    else:
        record['index_audit']['changes'] = [{'changed': 'index'}]
    with pytest.raises(ValueError, match='scope|UNKNOWN|native|replay|compiler|index'):
        current._validate_claims(record)


def test_archive_reuses_original_algorithm_and_separates_v45_artifact_name():
    current = qualifier()
    original = importlib.import_module('research.unified_consequence_runtime.qualify_experiment_interface_v43')
    assert current.original is original
    assert current.archive.__code__.co_code == original.archive.__code__.co_code
    assert 'NATIVE_NAMESPACE_V45_EVIDENCE.tar.gz' in current.archive.__code__.co_consts


def claim_record(current):
    child = {'path': '/synthetic/CHILD_NATIVE_ATTEMPTS.json', 'sha256': 'd'*64,
             'stdout': {'path': '/synthetic/RESTART_STDOUT.log', 'sha256': 'e'*64},
             'stderr': {'path': '/synthetic/RESTART_STDERR.log', 'sha256': 'f'*64},
             'native_outputs': [{'path': '/synthetic/restart/native-runs/run/receipt.json', 'sha256': 'a'*64}],
             'summary': {'schema': 'UDM_NATIVE_V45_CHILD_ATTEMPTS',
                 'native_attempts': {'delta': {'native_calls': 1, 'collection_calls': 1, 'subprocess_attempts': 2}},
                 'compilation_attempts': {'delta': {'compilation_calls': 1, 'compilation_seconds': 0.5}}}}
    record = {'scope': current.SCOPE, 'verdicts': {f'G{i}': 'UNKNOWN' for i in range(2, 7)},
            'prospective_task_sources_accessed': False, 'coding_agent_executed': False,
            'native_attempts': {'scope': 'MAIN_CONTROLLER_CONTEXT_ONLY',
                                'delta': {'native_calls': 2, 'collection_calls': 1, 'subprocess_attempts': 3}},
            'compilation_attempts': {'scope': 'MAIN_CONTROLLER_CONTEXT_ONLY',
                                     'delta': {'compilation_calls': 2, 'compilation_seconds': 0.5}},
            'raw_native_audit': {'native_passes': 1, 'native_failures': 1, 'independent_replays': 1},
            'index_audit': {'changes': []}, 'child_attempts': [child]}
    record['known_attempt_totals'] = current.known_attempt_totals(
        record['native_attempts']['delta'], record['compilation_attempts']['delta'], record['child_attempts'])
    return record


def test_actual_compiler_snapshot_schema_can_support_a_bounded_claim():
    current = qualifier()
    current._validate_claims(claim_record(current))


@pytest.mark.parametrize('field', ('native_calls', 'compilation_calls', 'native_passes'))
def test_boolean_counters_cannot_support_qualification_claims(field):
    current = qualifier()
    record = claim_record(current)
    if field == 'native_calls':
        record['native_attempts']['delta'][field] = True
    elif field == 'compilation_calls':
        record['compilation_attempts']['delta'][field] = True
    else:
        record['raw_native_audit'][field] = True
    with pytest.raises(ValueError, match='native|compiler|counter'):
        current._validate_claims(record)


@pytest.fixture
def accounting_input(tmp_path):
    """Synthetic parser inputs, removed before the real qualification audit."""
    root = tmp_path/'synthetic-accounting-input'
    root.mkdir()
    try:
        yield root
    finally:
        shutil.rmtree(root)


def test_required_child_summary_cannot_be_absent(accounting_input):
    current = qualifier()
    with pytest.raises(ValueError, match='child.*missing|missing.*child'):
        current.child_attempts(accounting_input)


@pytest.mark.parametrize('change', ('delta', 'stdout', 'output_escape'))
def test_child_summary_rejects_tampered_counter_or_unbound_artifact(accounting_input, change):
    current = qualifier()
    child = {'schema': 'UDM_NATIVE_V45_CHILD_ATTEMPTS', 'status': 'PASS_NATIVE',
             'native_attempts': {'before': {'native_calls': 0, 'collection_calls': 0, 'subprocess_attempts': 0},
                                 'after': {'native_calls': 1, 'collection_calls': 1, 'subprocess_attempts': 2},
                                 'delta': {'native_calls': 1, 'collection_calls': 1, 'subprocess_attempts': 2}},
             'compilation_attempts': {'before': {'compilation_calls': 0, 'compilation_seconds': 0.0, 'records': []},
                 'after': {'compilation_calls': 1, 'compilation_seconds': 0.5, 'records': []},
                 'delta': {'compilation_calls': 1, 'compilation_seconds': 0.5}},
             'native_run_outputs': [str(accounting_input/'child-run')]}
    stdout = {'status': 'PASS_NATIVE', 'native_calls': 1, 'attempts': copy.deepcopy(child)}
    if change == 'delta':
        child['native_attempts']['delta']['native_calls'] = 2
        stdout['attempts'] = copy.deepcopy(child)
    elif change == 'stdout':
        stdout['attempts']['native_attempts']['delta']['native_calls'] = 2
    else:
        child['native_run_outputs'] = ['/tmp/not-this-qualification']
        stdout['attempts'] = copy.deepcopy(child)
    (accounting_input/'CHILD_NATIVE_ATTEMPTS.json').write_text(json.dumps(child))
    (accounting_input/'RESTART_STDOUT.log').write_text(json.dumps(stdout))
    (accounting_input/'RESTART_STDERR.log').write_text('')
    with pytest.raises(ValueError, match='child|compiler|counter'):
        current.child_attempts(accounting_input)


def test_bound_child_accounting_parser_retains_exact_artifact_descriptors(accounting_input):
    """Synthetic accounting parser inputs do not supply a native warrant."""
    current = qualifier()
    compiler = accounting_input/'compiler'
    compiler.mkdir()
    payload = {'sources': {}}
    (compiler/'compiler.py').write_text('# synthetic parser input; never executed\n')
    (compiler/'original-input.json').write_text(json.dumps(payload))
    (compiler/'expected-code.json').write_text('{}')
    (compiler/'stdout.log').write_text('')
    (compiler/'stderr.log').write_text('')
    record = {'output': str(compiler), 'compilation_calls': 1, 'seconds': 0.5,
              'compiler_sha256': current.file_sha(compiler/'compiler.py'),
              'input_sha256': current.sha(current.canonical(payload).encode()),
              'report_sha256': current.file_sha(compiler/'expected-code.json')}
    (compiler/'compilation.json').write_text(json.dumps(record))
    run = accounting_input/'restart/native-runs/synthetic'
    (run/'execution').mkdir(parents=True)
    packet = {'checked-report.json': b'{}'}
    (run/'receipt.json').write_text(json.dumps({'schema': 'UDM_GENERIC_NATIVE_PYTEST_V45', 'status': 'PASS_NATIVE',
        'costs': {'native_calls': 1, 'collection_calls': 1},
        'packet': {name: base64.b64encode(raw).decode() for name, raw in packet.items()},
        'packet_sha256': {name: current.sha(raw) for name, raw in packet.items()}}))
    for name, raw in packet.items():
        (run/'execution'/name).write_bytes(raw)
    child = {'schema': 'UDM_NATIVE_V45_CHILD_ATTEMPTS', 'status': 'PASS_NATIVE',
             'native_attempts': {'before': {'native_calls': 0, 'collection_calls': 0, 'subprocess_attempts': 0},
                                 'after': {'native_calls': 1, 'collection_calls': 1, 'subprocess_attempts': 2},
                                 'delta': {'native_calls': 1, 'collection_calls': 1, 'subprocess_attempts': 2}},
             'compilation_attempts': {'before': {'compilation_calls': 0, 'compilation_seconds': 0.0, 'records': []},
                 'after': {'compilation_calls': 1, 'compilation_seconds': 0.5, 'records': [record]},
                 'delta': {'compilation_calls': 1, 'compilation_seconds': 0.5}},
             'native_run_outputs': [str(run)]}
    (accounting_input/'CHILD_NATIVE_ATTEMPTS.json').write_text(json.dumps(child))
    (accounting_input/'RESTART_STDOUT.log').write_text(json.dumps({'status': 'PASS_NATIVE', 'native_calls': 1, 'attempts': child}))
    (accounting_input/'RESTART_STDERR.log').write_text('')
    descriptor, = current.child_attempts(accounting_input)
    assert descriptor['summary'] == child
    assert descriptor['sha256'] == current.file_sha(accounting_input/'CHILD_NATIVE_ATTEMPTS.json')
    assert descriptor['native_outputs'][0]['sha256'] == current.file_sha(run/'receipt.json')
    foreign = accounting_input/'unrelated-main-run'
    shutil.copytree(run, foreign)
    child['native_run_outputs'] = [str(foreign)]
    (accounting_input/'CHILD_NATIVE_ATTEMPTS.json').write_text(json.dumps(child))
    (accounting_input/'RESTART_STDOUT.log').write_text(json.dumps({'status': 'PASS_NATIVE', 'native_calls': 1, 'attempts': child}))
    with pytest.raises(ValueError, match='child.*output|restart'):
        current.child_attempts(accounting_input)


@pytest.mark.parametrize('field', ('child_attempts', 'known_attempt_totals'))
def test_bounded_claim_requires_complete_child_cost_accounting(field):
    current = qualifier()
    record = claim_record(current)
    record.pop(field)
    with pytest.raises(ValueError, match='child|known.*total'):
        current._validate_claims(record)


def test_raw_invocation_inventory_covers_external_inherited_unknowns_without_granting_pass(accounting_input):
    current = qualifier()
    directory = accounting_input/'default-temporaries/inherited-v45-evidence/case/native/execution'
    directory.mkdir(parents=True)
    raw = {'mode': 'run', 'selected_test_nodes': [], 'collection_errors': ['diagnostic refusal']}
    checked = dict(raw, timeout=False, process_exit_code=2, source_mutations=[], unexpected_imports=[],
                   costs={'native_calls': 1, 'collection_calls': 0, 'seconds': 0.25, 'horizon_seconds': 10})
    (directory/'report.json').write_text(json.dumps(raw))
    (directory/'checked-report.json').write_text(json.dumps(checked))
    (directory/'stdout.log').write_text('')
    (directory/'stderr.log').write_text('diagnostic refusal')
    (directory/'tracked-source-manifest.json').write_text('[]')
    inventory = current.native_invocation_inventory(accounting_input)
    assert inventory['native_calls'] == 1 and inventory['collection_calls'] == 0
    assert inventory['invocations'][0]['path'] == str(directory)
    assert inventory['invocations'][0]['classification'] == 'RAW_INVOCATION_ONLY_NO_ADMISSION_WARRANT'
    assert 'native_passes' not in inventory


@pytest.mark.parametrize('version', ('V2', 'V42', 'V43', 'V45'))
def test_malformed_retained_receipt_fails_closed_with_exact_binding_diagnostic(accounting_input, version):
    """A parser fixture cannot be mistaken for authentic native execution."""
    current = qualifier()
    path = accounting_input/'synthetic-parser-input/restart/native-run/receipt.json'
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'schema': 'UDM_GENERIC_NATIVE_PYTEST_'+version, 'status': 'PASS_NATIVE'}))
    with pytest.raises(ValueError, match='native receipt certificate binding missing') as caught:
        current.audit_native_packets(accounting_input, {})
    assert str(path) in str(caught.value)


def test_known_attempt_totals_sum_calls_and_keep_overlapping_intervals_explicit():
    current = qualifier()
    main_native = {'native_calls': 4, 'collection_calls': 3, 'subprocess_attempts': 7}
    main_compiler = {'compilation_calls': 5, 'compilation_seconds': 0.75}
    children = [{'summary': {'native_attempts': {'delta': {'native_calls': 1, 'collection_calls': 1, 'subprocess_attempts': 2}},
                            'compilation_attempts': {'delta': {'compilation_calls': 2, 'compilation_seconds': 0.25}}}}]
    totals = current.known_attempt_totals(main_native, main_compiler, children)
    assert totals['native_calls'] == 5 and totals['collection_calls'] == 4
    assert totals['compilation_calls'] == 7
    assert totals['wall_intervals_additive'] is False


def test_truncated_native_xml_remains_an_explicit_partial_invocation(accounting_input):
    current = qualifier()
    directory = accounting_input/'partial-run'
    directory.mkdir()
    raw = {'mode': 'run'}
    checked = dict(raw, timeout=True, process_exit_code=-9, source_mutations=[], unexpected_imports=[],
                   costs={'native_calls': 1, 'collection_calls': 0, 'seconds': 1.0, 'horizon_seconds': 1})
    for name, data in [('report.json', raw), ('checked-report.json', checked), ('tracked-source-manifest.json', [])]:
        (directory/name).write_text(json.dumps(data))
    (directory/'stdout.log').write_text('')
    (directory/'stderr.log').write_text('')
    (directory/'native.xml').write_text('<testsuite><testcase')
    inventory = current.native_invocation_inventory(accounting_input)
    assert inventory['native_calls'] == 1
    assert inventory['invocations'][0]['packet_status'] == 'UNKNOWN_PARTIAL_NATIVE_PACKET'


def test_real_inherited_packets_outside_pytest_have_unique_native_outcomes(project_factory, modern_environment, tmp_path):
    current = qualifier()
    from . import native_v45_test_support as support
    worker = support.implementation()
    case = support.ordinary_case(project_factory,
        b'from subject import value\ndef test_contract():\n    assert value() == 1\n')
    output = tmp_path/'default-temporaries/inherited-v45-evidence'
    certificate, failed = support.collect_and_run(case, output/'failed')
    # The inherited original methods retain truthful raw wrappers without the
    # success helper's manifest. Exercise that exact discovery boundary.
    (output/'failed/V45_NATIVE_EVIDENCE.json').rename(output/'failed/UNMANIFESTED_INHERITED_INPUT.json')
    candidate = case.candidate('subject.py', 'def value():\n    return 1\n')
    passed = worker.verify(case.contract, candidate, output/'fixed', authority=case.authority,
                           admission_certificate=certificate, policy=case.policy)
    checked = worker.validate_receipt(case.contract, candidate, case.authority, certificate, passed,
                                      policy=case.policy, output_dir=output/'independent')
    assert failed['status'] == 'FAIL_NATIVE' and checked['status'] == 'PASS_NATIVE'
    support.record_evidence(output/'fixed', output/'failed/collection/admission-certificate.json',
                            output/'fixed/receipt.json', output/'independent/receipt.json')
    frozen = {'files': {current.PREFIX+'native_execution_v45.py': support.sha(Path(worker.__file__).read_bytes())},
              'profile_identities': {'modern': {'environment': modern_environment}}}
    audit = current.audit_native_packets(tmp_path, frozen)
    assert audit['native_passes'] == 2 and audit['native_failures'] == 1
    assert audit['independent_replays'] == 1
    assert len({row['invocation_path'] for row in audit['receipts']}) == len(audit['receipts'])


def test_adversarial_unknown_packet_cannot_be_mislabeled_as_genuine(project_factory, modern_environment, tmp_path):
    current = qualifier()
    from . import native_v45_test_support as support
    worker = support.implementation()
    case = support.ordinary_case(project_factory,
        b'import pytest\n@pytest.mark.skip(reason="qualification negative")\ndef test_contract():\n    assert False\n')
    output = tmp_path/'inherited-v45-evidence'
    certificate, receipt = support.collect_and_run(case, output)
    assert receipt['status'].startswith('UNKNOWN')
    support.record_evidence(output, output/'collection/admission-certificate.json', output/'native/receipt.json')
    manifest = output/'V45_NATIVE_EVIDENCE.json'
    frozen = {'files': {current.PREFIX+'native_execution_v45.py': support.sha(Path(worker.__file__).read_bytes())},
              'profile_identities': {'modern': {'environment': modern_environment}}}
    try:
        with pytest.raises(ValueError, match='mislabeled'):
            current.audit_native_packets(tmp_path, frozen)
    finally:
        # Preserve the manufactured parser input under an explicit synthetic
        # name. The actual refused native receipt and packets stay untouched.
        manifest.rename(output/'SYNTHETIC_MISLABEL_PARSER_INPUT.json')
