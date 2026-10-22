"""Parent launcher: wait for a real published arm, then invoke Codex.

This transport performs no target selection or queries. A published ticket is
not an executed-agent result; actual model and native telemetry are required.
"""
import argparse
import hashlib
import json
from pathlib import Path
import os
import shlex
import subprocess
import time


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bound(record):
    path = Path(record['path'])
    if path.is_symlink() or path.resolve() != path or digest(path) != record['sha256']:
        raise ValueError('published agent input differs')
    return json.loads(path.read_text())


def _execution_telemetry(events, before, after, process_started):
    model_turn = process_started and any(
        (event.get('type') == 'turn.completed'
         and type(event.get('usage', {}).get('output_tokens')) is int
         and event['usage']['output_tokens'] > 0)
        or (event.get('type') == 'item.completed'
            and event.get('item', {}).get('type') == 'agent_message'
            and bool(event['item'].get('text')))
        for event in events if isinstance(event, dict))
    valid_meter = (isinstance(before, dict) and isinstance(after, dict)
        and isinstance(before.get('attempts'), list) and isinstance(after.get('attempts'), list)
        and before.get('arm_sha256') == after.get('arm_sha256')
        and before.get('started_at_unix') == after.get('started_at_unix')
        and after['attempts'][:len(before['attempts'])] == before['attempts']
        and len(after['attempts']) >= len(before['attempts']))
    calls = [row.get('controller_attempts', {}).get('native_calls')
        for row in after['attempts'][len(before['attempts']):] if isinstance(row, dict)] if valid_meter else []
    native_calls = sum(value for value in calls if type(value) is int and value > 0)
    return {'process_started': process_started, 'model_turn_observed': bool(model_turn),
        'native_candidate_execution': native_calls > 0, 'new_native_attempt_calls': native_calls,
        'meter_prefix_preserved': valid_meter,
        'actual_agent_executed': bool(model_turn and native_calls > 0)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--agent-dir', type=Path, required=True)
    parser.add_argument('--python', type=Path, required=True)
    parser.add_argument('--python-sha256', required=True)
    parser.add_argument('--source-repos', type=Path, required=True)
    parser.add_argument('--metadata', type=Path, required=True)
    parser.add_argument('--history-helper', type=Path, required=True)
    parser.add_argument('--model')
    parser.add_argument('--publication-timeout-seconds', type=int, default=4200)
    args = parser.parse_args()
    interpreter = args.python.absolute()
    if not interpreter.is_file() or digest(interpreter) != args.python_sha256:
        raise ValueError('controller interpreter differs from trusted parent binary pin')
    repo, run, agent = args.repo.resolve(), args.run.resolve(), args.agent_dir.resolve()
    agent.mkdir(parents=True, exist_ok=False)
    authority = run/'AGENT_AUTHORITY.json'
    waiting = time.monotonic()
    while True:
        if authority.is_file():
            try:
                ticket = json.loads(authority.read_text())
                parent = bound(ticket['parent'])
                arm = bound(parent['arm'])
                break
            except (json.JSONDecodeError, KeyError):
                pass  # An original write may still be finishing; no native call.
        elif (run/'RESULT.json').is_file():
            (agent/'DISPATCH.json').write_text(json.dumps({'status':'UNKNOWN_RUN_FINISHED_WITHOUT_AGENT_ARM',
                'actual_agent_executed':False,'native_calls':0},indent=2)+'\n')
            return
        if time.monotonic()-waiting >= args.publication_timeout_seconds:
            (agent/'DISPATCH.json').write_text(json.dumps({'status':'UNKNOWN_NO_PUBLISHED_AGENT_ARM',
                'actual_agent_executed':False,'native_calls':0},indent=2)+'\n')
            return
        time.sleep(0.25)
    if (ticket['schema'] != 'UDM_NATIVE_CLI_AUTHORITY_V44' or ticket['operation'] != 'agent'
            or ticket['repo'] != str(repo)
            or parent['schema'] != 'UDM_NATIVE_AGENT_PARENT_RECEIPT_V44'
            or parent['controller_source_sha256'] != digest(repo/'research/unified_consequence_runtime/qualify_native_frontier_v44.py')
            or arm['schema'] != 'UDM_CODING_AGENT_NATIVE_ARM_V44'
            or arm['candidate_budget'] != 8 or arm['total_acquisition_native_calls'] != 512
            or arm['total_acquisition_wall_seconds'] != 3600):
        raise ValueError('wrong frozen agent publication')
    remaining = parent['started_at_unix']+3600-time.time()
    if remaining <= 0:
        (agent/'DISPATCH.json').write_text(json.dumps({'status':'UNKNOWN_AGENT_BUDGET_EXPIRED_BEFORE_DISPATCH',
            'actual_agent_executed':False,'parent':ticket['parent']},indent=2)+'\n')
        return
    authority_hash = digest(authority)
    frozen = bound(ticket['freeze'])
    metadata = args.metadata.resolve()
    helper = args.history_helper.resolve()
    for path in (metadata, helper):
        if (not path.is_relative_to(repo) or path.is_symlink()
                or frozen['files'].get(path.relative_to(repo).as_posix()) != digest(path)):
            raise ValueError('training history input differs from frozen source')
    history = agent/'TRAINING_SHARED_HISTORY.json'
    projection_command = [str(interpreter), '-B', str(helper), '--arm', parent['arm']['path'],
        '--authority', str(authority), '--authority-sha256', authority_hash, '--metadata', str(metadata),
        '--metadata-sha256', frozen['files'][metadata.relative_to(repo).as_posix()], '--out', str(history)]
    try:
        with (agent/'history-projection.stdout').open('w') as stdout, (agent/'history-projection.stderr').open('w') as stderr:
            projected = subprocess.run(projection_command,text=True,stdout=stdout,stderr=stderr,timeout=remaining)
    except (OSError, subprocess.TimeoutExpired) as error:
        (agent/'DISPATCH.json').write_text(json.dumps({'status':'UNKNOWN_TRAINING_HISTORY_PROJECTION_LAUNCH',
            'actual_agent_executed':False,'projection_command':projection_command,'error':type(error).__name__+': '+str(error)},indent=2)+'\n')
        return
    if projected.returncode != 0:
        (agent/'DISPATCH.json').write_text(json.dumps({'status':'UNKNOWN_TRAINING_HISTORY_PROJECTION_REFUSED',
            'actual_agent_executed':False,'projection_command':projection_command,
            'projection_returncode':projected.returncode},indent=2)+'\n')
        return
    remaining = parent['started_at_unix']+3600-time.time()
    if remaining <= 0:
        raise ValueError('agent budget expired during charged training history projection')
    native = [str(interpreter), '-B', '-m',
        'research.unified_consequence_runtime.qualify_native_frontier_v44',
        '--agent-spec', parent['arm']['path'], '--authority', str(authority),
        '--authority-sha256', authority_hash, '--candidate', 'CANDIDATE.json', '--out', 'NEW_EVIDENCE_DIR']
    prompt = (
        'Execute the actual matched coding-agent arm. Read only the exact published ARM and its prepared '
        'source, original candidate catalog/orders, native residual, projected current-binding training history, and pinned '
        'MSI/Triskelion implementations. The training projection explicitly supplies the same original training '
        'catalog, orders, contexts, profiles, episodes, probe evidence, complete retained receipts and observations '
        'used by the developmental and informed-ledger selections. Its exact training source/test blobs are allowed. '
        'Do not read RESULT.json, raw shared ledger/CAS beyond the projection, later future cold/warm/ledger results, '
        'screening raw reports, repaired upstream production/patch/PR body, or sibling comparator outputs. '
        'Do not fetch or query target metadata/source. Do not edit tests, configuration, verifiers, trusted '
        'source, retained program bytes or meter. Choose at most eight ordered proposals from the exact '
        'original catalog. Write each strict candidate JSON under this workspace. Invoke only the following '
        'original native command, substituting fresh candidate/output paths. Preserve every failure and '
        'partial result. Stop at the first independent PASS or any bound/refusal; do not reset clocks or meters. '
        'The total512native-call/3600second meter already includes common acquisition; model/tool/wall costs '
        'must be retained separately. Report actual observations and limits without claiming G4.\n\n'
        'ARM: '+parent['arm']['path']+'\nTraining projection: '+str(history)+'\nTraining projection SHA256: '+digest(history)+
        '\nOriginal method source root: '+str(args.source_repos.resolve())+
        '\nFrozen controller repository: '+str(repo)+'\nNative command:\n'+shlex.join(native)+'\n')
    (agent/'PROMPT.md').write_text(prompt)
    command = ['codex','exec','--cd',str(agent),'--add-dir',str(run),'--sandbox','workspace-write',
        '--skip-git-repo-check','--ephemeral','--json','--output-last-message',str(agent/'FINAL.md')]
    if args.model:
        command += ['--model',args.model]
    command += ['-']
    meter = Path(arm['meter_path'])
    meter_before = json.loads(meter.read_text())
    (agent/'ARM_METER.before.json').write_text(json.dumps(meter_before,indent=2)+'\n')
    record = {'schema':'UDM_V44_ACTUAL_AGENT_DISPATCH_V1','status':'RUNNING','command':command,
        'requested_model':args.model or 'CLI_DEFAULT_UNRESOLVED',
        'controller_interpreter':{'argv_path':str(interpreter),'realpath':str(interpreter.resolve()),
            'executable_sha256':digest(interpreter)},
        'process_started':False,'model_turn_observed':False,'native_candidate_execution':False,
        'actual_agent_executed':False,
        'authority':{'path':str(authority),'sha256':authority_hash},'arm':parent['arm'],
        'parent':ticket['parent'],'started_at_unix':time.time(),'remaining_arm_seconds_at_dispatch':remaining,
        'training_history':{'path':str(history),'sha256':digest(history)},'projection_command':projection_command,
        'history_helper_sha256':digest(helper),'metadata_sha256':digest(metadata),
        'prompt_sha256':digest(agent/'PROMPT.md'),'publication_wait_wall_seconds':time.monotonic()-waiting,
        'publication_wait_accounting':'Operator wait interval overlaps common acquisition; retain separately, never add twice.',
        'source_access_boundary':
        'Transcript-audited operator isolation; no non-bypassability claim. Other-arm files are prohibited inputs.',
        'scientific_verdicts':{f'G{i}':'UNKNOWN' for i in range(2,7)}}
    (agent/'DISPATCH.json').write_text(json.dumps(record,indent=2)+'\n')
    started = time.monotonic()
    with (agent/'events.jsonl').open('w') as stdout, (agent/'stderr.log').open('w') as stderr:
        try:
            result = subprocess.run(command,input=prompt,text=True,stdout=stdout,stderr=stderr,
                env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0',PYTHONPATH=str(repo)),
                timeout=remaining)
            record.update(process_started=True,process_status='CLI_PROCESS_COMPLETED',returncode=result.returncode)
        except subprocess.TimeoutExpired:
            record.update(process_started=True,process_status='UNKNOWN_ACTUAL_AGENT_WALL_LIMIT',returncode=None)
        except OSError as error:
            record.update(process_status='UNKNOWN_CLI_PROCESS_LAUNCH',returncode=None,
                launch_error=type(error).__name__+': '+str(error))
    record.update(full_agent_process_wall_seconds=time.monotonic()-started,
        completed_at_unix=time.time(),event_log_sha256=digest(agent/'events.jsonl'))
    record['full_arm_elapsed_wall_seconds']=record['completed_at_unix']-parent['started_at_unix']
    record['wall_scope']='Full arm elapsed includes common acquisition, projection, handoff and agent execution; nested intervals are not additive.'
    meter_after = None
    try:
        meter_after = json.loads(meter.read_text())
        record['retained_native_meter']={'path':str(meter),'sha256':digest(meter)}
        (agent/'ARM_METER.after.json').write_text(json.dumps(meter_after,indent=2)+'\n')
    except (OSError,ValueError) as error:
        record['meter_telemetry_error']=type(error).__name__+': '+str(error)
    usage, invalid, events = [], [], []
    for number, line in enumerate((agent/'events.jsonl').read_text().splitlines(),1):
        try:
            event=json.loads(line)
            events.append(event)
            if event.get('type')=='turn.completed':
                usage.append(event)
        except (json.JSONDecodeError,AttributeError):
            invalid.append(number)
    record.update(model_usage_events=usage,invalid_event_json_lines=invalid,
        model_token_cost='MEASURED_EVENTS_RETAINED' if usage and not invalid else 'UNKNOWN')
    record.update(_execution_telemetry(events,meter_before,meter_after,record['process_started']))
    record['observed_model_identifiers']=sorted({event[key] for event in events if isinstance(event,dict)
        for key in ('model','model_id') if isinstance(event.get(key),str)})
    record['served_model_identity']='OBSERVED_EVENT_IDENTIFIERS_RETAINED' if record['observed_model_identifiers'] else 'UNKNOWN'
    record['status']=('ACTUAL_AGENT_NATIVE_CANDIDATE_EXECUTED' if record['actual_agent_executed'] else
        'UNKNOWN_MODEL_TURN_WITHOUT_NATIVE_CANDIDATE' if record['model_turn_observed'] else
        'UNKNOWN_NO_OBSERVED_MODEL_TURN')
    record['model_dollars']='UNKNOWN_UNLESS_SEPARATELY_MEASURED'
    record['engineering_cost']='UNKNOWN_UNLESS_SEPARATELY_MEASURED'
    record['tool_and_fee_costs']='UNKNOWN_UNLESS_MEASURED_IN_RETAINED_EVENTS_OR_SEPARATE_RECEIPTS'
    (agent/'DISPATCH.json').write_text(json.dumps(record,indent=2)+'\n')


if __name__ == '__main__':
    main()
