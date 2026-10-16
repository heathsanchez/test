"""Admission-only qualification on three explicitly exposed development tasks."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import time

from .decisive_native_verify import _path, canonical, fingerprint, sha256
from .developmental_machine import Machine
from .qualify_decisive_native import copy_state
from . import native_environment_v2 as environment
from . import native_execution_v2 as execution

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RECORDS = HERE / 'archaeology/native-admission-v2'
PROTOCOL = RECORDS / 'PROTOCOL.json'


def inputs():
    protocol = json.loads(PROTOCOL.read_text())
    values = []
    for key in ('execution_policy', 'dependencies'):
        row = protocol[key]; path = ROOT / _path(row['path'])
        if sha256(path.read_bytes()) != row['sha256']:
            raise ValueError('frozen qualification input changed: ' + key)
        values.append(json.loads(path.read_text()))
    for row in protocol['origin'].values():
        if sha256((ROOT / _path(row['path'])).read_bytes()) != row['sha256']:
            raise ValueError('prior diagnostic authority changed')
    original = json.loads((ROOT / protocol['origin']['metadata']['path']).read_text())['selected']
    expected = [{**row, 'original_role': row['role'], 'role': 'EXPOSED_DEVELOPMENT_DIAGNOSTIC_' + str(i)}
                for i, row in enumerate(original)]
    if (protocol['diagnostics'] != expected or len(expected) != 3
            or [row['repo'] for row in expected] != [
                'more-itertools/more-itertools', 'python-attrs/attrs', 'python-attrs/cattrs']):
        raise ValueError('only three exact previously exposed diagnostics are licensed')
    environment._validate_inputs(values[0], values[1])
    if len(values[1]) != protocol['dependencies']['count']:
        raise ValueError('complete fixed dependency closure changed')
    return protocol, *values


def write_freeze(repo, out):
    repo = Path(repo).resolve(); protocol, _, _ = inputs()
    if subprocess.check_output(['git', '-C', str(repo), 'status', '--porcelain']).strip():
        raise ValueError('commit qualification source and protocol before diagnostic execution')
    head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    files = {}
    for name in protocol['freeze_files']:
        raw = subprocess.check_output(['git', '--no-replace-objects', '-C', str(repo), 'show', head + ':' + name])
        if raw != (repo / name).read_bytes():
            raise ValueError('working source differs from frozen Git source')
        files[name] = sha256(raw)
    result = {'schema': 'UDM_NATIVE_ADMISSION_FREEZE_V2', 'source_commit': head,
              'protocol_sha256': sha256(PROTOCOL.read_bytes()), 'files': files,
              'exposure': protocol['exposure'], 'mode': protocol['mode']}
    path = Path(out); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical(result) + '\n'); return result


def check_freeze(repo, path):
    repo = Path(repo).resolve(); frozen = json.loads(Path(path).read_text())
    protocol, _, _ = inputs()
    head = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    if (frozen.get('schema') != 'UDM_NATIVE_ADMISSION_FREEZE_V2' or frozen.get('source_commit') != head
            or frozen.get('protocol_sha256') != sha256(PROTOCOL.read_bytes())
            or set(frozen.get('files', {})) != set(protocol['freeze_files'])
            or any(sha256((repo / _path(name)).read_bytes()) != value for name, value in frozen['files'].items())):
        raise ValueError('qualification source or protocol differs from frozen authority')
    return frozen


def state_snapshot(state):
    state = Path(state); raw = (state / 'metatron-ledger.jsonl').read_bytes(); objects = {}
    for path in sorted((state / 'objects').iterdir()):
        if path.is_symlink() or not path.is_file() or sha256(path.read_bytes()) != path.name:
            raise ValueError('qualified CAS address differs')
        objects[path.name] = sha256(path.read_bytes())
    return {'records': len(raw.splitlines()), 'ledger_sha256': sha256(raw), 'objects': objects}


def preserve_authority(out, components, protocol):
    copy_state(out); before = state_snapshot(out / 'state')
    pins = protocol['preserved_authority']; inventory = HERE / 'capability_index.json'
    prior_inventory = inventory.read_bytes()
    source_pins = all(sha256((ROOT / name).read_bytes()) == value for name, value in pins['files'].items())
    machine = Machine(Path(components), out / 'state', Path(components) / 'evaluator', out / 'unused-native-config.json')
    after = state_snapshot(out / 'state')
    result = {'records': len(machine.log), 'CAS_objects': len(after['objects']),
        'inventory_rows': len(json.loads(inventory.read_text())['capabilities']),
        'ledger_sha256': after['ledger_sha256'], 'ledger_exact': before['ledger_sha256'] == after['ledger_sha256'] == pins['ledger_sha256'],
        'CAS_exact': before['objects'] == after['objects'], 'inventory_exact': inventory.read_bytes() == prior_inventory,
        'source_pins_exact': source_pins, 'original_FLASH_agrees': set(machine.mt.live_ids(machine.log)) == machine.flash_live_ids(),
        'machine_costs': machine.costs, 'historical_acquisition_rerun': False}
    if (any(result[key] != pins[key] for key in ('records', 'CAS_objects', 'inventory_rows'))
            or not all(result[key] for key in ('ledger_exact', 'CAS_exact', 'inventory_exact', 'source_pins_exact', 'original_FLASH_agrees'))):
        raise ValueError('prior qualified source, ledger, CAS or inventory authority changed')
    return result


def first_task_gate(authority, certificate, receipt):
    """Additional controller gate after independent native receipt validation."""
    try:
        nodes = certificate['collection']['collected_test_nodes']; data = receipt['execution']; count = receipt['junit']
        calls = [row for row in data['reports'] if row['when'] == 'call']
        protected = [row['nodeid'] for row in calls if row['outcome'] == 'failed' and any(
            row['nodeid'] == prefix or row['nodeid'].startswith(prefix + '[')
            or row['nodeid'].startswith(prefix + '::') for prefix in authority['required_test_nodes'])]
        good = (receipt['status'] == 'FAIL_NATIVE' and nodes and len(set(nodes)) == len(nodes)
            and data['collected_test_nodes'] == data['selected_test_nodes'] == nodes and not data['deselected_test_nodes']
            and [row['nodeid'] for row in calls] == nodes and protected
            and not any(row.get('wasxfail') or row['outcome'] == 'skipped' for row in data['reports'])
            and count['tests'] == count['passed'] + count['failures'] == len(nodes) and count['failures'] > 0
            and not count['errors'] and not count['skipped']
            and receipt['independent_reexecution']['costs']['native_calls'] == 1)
    except (KeyError, TypeError):
        good = False; protected = []
    return {'status': 'PASS' if good else 'FAIL', 'protected_failed_nodes': protected,
            'requirement': 'Complete independent original suite with protected actual call failure, no skips/xfails/deselection'}


def qualify(args):
    protocol, policy, packages = inputs(); frozen = check_freeze(args.repo, args.freeze)
    out = Path(args.out).resolve(); out.mkdir(parents=True, exist_ok=False); started = time.monotonic()
    binding = sha256(Path(args.freeze).read_bytes())
    result = {'schema': 'UDM_NATIVE_ADMISSION_RESULT_V2', 'status': 'QUALIFICATION_FAILED',
        'source_commit': frozen['source_commit'], 'mode': protocol['mode'], 'exposure': protocol['exposure'],
        'freeze': frozen, 'protocol_binding': binding, 'verdicts': protocol['verdicts'], 'tasks': [],
        'first_task_gate': {'status': 'FAIL', 'reason': 'No independently executed protected native failure'},
        'cost_boundary': protocol['costs'], 'acquisitions': 0, 'candidates': 0}
    def save():
        result['total_wall_seconds'] = time.monotonic() - started
        (out / 'RESULT.json').write_text(canonical(result) + '\n')
    for path in (PROTOCOL, RECORDS / 'EXECUTION_POLICY.json', RECORDS / 'PINNED_DEPENDENCIES.json'):
        (out / path.name).write_bytes(path.read_bytes())
    (out / 'FREEZE.json').write_bytes(Path(args.freeze).read_bytes())
    try:
        result['retention'] = preserve_authority(out, args.components, protocol); save()
        for index, spec in enumerate(protocol['diagnostics']):
            item = {'repository': spec['repo'], 'role': spec['role'], 'status': 'UNKNOWN_SETUP'}
            result['tasks'].append(item); task_started = time.monotonic()
            try:
                setup = environment.provision(spec, out / ('task-' + str(index)), binding, policy=policy, packages=packages)
                item['setup'] = setup
                if setup['status'] == 'PREPARED':
                    contract = setup['contract']; authority = setup['authority']; folder = out / ('task-' + str(index))
                    certificate = execution.collect(contract, authority, folder / 'collection', policy=policy)
                    item['collection'] = {'nodes': len(certificate['collection']['collected_test_nodes']), 'costs': certificate['costs'],
                                          'certificate_sha256': fingerprint(certificate)}
                    receipt = execution.verify(contract, {'replacements': []}, folder / 'native', authority=authority,
                                               admission_certificate=certificate, policy=policy)
                    item['receipt'] = {key: receipt[key] for key in ('status', 'junit', 'costs')}; item['status'] = receipt['status']
                    if index == 0:
                        checked = execution.validate_receipt(contract, {'replacements': []}, authority, certificate, receipt,
                                                             policy=policy, output_dir=folder / 'receipt-recheck')
                        (folder / 'independently-validated-receipt.json').write_text(canonical(checked) + '\n')
                        item['independent_reexecution'] = checked['independent_reexecution']
                        result['first_task_gate'] = first_task_gate(authority, certificate, checked)
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
                item.update(status='UNKNOWN_DIAGNOSTIC', error=str(error))
            item['total_wall_seconds'] = time.monotonic() - task_started; save()
        if result['first_task_gate']['status'] == 'PASS':
            result['status'] = 'ADMISSION_ONLY_QUALIFIED'
        return result
    finally:
        save()


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--repo', required=True); parser.add_argument('--out', required=True)
    parser.add_argument('--components'); parser.add_argument('--source-repos'); parser.add_argument('--freeze')
    parser.add_argument('--write-freeze', action='store_true'); args = parser.parse_args()
    if args.write_freeze:
        result = write_freeze(args.repo, args.out)
    else:
        if not args.components or not args.freeze:
            parser.error('--components and --freeze are required for qualification')
        result = qualify(args)
    print(canonical({'status': result.get('status', 'FROZEN'), 'verdicts': result.get('verdicts', {})}))
    if not args.write_freeze and result['status'] != 'ADMISSION_ONLY_QUALIFIED':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
