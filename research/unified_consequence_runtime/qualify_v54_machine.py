"""Qualify original native V54 construction over the retained, qualified UDM.

The JSONL journal is append-only. RESULT.json is its current review checkpoint;
failed stages and native observations remain in the output directory.
"""
from __future__ import annotations

import argparse
import ast
from contextlib import contextmanager
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

from .developmental_machine import Machine, canonical, digest
from .v54_runtime import V54Runtime
from .v54_source import OriginalV54, SOURCE_SHA256, WORLD_PINS


class Journal:
    def __init__(self, out: Path):
        self.out = Path(out).resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        self.path = self.out / 'qualification-events.jsonl'
        if self.path.exists():
            raise ValueError('qualification journal already exists; use a fresh output directory')
        self.result = {'schema': 'udm.v54.native-developmental-qualification.v1',
                       'status': 'RUNNING', 'stages': {}, 'claim_boundary': {
            'constructor': 'SUPPLIED_ORIGINAL_GENERIC_TOKEN_EMISSION_SUBSTRATE',
            'search_horizon': 'EXACT_ORIGINAL_ONE_NEW_REWRITE',
            'unrestricted_nonreachability': 'UNKNOWN', 'newly_blinded_discovery': 'NOT_CLAIMED',
            'fresh_browser_observation': 'NOT_CHECKED',
            'reference_monitor': 'UNKNOWN_NONBYPASSABILITY',
            'external_execution_authority': 'NONE'}}
        self._write('started', self.result)

    def _write(self, kind, payload):
        with self.path.open('a') as handle:
            handle.write(json.dumps({'kind': kind, 'time': time.time(), 'payload': payload}) + '\n')
            handle.flush()
            os.fsync(handle.fileno())
        temporary = self.out / 'RESULT.tmp'
        temporary.write_text(json.dumps(self.result, indent=2) + '\n')
        temporary.replace(self.out / 'RESULT.json')

    def update(self, key, value):
        self.result[key] = value
        self._write(key, value)

    @contextmanager
    def stage(self, name):
        started = time.perf_counter()
        self.result['stages'][name] = {'status': 'RUNNING'}
        self._write('stage_started', {'name': name})
        print(json.dumps({'stage': name, 'status': 'RUNNING'}), flush=True)
        try:
            yield
        except BaseException as error:
            self.result['stages'][name] = {'status': 'FAILED', 'reason': str(error),
                'error_type': type(error).__name__, 'seconds': time.perf_counter() - started}
            self._write('stage_failed', {'name': name, **self.result['stages'][name]})
            raise
        else:
            self.result['stages'][name] = {'status': 'PASS', 'seconds': time.perf_counter() - started}
            self._write('stage_completed', {'name': name, **self.result['stages'][name]})
            print(json.dumps({'stage': name, **self.result['stages'][name]}), flush=True)


@contextmanager
def native_environment(python: Path):
    old = os.environ.get('PATH', '')
    os.environ['PATH'] = str(Path(python).absolute().parent) + os.pathsep + old
    try:
        yield
    finally:
        os.environ['PATH'] = old


