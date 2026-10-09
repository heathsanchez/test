#!/usr/bin/env python3
"""External Hard-set harness: opaque agent inputs, explicit diagnostic accounting.

Evaluation metadata never enters the agent command. This is a four-environment,
shared-state diagnostic, not a six-site isolated benchmark leaderboard score.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import os
import signal
import subprocess
import sys
import uuid
from pathlib import Path

UPSTREAM = '6473f72db5dcefc97b5725b59e734504edc28a21'
SITES = ('shopping_admin', 'shopping', 'reddit', 'gitlab')
CONFIG = {'environments': {
 '__SHOPPING_ADMIN__': {'urls':['http://localhost:7780/admin'], 'active_url_idx':0},
 '__SHOPPING__': {'urls':['http://localhost:7770'], 'active_url_idx':0},
 '__REDDIT__': {'urls':['http://localhost:9999'], 'active_url_idx':0},
 '__GITLAB__': {'urls':['http://localhost:8023'], 'active_url_idx':0,
                'credentials':{'username':'byteblaze','password':'hello1234'}},
 '__MAP__': {'urls':['http://localhost:3030'], 'active_url_idx':0},
 '__WIKIPEDIA__': {'urls':['http://localhost:8888'], 'active_url_idx':0},
}}


def partition(sites):
    return sites[0] if len(sites) == 1 and sites[0] in SITES else 'crosssite'


def failure_class(stderr):
    if 'unsupported initial site:' in stderr:
        return 'unsupported_site'
    if any(marker in stderr for marker in ('unsupported shopping instruction:',
           'unsupported shopping_admin instruction:', 'unsupported GitLab intent:',
           'no blind route for intent:', 'unsupported report intent:')):
        return 'unsupported_route'
    return 'execution_error'


def invoke_agent(command, out, timeout):
    # Timeout cleanup is restricted to this invocation's own process group.
    with (out/'stdout.txt').open('w') as stdout, (out/'stderr.txt').open('w') as stderr:
        process = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True)
        try:
            return process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            return 124


def run_lane(dataset: Path, lane: str, output: Path, timeout=600):
    from webarena_verified.api import WebArenaVerified
    from webarena_verified.types.config import WebArenaVerifiedConfig
    from webarena_verified.types.tracing import NetworkTrace
    tasks = json.loads(dataset.read_text())
    if len(tasks) != 258 or len({int(t['task_id']) for t in tasks}) != 258:
        raise ValueError('expected exactly 258 unique Hard tasks')
    selected = [task for task in tasks if partition(task.get('sites') or []) == lane]
    output.mkdir(parents=True, exist_ok=True)
    config_file = output/'config.json'
    config_file.write_text(json.dumps(CONFIG, indent=2)+'\n')
    authority = WebArenaVerified(config=WebArenaVerifiedConfig.from_file(config_file))
    empty = NetworkTrace.model_construct(is_playwright=False, src_file=Path('<no-network-evaluator>'), events=())
    rows = {}
    errors = 0
    for task in selected:
        ident = int(task['task_id'])
        slot = uuid.uuid4().hex
        dest = output/'output'/slot
        dest.mkdir(parents=True)
        start = (task.get('start_urls') or [''])[0]
        command = [sys.executable, 'scripts/webarena_blind_retrieval_bridge.py',
                   '--intent', task['intent'], '--start-url', start, '--output-dir', str(dest)]
        code = invoke_agent(command, dest, timeout)
        row = {'task_id':ident, 'opaque_slot':slot, 'exit_code':code, 'score':0.0,
               'sites':task.get('sites',[]), 'agent_completed':False}
        if code == 124:
            row['status'] = 'execution_timeout'
        elif code:
            row['status'] = failure_class((dest/'stderr.txt').read_text(errors='replace'))
        elif not (dest/'agent_response.json').is_file():
            row['status'] = 'missing_response'
        else:
            row['agent_completed'] = True
            try:
                # Read evaluator requirements from its typed authority, not a raw dict.
                official = authority.get_task(ident)
                protected = any(e.evaluator == 'NetworkEventEvaluator' for e in official.eval)
                trace_path = dest/'network.har'
                if protected and not trace_path.is_file():
                    row['status'] = 'missing_network_evidence'
                else:
                    trace = NetworkTrace.from_har(trace_path) if protected else empty
                    result = authority.evaluate_task(task_id=ident, agent_response=dest/'agent_response.json', network_trace=trace)
                    (dest/'official.json').write_text(json.dumps(result.model_dump(mode='json',exclude_none=True),indent=2)+'\n')
                    row['official_status'] = result.status.value
                    row['official_score'] = float(result.score)
                    good = row['official_score'] == 1.0 and row['official_status'] == 'success'
                    row.update(score=1.0 if good else 0.0, status='official_success' if good else 'official_failure')
            except Exception as exc:
                errors += 1
                row.update(status='scorer_error', error=repr(exc))
        rows[str(ident)] = row
        print('RESULT', ident, row['status'], row['score'], flush=True)
        (output/'progress.json').write_text(json.dumps(rows,indent=2)+'\n')
    report = {'epistemic_state':'REJECTED_SCORER_ERROR' if errors else 'WARRANTED_BOUNDED_DIAGNOSTIC',
              'boundary':'one agent; shared state within lane; Map and Wikipedia not provisioned',
              'upstream_commit':UPSTREAM, 'source_commit':os.environ.get('GITHUB_SHA','local'),
              'dataset_sha256':hashlib.sha256(dataset.read_bytes()).hexdigest(),
              'lane':lane, 'presented':len(rows), 'total':len(selected),
              'official_success_count':sum(row['score']==1 for row in rows.values()),
              'scorer_errors':errors, 'results':rows}
    (output/'lane.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2),flush=True)
    if errors or len(rows) != len(selected):
        raise RuntimeError('diagnostic accounting or scorer failure; no score promotion')
    return report


def aggregate(root: Path, dataset: Path, output: Path):
    tasks = json.loads(dataset.read_text())
    wanted = {str(int(t['task_id'])) for t in tasks}
    rows = {}
    commits = set()
    hashes = set()
    lanes = set()
    errors = 0
    for path in sorted(root.rglob('lane.json')):
        report = json.loads(path.read_text())
        if report['lane'] in lanes or rows.keys() & report['results'].keys():
            raise RuntimeError('duplicate lane or task in aggregate')
        lanes.add(report['lane'])
        commits.add(report['source_commit'])
        hashes.add(report['dataset_sha256'])
        errors += report['scorer_errors']
        rows.update(report['results'])
    if lanes != set(SITES)|{'crosssite'} or set(rows) != wanted or len(commits) != 1:
        raise RuntimeError('incomplete or mixed-source aggregate')
    if hashes != {hashlib.sha256(dataset.read_bytes()).hexdigest()} or errors:
        raise RuntimeError('dataset identity or scoring failure')
    wins = sum(row['score']==1 for row in rows.values())
    classes = collections.Counter(row['status'] for row in rows.values())
    report = {'epistemic_state':'WARRANTED_BOUNDED_DIAGNOSTIC',
              'boundary':'258 tasks; same agent commit; four fixture sites; shared state per lane; not six-site isolated leaderboard',
              'source_commit':next(iter(commits)), 'upstream_commit':UPSTREAM,
              'presented':len(rows), 'official_success_count':wins, 'score_fraction':wins/len(rows),
              'status_counts':dict(classes), 'scorer_errors':errors, 'results':rows}
    output.mkdir(parents=True,exist_ok=True)
    (output/'qualification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='results'},indent=2),flush=True)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--lane',choices=SITES+('crosssite',))
    parser.add_argument('--aggregate',type=Path)
    args = parser.parse_args()
    if args.aggregate:
        aggregate(args.aggregate,args.dataset,args.output)
    elif args.lane:
        run_lane(args.dataset,args.lane,args.output)
    else:
        parser.error('supply --lane or --aggregate')


if __name__ == '__main__':main()
