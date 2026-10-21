#!/usr/bin/env python3
"""Expose only current-binding training CAS evidence to a published agent arm.

This observer never executes target code or opens RESULT.json, future directories,
source repositories, repaired heads, or author patches. It is a transport helper,
not an independent native verifier or a reference monitor. Run from trusted parent
custody with independently recorded authority and metadata SHA256 values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import time

HEX = re.compile(r'[0-9a-f]{64}')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _pass(receipt):
    # Exact v2 success rule: decisive_native.passed with the v2 exit-code adapter.
    counts = receipt.get('junit', {})
    return (receipt.get('status') == 'PASS_NATIVE'
            and receipt.get('execution', {}).get('process_exit_code') == 0
            and counts.get('tests', 0) > 0
            and counts.get('passed', 0) == counts['tests']
            and all(counts.get(key) == 0 for key in ('failures', 'errors', 'skipped')))


def project(arm_path, authority_path, authority_sha256, metadata_path, metadata_sha256):
    started = time.monotonic()
    accesses = []

    def read(path, expected=None, label='input'):
        path = Path(path)
        if not path.is_absolute() or path.is_symlink() or path.resolve() != path or not path.is_file():
            raise ValueError('canonical original ' + label + ' file required')
        raw = path.read_bytes()
        actual = digest(raw)
        if expected is not None and (not isinstance(expected, str)
                or HEX.fullmatch(expected) is None or actual != expected):
            raise ValueError(label + ' bytes differ from independently supplied pin')
        accesses.append({'path': str(path), 'sha256': actual, 'bytes': len(raw), 'kind': label})
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError(label + ' must be a JSON object')
        return value

    arm_path = Path(arm_path)
    authority_path = Path(authority_path)
    metadata_path = Path(metadata_path)
    if arm_path.name != 'AGENT_ARM.json' or authority_path != arm_path.with_name('AGENT_AUTHORITY.json'):
        raise ValueError('published canonical agent arm and sibling authority required')
    authority = read(authority_path, authority_sha256, 'external authority')
    if (authority.get('schema') != 'UDM_NATIVE_CLI_AUTHORITY_V3'
            or authority.get('operation') != 'agent'):
        raise ValueError('wrong external authority type')
    descriptor = authority['parent']
    if (set(descriptor) != {'path', 'sha256'}
            or descriptor['path'] != str(arm_path.with_name('AGENT_PARENT_RECEIPT.json'))):
        raise ValueError('wrong immutable parent receipt path')
    parent = read(Path(descriptor['path']), descriptor['sha256'], 'immutable parent receipt')
    if (parent.get('schema') != 'UDM_NATIVE_AGENT_PARENT_RECEIPT_V3'
            or parent.get('freeze') != authority.get('freeze')
            or set(parent.get('arm', {})) != {'path', 'sha256'}
            or parent['arm']['path'] != str(arm_path)):
        raise ValueError('wrong published agent parent lineage')
    arm = read(arm_path, parent['arm']['sha256'], 'published arm')
    binding = arm.get('protocol_binding')
    if (arm.get('schema') != 'UDM_CODING_AGENT_NATIVE_ARM_V3'
            or not isinstance(binding, str) or HEX.fullmatch(binding) is None
            or parent['freeze'].get('sha256') != binding
            or arm.get('released_at_unix') != parent.get('released_at_unix')):
        raise ValueError('published arm has wrong protocol or release lineage')
    metadata = read(metadata_path, metadata_sha256, 'frozen role metadata')
    roles = metadata.get('selected')
    if (not isinstance(roles, list) or not roles or not isinstance(roles[0], dict)
            or roles[0].get('role', 'TRAINING') != 'TRAINING'
            or not isinstance(roles[0].get('repo'), str) or not roles[0]['repo']):
        raise ValueError('first frozen source must be the training role')
    training = roles[0]['repo']
    state = arm_path.parent / 'state'
    objects = state / 'objects'
    if objects.is_symlink() or objects.resolve() != objects:
        raise ValueError('canonical original content-addressed state required')

    def get(key):
        if not isinstance(key, str) or HEX.fullmatch(key) is None:
            raise ValueError('invalid content-addressed object reference')
        return read(objects / key, key, 'content-addressed training object')

    ledger_path = state / 'metatron-ledger.jsonl'
    if ledger_path.is_symlink() or ledger_path.resolve() != ledger_path:
        raise ValueError('canonical original immutable ledger required')
    ledger_raw = ledger_path.read_bytes()
    accesses.append({'path': str(ledger_path), 'sha256': digest(ledger_raw),
                     'bytes': len(ledger_raw), 'kind': 'immutable ledger snapshot'})
    ledger = []
    for line in ledger_raw.splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict) or set(row) != {'id', 'kind', 'payload', 'premises'}:
            raise ValueError('unexpected immutable ledger record')
        body = {key: row[key] for key in ('kind', 'payload', 'premises')}
        encoded = json.dumps(body, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
                             allow_nan=False).encode()
        if digest(encoded) != row['id']:
            raise ValueError('immutable ledger record hash differs')
        ledger.append(row)

    profiles, episodes, native_records, contexts, statuses, evidence = {}, {}, {}, {}, {}, []
    common_scope = None
    baseline = None
    for node in ledger:
        if node['kind'] != 'native_frontier_v2_profile':
            continue
        report_key = node['payload']['report']
        report = get(report_key)
        scope = report.get('scope', {})
        # Never dereference attempts/context for another run or any protected future.
        if scope.get('protocol_binding') != binding or report.get('future') != training:
            continue
        name = report.get('candidate')
        if not isinstance(name, str) or not name:
            raise ValueError('invalid training policy identity')
        if name in profiles:
            raise ValueError('duplicate current training policy profile')
        if common_scope is None:
            common_scope = scope
        elif scope != common_scope:
            raise ValueError('mixed current training profile scope')
        if scope.get('budget') != 8 or set(scope.get('contexts', {})) != {training}:
            raise ValueError('training scope is not the frozen eight-proposal carrier')
        context_key = scope['contexts'][training]
        if training not in contexts:
            context = get(context_key)
            if (context.get('contract', {}).get('repository') != training
                    or context['contract'].get('protocol_binding') != binding):
                raise ValueError('training context has wrong source or binding')
            contexts[training] = {'sha256': context_key, 'value': context}
            baseline_record = get(context['baseline_record'])
            if (baseline_record.get('contract') != context['contract']
                    or baseline_record.get('candidate') != {'replacements': []}):
                raise ValueError('training baseline does not preserve original unrepaired contract')
            baseline = baseline_record
        context = contexts[training]['value']
        order = context['orders'].get(name)
        attempts = report.get('attempts')
        if (not isinstance(order, list) or report.get('order') != order
                or not isinstance(attempts, list) or len(attempts) > 8
                or report.get('episode', {}).get('attempts') != attempts):
            raise ValueError('training order or episode differs from original retained context')
        required = {context_key, context['baseline_record'], *attempts}
        if not required <= set(scope.get('receipt_objects', [])):
            raise ValueError('training evidence is absent from original retained scope')
        receipts, producer_events = [], []
        for index, key in enumerate(attempts):
            record = get(key)
            if (record.get('schema') != 'UDM_NATIVE_PROFILE_RECORD_V2'
                    or record.get('contract') != context['contract']
                    or index >= len(order) or digest(canonical(record.get('candidate')).encode()) != order[index]
                    or record.get('producer', {}).get('source') != context['runtime_source']
                    or record['producer'].get('authority') != context['runtime_authority']
                    or any(_pass(receipt) for receipt in receipts)):
                raise ValueError('training candidate/order/source producer lineage differs')
            producer = record['producer']
            premises = [producer['source'], producer['authority'], *producer.get('dependencies', [])]
            matching = [event['id'] for event in ledger
                        if event['kind'] == 'native_frontier_v2_probe'
                        and event['payload'].get('record') == key and event['premises'] == premises]
            if len(matching) != 1:
                raise ValueError('ambiguous or missing retained training probe event')
            producer_events.append(matching[0])
            receipt = record['receipt']
            calls = receipt.get('costs', {}).get('native_calls')
            if type(calls) is not int or calls < 0:
                raise ValueError('native_calls must be a retained nonnegative integer')
            native_records[key] = record
            receipts.append(receipt)
        if node['premises'] != producer_events:
            raise ValueError('training profile premises differ from exact original executed trace')
        profiles[name] = {training: [0 if any(_pass(receipt) for receipt in receipts) else 1,
                                    sum(receipt['costs']['native_calls'] for receipt in receipts)]}
        episodes[name] = report['episode']
        statuses[name] = [receipt.get('status') for receipt in receipts]
        evidence.append({'event': node, 'report_sha256': report_key, 'report': report})
    if profiles:
        if set(profiles) != set(contexts[training]['value']['orders']):
            raise ValueError('incomplete retained training profile carrier')
        status = 'CURRENT_TRAINING_PROFILE_CARRIER_PROJECTED'
    else:
        if arm.get('contract', {}).get('repository') != training:
            raise ValueError('future arm has no retained current training profiles')
        baseline = arm['native_residual']
        status = 'TRAINING_BASELINE_ONLY_NO_PROFILE_CARRIER'
    return {'schema': 'UDM_AGENT_TRAINING_SHARED_HISTORY_V3', 'status': status,
            'protocol_binding': binding, 'training_repository': training,
            'profiles': profiles, 'episodes': episodes, 'profile_statuses': statuses,
            'scope': common_scope, 'contexts': contexts, 'native_records': native_records,
            'baseline': baseline, 'profile_evidence': evidence,
            'arm_descriptor': parent['arm'], 'authority_sha256': authority_sha256,
            'metadata_sha256': metadata_sha256, 'input_accesses': accesses,
            'projection_wall_seconds': time.monotonic() - started,
            'native_execution_performed': False,
            'scientific_verification': 'NOT_PERFORMED_BY_PROJECTION',
            'information_boundary': 'CURRENT_BINDING_TRAINING_RECEIPTS_ONLY; NO_RESULT_OR_FUTURE_SOURCE_OR_OUTCOMES',
            'helper_sha256': digest(Path(__file__).read_bytes())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arm', required=True)
    parser.add_argument('--authority', required=True)
    parser.add_argument('--authority-sha256', required=True)
    parser.add_argument('--metadata', required=True)
    parser.add_argument('--metadata-sha256', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    output = Path(args.out)
    if output.exists():
        raise ValueError('new immutable training history output required')
    result = project(args.arm, args.authority, args.authority_sha256,
                     args.metadata, args.metadata_sha256)
    with output.open('x') as stream:
        stream.write(canonical(result) + '\n')
    print(canonical({'status': result['status'], 'path': str(output.resolve()),
                     'sha256': digest(output.read_bytes()),
                     'training_policies': len(result['profiles']),
                     'projection_wall_seconds': result['projection_wall_seconds']}))


if __name__ == '__main__':
    main()