def resume_session(source, worlds, output, acquired, *, retain_native=True):
    """Restore producer knowledge only; independent native admission still reruns."""
    acquired = Path(acquired)
    record = json.loads(acquired.read_text())
    provenance = record.get('source_provenance', record.get('provenance', {}))
    if provenance.get('sha256') != SOURCE_SHA256 or provenance.get('world_pins') != WORLD_PINS:
        raise ValueError('resumed acquisition source/world provenance differs from exact pins')
    knowledge = record.get('result', record.get('acquisition', record))
    values = deepcopy(record.get('env', {}))
    mapping = {'operator': 'O1', 'repair_survivors_1': 'r1', 'repair_survivors_2': 'r2',
               'common': 'common', 'old_closure_obstruction': 'old_closure_obstruction_O1',
               'scope_word': 'scope_word', 'harm_first_word': 'harm_first', 'harm_line': 'harm_line'}
    for original, target in mapping.items():
        if target not in values and original in knowledge:
            values[target] = knowledge[original]
    if 'help_lines' in knowledge:
        values.setdefault('l1', knowledge['help_lines'][0])
        values.setdefault('l2', knowledge['help_lines'][1])
    required = {'O1', 'r1', 'r2', 'common', 'old_closure_obstruction_O1',
                'scope_word', 'harm_first', 'l1', 'l2', 'harm_line'}
    if not required <= values.keys() or values['O1'] is None:
        raise ValueError('resumed acquisition lacks original learned O1 and scope evidence')
    common = sorted(set(values['r1']) & set(values['r2']))
    if len(common) != 1 or common != values['common'] or values['O1'].get('dst') != common[0]:
        raise ValueError('resumed operator does not equal original survivor intersection')
    output = Path(output)
    native_source = Path(record.get('native_output', acquired.parent / 'native'))
    if retain_native and output.resolve() != native_source.resolve():
        if not native_source.is_dir():
            raise ValueError('original acquisition native receipts are missing')
        shutil.copytree(native_source, output, dirs_exist_ok=True)
    calls_path, segments_path = output / 'native-calls.jsonl', output / 'executed-segments.json'
    observed_calls = [json.loads(row) for row in calls_path.read_text().splitlines() if row] if retain_native and calls_path.exists() else []
    previous_calls = record.get('native_calls', [call for call in observed_calls if call.get('phase') == 'phase_a']) if retain_native else []
    if retain_native and (not isinstance(previous_calls, list) or any(call.get('phase') != 'phase_a' for call in previous_calls)
                          or observed_calls[:len(previous_calls)] != previous_calls):
        raise ValueError('original Phase A native observations differ from acquisition checkpoint')
    if retain_native and len(observed_calls) > len(previous_calls):
        # A new output can reuse the frozen acquisition while the failed run's
        # complete trace remains retained both at its origin and in this copy.
        if output.resolve() == native_source.resolve():
            raise ValueError('acquisition native output already contains later execution; use a fresh --out')
        (output / 'prior-complete-native-calls.jsonl').write_text(calls_path.read_text())
        calls_path.write_text(''.join(json.dumps(call) + '\n' for call in previous_calls))
    previous_segments = json.loads(segments_path.read_text()) if retain_native and segments_path.exists() else []
    previous_segments = [item for item in previous_segments if item.get('name') in ('imports', 'substrate', 'phase_a')]
    if retain_native and (not previous_calls or not any(item.get('name') == 'phase_a' and item.get('status') == 'completed' for item in previous_segments)):
        raise ValueError('resumed acquisition lacks completed original Phase A execution receipts')
    session = OriginalV54(source, {name: Path(worlds) / name for name in WORLD_PINS}, output)
    session.env.update({key: values[key] for key in required})
    help_words = {session.env['line_first_word'](values['l1']), session.env['line_first_word'](values['l2'])}
    harm_word = session.env['line_first_word'](values['harm_line'])
    if help_words != {values['scope_word']} or harm_word != values['harm_first'] or harm_word == values['scope_word']:
        raise ValueError('resumed learned scope is inconsistent with original help/harm lines')
    session._acquired = True
    session.native_calls = previous_calls
    if previous_segments:
        session.executed_segments = previous_segments + session.executed_segments
        segments_path.write_text(json.dumps(session.executed_segments, indent=2))
    session.source_provenance['resumed_acquisition'] = {'path': str(acquired.resolve()),
        'sha256': digest(acquired.read_bytes()), 'status': 'PRODUCER_KNOWLEDGE_REQUIRES_FRESH_NATIVE_ADMISSION'}
    return session


def _task_caps(machine):
    selected = {}
    for node_id in machine.active_capabilities():
        operation = machine.descriptor(node_id).operation
        if operation in ('grouping', 'stars'):
            selected[operation] = node_id
    if set(selected) != {'grouping', 'stars'}:
        raise ValueError('qualified base state lacks live original E/D executable routes')
    return selected


def execute_protected(machine, assets, capabilities):
    tasks = json.loads((Path(assets) / 'full_no_eval.json').read_text())
    outcomes = {}
    for kind, ids in (('grouping', (62, 64, 65)), ('stars', (168, 169, 172))):
        for task_id in ids:
            task = next(item for item in tasks if item['task_id'] == task_id)
            response, warrant = machine.execute(capabilities[kind], task)
            outcomes[str(task_id)] = {'response_sha256': digest(canonical(response).encode()), 'warrant': warrant}
    return outcomes


