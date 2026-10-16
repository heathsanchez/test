"""Local record assembly only: no metadata queries, source fetches or native calls.

Run from the prospective repository with PYTHONPATH pointing to that repository.
The independent audit is an input, never manufactured by this helper.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import shutil

from research.unified_consequence_runtime import qualify_native_frontier_v3 as q


def descriptor(path, *, relative=False):
    path = Path(path).resolve()
    return {'path': path.relative_to(q.HERE.parents[1]).as_posix() if relative else str(path),
            'sha256': q.digest(path.read_bytes())}


def copy_exact(source, target):
    source, target = Path(source).resolve(), Path(target).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_bytes() != source.read_bytes():
        raise ValueError('refusing to replace existing different evidence: '+str(target))
    if source != target and not target.exists():
        shutil.copyfile(source, target)
    return descriptor(target, relative=True)


def prepare(args):
    wrapper = json.loads(Path(args.environment_gate).read_text())
    q.require_environment_gate(wrapper)
    curated = Path(args.curation).resolve()
    execution = copy_exact(curated/'PREQUERY_EXECUTION.json', q.RECORDS/'PREQUERY_EXECUTION.json')
    pool = copy_exact(curated/'FROZEN_POOL.json', q.RECORDS/'FROZEN_POOL.json')
    copy_exact(curated/'METADATA_CURATION.json', q.RECORDS/'METADATA_CURATION.json')
    if json.loads((q.RECORDS/'PREQUERY_EXECUTION.json').read_text())['environment_gate'] != wrapper['environment_gate']:
        raise ValueError('curation gate differs from current independently qualified gate')
    value = copy.deepcopy(q.DEFAULTS)
    value.update(environment_gate=wrapper['environment_gate'], catalog=wrapper['catalog'],
                 prequery=execution, pool=pool)
    if q.PROTOCOL.exists() and json.loads(q.PROTOCOL.read_text()) != value:
        raise ValueError('existing prospective protocol differs; preserve it and use a new version')
    q._write_record(q.PROTOCOL, value)
    ticket = {'schema': 'UDM_NATIVE_CLI_AUTHORITY_V3', 'operation': 'screen',
              'repo': str(q.HERE.parents[1]), 'environment_gate': wrapper['environment_gate'],
              'prequery': execution, 'pool': pool, 'output_root': str(Path(args.screen_root).resolve())}
    path = q.RECORDS/'SCREENING_AUTHORITY.json'
    if path.exists() and json.loads(path.read_text()) != ticket:
        raise ValueError('new versioned screening authority required; existing ticket differs')
    authority = q._write_record(path, ticket)
    print(q.canonical({'state': 'MUST_COMMIT_ALL_RECORDS_BEFORE_SOURCE_SCREENING', 'authority': authority,
                       'protocol': descriptor(q.PROTOCOL, relative=True)}))


def requests(args):
    authority = descriptor(args.authority)
    ticket, bound, _ = q.cli_authority(authority['path'], authority['sha256'], 'screen')
    pool = q._committed_record(ticket['repo'], ticket['pool'])
    destination = Path(args.requests).resolve(); destination.mkdir(parents=True, exist_ok=True)
    for index, spec in enumerate(pool['pool']):
        request = {'pool_index': index, 'spec': spec, 'protocol_binding': bound['sha256']}
        # Authenticate the genuine committed source, plan/code, pool and gate now.
        q.screening_request(request, ticket, bound)
        q._write_record(destination/('request-'+format(index, '03d')+'.json'), request)
    print(q.canonical({'authority': authority, 'request_count': len(pool['pool']),
                       'requests': str(destination), 'screen_root': ticket['output_root']}))


def finalize(args):
    value = q.protocol(); q.require_environment_gate(value)
    authority = descriptor(args.authority)
    ticket, _, _ = q.cli_authority(authority['path'], authority['sha256'], 'screen')
    pool = q._committed_record(ticket['repo'], ticket['pool'])
    root = Path(ticket['output_root']); meter_path = root/'SCREENING_METER.json'
    meter = json.loads(meter_path.read_text())
    if (meter['pending'] is not None or meter['accounting_complete'] is not True
            or len(meter['cases']) != len(pool['pool'])):
        raise ValueError('entire fixed ordered pool must finish with complete cost accounting')
    reports = [json.loads((root/('case-'+format(i, '03d'))/'SCREENING_ENVELOPE.json').read_text())
               for i in range(len(pool['pool']))]
    roles = q.select_screened_roles(pool['pool'], reports, requested=2)
    audit_path = Path(args.independent_audit).resolve()
    audit = json.loads(audit_path.read_text())
    expected = {'status': 'PASS_ADMISSION_ONLY_SCREENING_AUDIT',
        'pool_sha256': value['pool']['sha256'], 'reports_sha256': q.worker.fingerprint(reports),
        'eligibility_rule': 'PASS_NATIVE_OR_FAIL_NATIVE_IDENTICAL',
        'all_screened_cases_and_costs_retained': True, 'independent_screener': True,
        'search_or_policy_outcomes_accessed': False, 'learner_future_source_accessed': False}
    if any(audit.get(key) != expected_value for key, expected_value in expected.items()):
        raise ValueError('actual independent audit must bind all exact reports and exposure attestations')
    audit_record = copy_exact(audit_path, q.RECORDS/'SCREENING_AUDIT.json')
    # Only sealed public envelopes are copied; raw future packets remain at root.
    meter_record = copy_exact(meter_path, q.RECORDS/'SCREENING_METER.json')
    screening = {'schema': 'UDM_ADMISSION_ONLY_SCREENING_V3',
        'pool_sha256': value['pool']['sha256'], 'prequery_sha256': value['prequery']['sha256'],
        'environment_gate': value['environment_gate'], 'independent_screener': True,
        'search_or_policy_outcomes_accessed': False, 'learner_future_source_accessed': False,
        'reports': reports, 'independent_audit': audit_record,
        'screening_authority': authority,
        'screening_meter': descriptor(q.HERE.parents[1]/meter_record['path']),
        'costs': {'native_calls': meter['native_calls'], 'collection_calls': meter['collection_calls'],
            'sum_case_wall_seconds': sum(row['total_wall_seconds'] for row in reports),
            'ordered_screening_interval_wall_seconds': max(0, meter_path.stat().st_mtime-meter['started_at_unix']),
            'all_pool_members_retained': len(reports), 'accounting_complete': True,
            'cost_scope': 'Entire independent admission pool; retained separately from each matched acquisition arm.'}}
    metadata = {'schema': 'UDM_PROSPECTIVE_NATIVE_FRONTIER_TASK_METADATA_V3',
                'selected': roles, 'pool_sha256': value['pool']['sha256'],
                'selection_rule': 'FIRST_TWO_SOURCE_DISTINCT_AUTHENTIC_NATIVE_ADMISSIONS_IN_FIXED_POOL_ORDER'}
    for path, record in ((q.METADATA, metadata), (q.RECORDS/'SCREENING.json', screening)):
        if path.exists() and json.loads(path.read_text()) != record:
            raise ValueError('existing frontier evidence differs; preserve it and use a new version')
        q._write_record(path, record)
    value.update(state='READY_TO_FREEZE_NO_LEARNER_SOURCE_ACCESS',
                 screening=descriptor(q.RECORDS/'SCREENING.json', relative=True),
                 metadata_sha256=q.digest(q.METADATA.read_bytes()))
    q._write_record(q.PROTOCOL, value)
    q.require_screening_manifest(value)
    print(q.canonical({'state': 'MUST_COMMIT_CLEAN_SOURCE_BEFORE_FREEZE',
                       'protocol': descriptor(q.PROTOCOL, relative=True),
                       'metadata': descriptor(q.METADATA, relative=True), 'selected_roles': len(roles)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True)
    prepare_parser = modes.add_parser('prepare-screening')
    prepare_parser.add_argument('--environment-gate', required=True)
    prepare_parser.add_argument('--curation', required=True)
    prepare_parser.add_argument('--screen-root', required=True)
    prepare_parser.set_defaults(function=prepare)
    request_parser = modes.add_parser('write-requests')
    request_parser.add_argument('--authority', required=True)
    request_parser.add_argument('--requests', required=True)
    request_parser.set_defaults(function=requests)
    final_parser = modes.add_parser('finalize-records')
    final_parser.add_argument('--authority', required=True)
    final_parser.add_argument('--independent-audit', required=True)
    final_parser.set_defaults(function=finalize)
    args = parser.parse_args(); args.function(args)


if __name__ == '__main__':
    main()
