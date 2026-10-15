"""Finite source-native observation selection and existing typed-route activation.

No constructor or new observation grammar is synthesized here. Missing or tied
routes remain UNKNOWN. The full existing scope guard is always checked, even
when a smaller observation basis explains the finite candidate profiles.
"""
from __future__ import annotations

import ast
import argparse
from functools import lru_cache
import hashlib
import itertools
import json
import os
from pathlib import Path
import subprocess
import shutil
import sys
from threading import RLock
from types import ModuleType


SOURCE_PINS = {
    'core': {'repo': 'msi', 'commit': '5d448c0ecc82ff3945d009963064ebbb67d2f308',
             'path': 'consequential_core.py',
             'sha256': '2c8be1f9fde571bfcdba6d1daf8a0e680a9636f697687fd4c128a8b214975ad8'},
    'version_space': {'repo': 'msi', 'commit': '5d448c0ecc82ff3945d009963064ebbb67d2f308',
                      'path': 'consequential_version_space.py',
                      'sha256': '1494620801a524fce54ae9b87a55ae12b79094875084e883fe2183c044e181f9'},
    'minimal_basis': {'repo': 'test', 'commit': '52eb1e7995bd877a2b698efe1883ae2b80a03737',
                      'path': 'research/mathgraph_minimal_quotient/h11_quotient.py',
                      'sha256': 'f9c5146748c324bc951b076b0db30d1a3e947eacc0d9095492d4a12e983d1f1a'},
}
_NATIVE_LOAD_LOCK = RLock()


def _source(repos, name):
    pin = SOURCE_PINS[name]
    raw = subprocess.check_output(['git', '-C', str(repos/pin['repo']), 'show',
                                   pin['commit'] + ':' + pin['path']])
    if hashlib.sha256(raw).hexdigest() != pin['sha256']:
        raise ValueError('pinned native selection source changed: ' + name)
    return raw


def _module(name, raw):
    module = ModuleType(name)
    sys.modules[name] = module
    try:
        exec(compile(raw, '<pinned-native-selection:' + name + '>', 'exec'), module.__dict__)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


@lru_cache(maxsize=4)
def native_selectors(repos=None):
    """Load exact native definitions; never import the h11 experiment entrypoint."""
    with _NATIVE_LOAD_LOCK:
        repos = Path(repos or os.environ.get('UDM_SOURCE_REPOS', '/workspace/repos'))
        core = _module('_udm_selection_msi_core', _source(repos, 'core'))
        previous = sys.modules.get('consequential_core')
        sys.modules['consequential_core'] = core
        try:
            version_space = _module('_udm_selection_msi_version_space',
                                    _source(repos, 'version_space'))
        finally:
            if previous is None:
                sys.modules.pop('consequential_core', None)
            else:
                sys.modules['consequential_core'] = previous
        tree = ast.parse(_source(repos, 'minimal_basis'))
        function = next(node for node in tree.body
                        if isinstance(node, ast.FunctionDef) and node.name == 'minimal_basis')
        definitions = ast.Module(body=[function], type_ignores=[])
        namespace = {'itertools': itertools}
        exec(compile(definitions, '<pinned-native-jpl:minimal_basis>', 'exec'), namespace)
        return {'core': core, 'version_space': version_space,
                'minimal_basis': namespace['minimal_basis'], 'sources': SOURCE_PINS}


def select_and_execute(machine, task):
    """Discover available E/D routes from state; the caller supplies no method ID."""
    from .developmental_machine import safe_task

    task = safe_task(task)
    before = tuple(machine.active_capabilities())
    profiles = []
    available = []
    unsupported = []
    for capability_id in before:
        cap = machine.descriptor(capability_id)
        if not {'task_ids', 'template'} <= cap.scope.keys():
            unsupported.append(capability_id)
            continue
        profile = [int(task['task_id'] in cap.scope['task_ids']),
                   int(task['intent_template_id'] == cap.scope['template'])]
        applicable = machine.applicable(capability_id, task)
        profiles.append({'capability_id': capability_id, 'values': profile,
                         'applicable': applicable})
        if applicable:
            available.append(capability_id)
    basis = native_selectors()['minimal_basis'](
        [row['values'] for row in profiles], ['task_id_in_scope', 'intent_template_matches'])
    result = {'status': 'UNKNOWN_NO_APPLICABLE_METHOD' if not available else
                        'UNKNOWN_AMBIGUOUS_METHOD' if len(available) != 1 else
                        'VERIFIED_EXISTING_METHOD_ACTIVATION',
              'selected_capability': None, 'available_capabilities': list(before),
              'applicable_capabilities': available, 'profiles': profiles,
              'unsupported_input_schema': unsupported, 'observation_basis': basis,
              'basis_scope': 'finite current available-route profiles only; full scope guard still required',
              'sources': SOURCE_PINS, 'language_changed': False,
              'expressivity': 'NOT_TESTED', 'grammar_exhausted': 'UNKNOWN',
              'new_method_invented': False, 'authorization': 'LOCAL_RESEARCH_EXECUTION_ONLY',
              'classification': 'ROUTING_INTEGRATION_NOT_NEW_DOMAIN_RESULT'}
    premises = ()
    if len(available) == 1:
        selected = available[0]
        response, consequence = machine.execute(selected, task)
        result.update(selected_capability=selected, response=response, consequence=consequence)
        premises = (selected, consequence)
    if tuple(machine.active_capabilities()) != before:
        raise ValueError('selection unexpectedly changed the installed capability language')
    result['selection_event'] = machine.append('existing_method_selection',
        {'task_id': task['task_id'], **result}, premises)
    machine.flush()
    return result