def _source_range(session, start, end, phase):
    """Execute additional whole original statements for the executable baseline."""
    nodes = [node for node in session.program.tree.body if start <= node.lineno <= end]
    if not nodes or any(node.end_lineno > end for node in nodes):
        raise ValueError('baseline range cuts an original AST statement')
    session.phase = phase
    exec(compile(ast.Module(body=nodes, type_ignores=[]), session.program.filename, 'exec'), session.env)


def baseline(spec, out):
    spec = json.loads(Path(spec).read_text())
    started = time.perf_counter()
    destination = Path(out).parent
    destination.mkdir(parents=True, exist_ok=True)
    with native_environment(Path(spec['native_python'])):
        session = resume_session(Path(spec['source']), Path(spec['worlds']), destination / 'native',
                                 Path(spec['acquisition']), retain_native=False)
        session.prepare_target()
        session.program.execute('warm_prepare', session.env)
        _source_range(session, 168, 171, 'baseline_original_O1_reuse')
        session.state_snapshot('warm-after-O1')
        session._warm_prepared = session._warm_operator_applied = True
        result = session.warm_search()
        _source_range(session, 200, 207, 'baseline_original_final_execution')
        final = session.state_snapshot('final')
        _source_range(session, 210, 214, 'baseline_original_O1_ablation')
        causal = {'cold': session.env['cold'], 'after_O1_only': session.env['mid'],
                  'after_O1_O2': session.env['warm'], 'O1_ablated_O2_present': session.env['ablated_O1']}
        if not (causal['cold'] is False and causal['after_O1_only'] is False and
                causal['after_O1_O2'] is True and causal['O1_ablated_O2_present'] is False):
            raise AssertionError('fresh original executable-ledger baseline causal checks failed')
        answer = {'status': 'PASS', 'source_sha256': SOURCE_SHA256,
            'equal_information': True, 'memory': 'PERSISTED_EXECUTABLE_O1_AND_SAME_ORIGINAL_SOURCE',
            'causal_maintenance': 'NO_UDM_ROUTING_OR_LEDGER', 'warm_search': result,
            'final_source_sha256': final['source_sha256'], 'causal': causal,
            'native_summary': session.native_summary(), 'seconds': time.perf_counter() - started,
            'warm_native_checks': sum(call['phase'] == 'warm' for call in session.native_calls)}
    Path(out).write_text(json.dumps(answer, indent=2) + '\n')
    return answer


def replay(spec, out):
    spec = json.loads(Path(spec).read_text())
    started = time.perf_counter()
    with native_environment(Path(spec['native_python'])):
        machine = Machine(Path(spec['components']), Path(spec['state']), Path(spec['evaluator']), Path(spec['config']))
        session = OriginalV54(Path(spec['source']), {name: Path(spec['worlds']) / name for name in WORLD_PINS},
                              Path(out).parent / 'restart-native')
        runtime = V54Runtime(machine, session, Path(spec['source']), Path(spec['worlds']), Path(spec['native_python']))
        operators = spec['operators']
        runtime.restore_session(operators)
        for old in spec['withdrawn']:
            if old in machine.mt.live_ids(machine.log) or old in machine.flash_live_ids():
                raise AssertionError('cold restart resurrected a withdrawn V54 generation')
        session.make_double_broken()
        effects = [runtime.apply(node_id)[1] for node_id in operators]
        native = session.execute_native()
        if not native['passed']:
            raise AssertionError('cold restarted executable V54 route failed native target')
        consequence, receipt = runtime.native_consequence(operators, 'cold_restart')
        protected = execute_protected(machine, Path(spec['assets']), spec['protected_capabilities'])
        result = {'status': 'PASS', 'native': native, 'consequence': consequence,
                  'independent_receipt': receipt, 'effects': effects, 'protected': protected,
                  'withdrawn_generations_inactive': True, 'acquisition_rerun': False,
                  'history_retained': set(spec['historical_ids']) <= set(machine.mt.ids(machine.log)),
                  'costs': machine.costs, 'seconds': time.perf_counter() - started}
        if not result['history_retained']:
            raise AssertionError('cold restart lost append-only history')
    Path(out).write_text(json.dumps(result, indent=2) + '\n')
    return result