def _state_digest(state):
    files = {str(path.relative_to(state)): hashlib.sha256(path.read_bytes()).hexdigest()
             for path in sorted(state.rglob('*')) if path.is_file()}
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def qualify(state, assets, components, evaluator, state_out):
    """Run on a saved COPY of retained state; never acquire E/D or touch V54 worlds."""
    from .developmental_machine import Machine

    state, assets, state_out = Path(state).resolve(), Path(assets), Path(state_out).resolve()
    if state == state_out or state in state_out.parents or state_out in state.parents:
        raise ValueError('selection state must be separate from its retained source state')
    before = _state_digest(state)
    shutil.copytree(state, state_out)
    machine = Machine(Path(components), state_out, Path(evaluator), assets/'config.json')
    tasks = {row['task_id']: row for row in json.loads((assets/'full_no_eval.json').read_text())}
    active = tuple(machine.active_capabilities())
    operations = {name: [cap for cap in active if machine.descriptor(cap).operation == name]
                  for name in ('grouping', 'stars')}
    if any(len(caps) != 1 for caps in operations.values()):
        raise ValueError('retained source state must have one live qualified E and D route')
    outcomes = []
    for task_id in (62, 64, 65, 168, 169, 172):
        task = tasks[task_id]
        selection = machine.select_and_execute(task)
        # Equally informed conventional enumeration uses identical live scopes/ops.
        informed = [cap for cap in active
                    if {'task_ids', 'template'} <= machine.descriptor(cap).scope.keys()
                    and machine.applicable(cap, task)]
        baseline = None
        if len(informed) == 1:
            baseline, _ = machine.execute(informed[0], task)
        outcomes.append({'task_id': task_id, 'selection': selection,
                         'equally_informed_available': informed,
                         'baseline_response': baseline,
                         'baseline_tie': selection.get('response') == baseline and baseline is not None})
    unchanged = tuple(machine.active_capabilities()) == active
    machine.withdraw(operations['grouping'][0], 'separate selection-only copied-state withdrawal')
    refused = machine.select_and_execute(tasks[62])
    independent = machine.select_and_execute(tasks[169])
    leak_refused = False
    try:
        machine.select_and_execute(tasks[169] | {'eval': {'reference': 'excluded'}})
    except ValueError:
        leak_refused = True
    after = _state_digest(state)
    gates = {
        'six_existing_native_outcomes': all(row['selection']['status'] == 'VERIFIED_EXISTING_METHOD_ACTIVATION'
            and row['selection']['response'].get('status') == 'SUCCESS' for row in outcomes),
        'equally_informed_same_operations_tie': all(row['baseline_tie'] for row in outcomes),
        'no_capability_language_change_during_selection': unchanged,
        'withdrawal_refuses_unknown': refused['status'] == 'UNKNOWN_NO_APPLICABLE_METHOD'
            and refused['grammar_exhausted'] == 'UNKNOWN',
        'independent_method_preserved': independent['selected_capability'] == operations['stars'][0],
        'evaluation_information_refused': leak_refused,
        'retained_input_state_unchanged': before == after,
    }
    return {'schema': 'metalogic.consequence-selection.integration.v1',
            'status': 'PASS_BOUNDED_ROUTING_INTEGRATION' if all(gates.values()) else 'FAIL_ROUTING_INTEGRATION',
            'classification': 'NEW_ROUTING_INTEGRATION_NOT_NEW_DOMAIN_RESULT',
            'native_successes': sum(row['selection']['status'] == 'VERIFIED_EXISTING_METHOD_ACTIVATION'
                and row['selection']['response'].get('status') == 'SUCCESS' for row in outcomes),
            'baseline': 'TIE_SAME_AVAILABLE_OPERATIONS' if all(row['baseline_tie'] for row in outcomes) else 'NOT_TIED',
            'gates': gates, 'outcomes': outcomes, 'withdrawal': refused,
            'independent_after_withdrawal': independent, 'sources': SOURCE_PINS,
            'retained_input_state': str(state), 'selection_state': str(state_out),
            'retained_source_state_before': before, 'retained_source_state_after': after,
            'selection_state_sha256': _state_digest(state_out),
            'costs': machine.costs, 'expressivity': 'NOT_TESTED', 'grammar_exhaustion': 'UNKNOWN',
            'economic_advantage': 'NOT_ESTABLISHED', 'new_method_invented': False,
            'prospective_frontier': 'NOT_FROZEN_NOT_RUN',
            'authority_nonbypassability': 'UNKNOWN'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True, help='retained input state, copied before use')
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--components', type=Path, required=True)
    parser.add_argument('--evaluator', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--state-out', type=Path)
    args = parser.parse_args()
    destination = args.state_out or args.out.parent/(args.out.stem + '-state')
    output = args.out.resolve()
    if any(output == state.resolve() or state.resolve() in output.parents
           for state in (args.state, destination)):
        parser.error('--out must be outside both retained input and copied selection state')
    report = qualify(args.state, args.assets, args.components, args.evaluator, destination)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'native_successes': report['native_successes'],
                      'baseline': report['baseline'], 'report': str(args.out),
                      'selection_state': str(destination)}, sort_keys=True))
    return 0 if all(report['gates'].values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())