def _subprocess_mode(python, mode, spec, out, *, timeout):
    command = [str(python), '-B', '-m', 'research.unified_consequence_runtime.qualify_v54_machine',
               mode, str(spec), '--out', str(out)]
    process = subprocess.run(command, text=True, capture_output=True, timeout=timeout)
    (Path(out).parent / ('process-' + mode[2:] + '.log')).write_text(process.stdout + process.stderr)
    if process.returncode:
        raise RuntimeError(f'{mode} process failed ({process.returncode}); see process log')
    return json.loads(Path(out).read_text())


def qualify(args):
    journal = Journal(args.out)
    started = time.perf_counter()
    out, state, assets = args.out.resolve(), args.out.resolve() / 'state', args.config.resolve().parent
    session = machine = None
    try:
        with native_environment(args.native_python):
            with journal.stage('restore_qualified_base'):
                if state.exists():
                    raise ValueError('qualification state already exists; refusing to mix separate executions')
                shutil.copytree(args.base_state, state)
                machine = Machine(args.components, state, args.evaluator, args.config)
                historical = set(machine.mt.ids(machine.log))
                prior_flash = {value for value in machine.flash['summary']['active_capability_ids'] if not value.startswith('udm:warrant:')}
                protected_caps = _task_caps(machine)
                journal.update('base', {'historical_records': len(historical), 'source_flash_capabilities': len(prior_flash),
                    'state_sha256': digest((state / 'metatron-ledger.jsonl').read_bytes()), 'protected_capabilities': protected_caps})
            with journal.stage('original_O1_acquisition'):
                acquisition = args.resume_acquisition or out / 'acquired-o1.json'
                if args.resume_acquisition:
                    session = resume_session(args.source, args.worlds, out / 'native', acquisition)
                    learned = session.acquire_o1()
                else:
                    session = OriginalV54(args.source, {name: args.worlds / name for name in WORLD_PINS}, out / 'native')
                    learned = session.acquire_o1()
                    values = {name: deepcopy(session.env[name]) for name in ('O1', 'r1', 'r2', 'common',
                        'old_closure_obstruction_O1', 'scope_word', 'harm_first', 'l1', 'l2', 'harm_line')}
                    acquisition.write_text(json.dumps({'result': learned, 'env': values,
                        'source_provenance': session.source_provenance, 'native_output': str(session.output),
                        'native_calls': session.native_calls, 'process_calls': session.process_calls}, indent=2))
                if not learned['operator'] or not learned['old_closure_obstruction'] or not learned['scope_word']:
                    raise AssertionError('original O1 construction or scope gate failed')
                journal.update('O1_acquisition', learned)
                original_seconds = sum(item.get('duration_seconds', 0) for item in session.executed_segments if item.get('name') == 'phase_a' and item.get('status') == 'completed')
                journal.update('acquisition_cost', {'original_phase_a_seconds': original_seconds,
                    'phase_a_native_calls': sum(call['phase'] == 'phase_a' for call in session.native_calls),
                    'phase_a_native_test_seconds': sum(call['duration_seconds'] for call in session.native_calls if call['phase'] == 'phase_a'),
                    'resumed_without_rerunning': bool(args.resume_acquisition)})
            with journal.stage('native_target_and_O1_admission'):
                session.prepare_target()
                runtime = V54Runtime(machine, session, args.source, args.worlds, args.native_python)
                cap1 = runtime.admit_operator('O1', learned['operator'])
                journal.update('O1_capability', cap1)
            with journal.stage('protected_original_ED_before'):
                before_protected = execute_protected(machine, assets, protected_caps)
                journal.update('protected_before', before_protected)
            with journal.stage('original_complete_cold_search'):
                cold, cold_node = runtime.construct_next()
                if cold:
                    raise AssertionError('original cold one-new-rewrite horizon contains a native survivor')
                broken = session.state_snapshot('double-broken')
                broken_native = session.execute_native()
                if broken_native['passed']:
                    raise AssertionError('double-broken native target unexpectedly passed')
                journal.update('cold', {'survivors': cold, 'search_node': cold_node, 'native': broken_native})
            with journal.stage('UDM_O1_reuse_and_original_O2_construction'):
                warm, warm_node = runtime.construct_next(cap1)
                if not warm['operator'] or not warm['A1_obstruction']:
                    raise AssertionError('original warm constructor failed to derive a new O2')
                cap2 = runtime.admit_operator('O2', warm['operator'], (cap1,))
                effect2, effect2_node = runtime.apply(cap2)
                final_native = session.execute_native()
                if not final_native['passed']:
                    raise AssertionError('UDM routed O1 then O2 failed original native test')
                final = session.state_snapshot('final')
                consequence, receipt = runtime.native_consequence((cap1, cap2))
                journal.update('warm', {'construction': warm, 'search_node': warm_node, 'O2_capability': cap2,
                    'O2_effect': effect2, 'O2_effect_node': effect2_node, 'native': final_native,
                    'final_consequence': consequence, 'independent_receipt': receipt})
            with journal.stage('fresh_equal_information_executable_ledger_baseline'):
                folder = out / 'baseline'; folder.mkdir()
                spec = {'source': str(args.source.resolve()), 'worlds': str(args.worlds.resolve()),
                        'native_python': str(args.native_python.absolute()), 'acquisition': str(acquisition.resolve())}
                (folder / 'spec.json').write_text(json.dumps(spec, indent=2))
                comparison = _subprocess_mode(args.native_python, '--baseline', folder / 'spec.json', folder / 'RESULT.json', timeout=2400)
                actual_warm_calls = sum(call['phase'] == 'warm' for call in session.native_calls)
                if (comparison['warm_search']['operator'] != warm['operator'] or
                    comparison['warm_search']['survivors'] != warm['survivors'] or
                    comparison['final_source_sha256'] != final['source_sha256'] or
                    comparison['warm_native_checks'] != actual_warm_calls):
                    raise AssertionError('equally informed original executable baseline differs from UDM')
                comparison['comparison'] = 'TIE_ON_NATIVE_CAPABILITY_AND_SEARCH_HORIZON'
                journal.update('baseline', comparison)
            with journal.stage('selective_exact_O1_ancestor_withdrawal'):
                live_before = set(machine.mt.live_ids(machine.log))
                support = machine.descriptor(cap1).dependencies[0]
                revocation = machine.withdraw(cap1, 'controlled withdrawal of exact O1 source-support ancestor')
                live_after = set(machine.mt.live_ids(machine.log))
                if any(value in live_after for value in (support, cap1, cap2, warm_node, effect2_node, consequence)):
                    raise AssertionError('exact O1 withdrawal retained a dependent V54 executable/consequence')
                if not set(protected_caps.values()) <= live_after:
                    raise AssertionError('O1 withdrawal removed an unrelated protected E/D capability')
                blocked = {}
                for name, action in (('O1', lambda: runtime.apply(cap1)), ('O2', lambda: runtime.apply(cap2)),
                                     ('constructor_descendant', lambda: runtime.construct_next(cap1))):
                    try: action()
                    except PermissionError: blocked[name] = True
                    else: raise AssertionError('withdrawn V54 route still executable: ' + name)
                retained = execute_protected(machine, assets, protected_caps)
                if any(retained[key]['response_sha256'] != value['response_sha256'] for key, value in before_protected.items()):
                    raise AssertionError('unrelated protected E/D behavior changed after V54 withdrawal')
                journal.update('withdrawal', {'status': 'PASS', 'exact_ancestor': support, 'revocation': revocation,
                    'removed_ids': sorted(live_before - live_after), 'blocked': blocked, 'protected': retained,
                    'upstream_revocation': False})
            with journal.stage('independent_native_restoration_new_lineage'):
                restored1 = runtime.admit_operator('O1', learned['operator'], supersedes=cap1)
                restored2 = runtime.admit_operator('O2', warm['operator'], (restored1,), supersedes=cap2)
                session.make_double_broken()
                runtime.apply(restored1); runtime.apply(restored2)
                restored_native = session.execute_native()
                restored_consequence, restored_receipt = runtime.native_consequence((restored1, restored2), 'restore')
                if not restored_native['passed'] or restored1 == cap1 or restored2 == cap2:
                    raise AssertionError('restoration failed to create independently warranted new executable lineage')
                journal.update('restoration', {'status': 'PASS', 'operators': [restored1, restored2],
                    'supersedes': [cap1, cap2], 'native': restored_native, 'consequence': restored_consequence,
                    'independent_receipt': restored_receipt})
            with journal.stage('separate_process_cold_restart_native_and_ED'):
                spec = {name: str(getattr(args, name).resolve()) for name in ('source', 'worlds', 'components', 'evaluator', 'config')}
                spec.update(state=str(state), assets=str(assets), native_python=str(args.native_python.absolute()),
                    operators=[restored1, restored2], withdrawn=[support, cap1, cap2],
                    protected_capabilities=protected_caps, historical_ids=sorted(machine.mt.ids(machine.log)))
                (out / 'replay-spec.json').write_text(json.dumps(spec, indent=2))
                restarted = _subprocess_mode(Path(sys.executable), '--replay', out / 'replay-spec.json', out / 'cold-replay.json', timeout=1200)
                if any(restarted['protected'][key]['response_sha256'] != value['response_sha256'] for key, value in before_protected.items()):
                    raise AssertionError('cold restart changed old protected E/D semantics')
                journal.update('restart', restarted)
            final_machine = Machine(args.components, state, args.evaluator, args.config)
            if not historical <= set(final_machine.mt.ids(final_machine.log)):
                raise AssertionError('extension lost historical qualified UDM nodes')
            final_flash = {value for value in final_machine.flash['summary']['active_capability_ids'] if not value.startswith('udm:warrant:')}
            if final_flash != prior_flash:
                raise AssertionError('extension changed unrelated original FLASH source capabilities')
            journal.update('retention', {'historical_nodes': len(historical), 'all_retained': True,
                'source_flash_capabilities_unchanged': True,
                'old_generation_inactive': cap1 not in final_machine.mt.live_ids(final_machine.log),
                'closure_agreement': set(final_machine.mt.live_ids(final_machine.log)) == final_machine.flash_live_ids(),
                'final_ledger_sha256': digest((state / 'metatron-ledger.jsonl').read_bytes())})
            journal.update('native_summary', session.native_summary())
            journal.update('costs', machine.costs)
            journal.update('total_seconds', time.perf_counter() - started)
            journal.update('status', 'WARRANTED_BOUNDED_V54_TWO_GENERATION_EXTENSION')
            return journal.result
    except BaseException as error:
        if session is not None: journal.update('native_summary', session.native_summary())
        if machine is not None: journal.update('costs', machine.costs)
        journal.update('failure', {'reason': str(error), 'error_type': type(error).__name__,
                                  'traceback': traceback.format_exc()})
        journal.update('status', 'FAILED_OR_UNKNOWN')
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('/workspace/repos/triskelion'))
    parser.add_argument('--worlds', type=Path, default=Path('/workspace/v54-worlds'))
    parser.add_argument('--components', type=Path, default=Path('/workspace/components'))
    parser.add_argument('--base-state', type=Path, default=Path('/workspace/v54-worlds/base_udm/artifact/qualified-state'))
    parser.add_argument('--config', type=Path, default=Path('/workspace/v54-worlds/base_udm/artifact/qualification/original-depth5/config.json'))
    parser.add_argument('--evaluator', type=Path, default=Path('/workspace/repos/webarena-verified'))
    parser.add_argument('--native-python', type=Path, default=Path('/workspace/v54-venv/bin/python'))
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--resume-acquisition', type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--baseline', type=Path)
    mode.add_argument('--replay', type=Path)
    args = parser.parse_args()
    try:
        if args.baseline: result = baseline(args.baseline, args.out)
        elif args.replay: result = replay(args.replay, args.out)
        else: result = qualify(args)
    except BaseException as error:
        if args.baseline or args.replay:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(json.dumps({'status': 'FAILED_OR_UNKNOWN', 'reason': str(error),
                'error_type': type(error).__name__, 'traceback': traceback.format_exc()}, indent=2) + '\n')
        raise
    print(json.dumps({'status': result['status'], 'out': str(args.out)}), flush=True)


if __name__ == '__main__':
    main()
