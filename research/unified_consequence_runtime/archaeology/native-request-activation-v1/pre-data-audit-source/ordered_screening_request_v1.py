"""Source-preserving request transport plus the remaining original outer budget.

Import/preparation never execute screening. The original process/source/index/
actor transport is retained; only its native CLI module changes. This outer
receipt grants neither native admission nor a scientific warrant.
"""
import time
_STARTED = time.monotonic()
_STARTED_UNIX = time.time()

import argparse
from decimal import Decimal
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys

HERE = Path(__file__).resolve().parent
OLD = Path('/workspace/qualification/native-namespace-v45-screening-audit-preparation')
OLD_FREEZE_SHA256 = 'bc0249e2cea713bedeaf5e97217bbead3e7dc0b436502ca4056188177f4f1c8b'
OLD_FACTORY_SHA256 = 'f7551245c790b8dfa7ac7a2dd2f190c95455bbc7dfd6d6fd1fcda09f7aa1b1fc'
OLD_CONTROLLER_SHA256 = '27a5d944c43e9c28836c53018ba11745b899871abbb14f674c89a8826de7cd3f'
PRIOR_PATH = Path('/workspace/qualification/native-namespace-v45-prospective-20261028T2335Z/ORDERED_DRIVER_OUTER_COSTS.json')
PRIOR_SHA256 = '6e0104a9c1cb91078a189b349694496038f9ae21003ec883e13decc4bd7b95d1'
PRIOR_CHARGED = Decimal('25.756850843')
TOTAL_BUDGET = Decimal('7200')
SCHEMA = 'UDM_REQUEST_ACTIVATION_V1_SCREENING_OUTER_BUDGET'
SCOPE = 'OUTER_TRANSPORT_COMPLETION_AND_COST_ONLY'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def original_factory():
    freeze = OLD/'AUDITOR_FREEZE.json'
    if freeze.is_symlink() or sha(freeze) != OLD_FREEZE_SHA256:
        raise ValueError('original 47-file independent freeze differs')
    frozen = json.loads(freeze.read_text())['source_files_sha256']
    for name, digest in frozen.items():
        path = Path(name)
        if path.is_symlink() or sha(path) != digest:
            raise ValueError('original frozen dependency differs: '+name)
    factory = OLD/'ordered_screening_v45.py'
    controller = OLD/'original_run_ordered_screening.py'
    if (frozen.get(str(factory)) != OLD_FACTORY_SHA256 or sha(factory) != OLD_FACTORY_SHA256
            or frozen.get(str(controller)) != OLD_CONTROLLER_SHA256 or sha(controller) != OLD_CONTROLLER_SHA256):
        raise ValueError('original ordered transport source differs')
    spec = importlib.util.spec_from_file_location('_request_original_ordered_factory', factory)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def prepare_driver_source():
    source = original_factory().prepare_driver_source()
    before = 'research.unified_consequence_runtime.qualify_native_frontier_v45'
    after = 'research.unified_consequence_runtime.qualify_native_frontier_request_v1'
    if source.count(before) != 1:
        raise ValueError('original native CLI transport binding site differs')
    return source.replace(before, after)


def prior_outer_cost():
    if PRIOR_PATH.is_symlink() or sha(PRIOR_PATH) != PRIOR_SHA256:
        raise ValueError('exact original outer-cost evidence differs')
    value = json.loads(PRIOR_PATH.read_text())
    observed = value.get('outer_wall_seconds')
    if (value.get('schema') != 'UDM_V45_INDEPENDENT_SCREENING_OUTER_COSTS'
            or type(observed) not in (int, float) or not math.isfinite(observed)
            or not 0 <= PRIOR_CHARGED-Decimal(str(observed)) < Decimal('0.000000001')
            or value.get('raw_native_outcomes_accessed') is not False
            or value.get('learner_or_policy_execution') is not False
            or value.get('retry_or_pool_substitution') is not False):
        raise ValueError('original outer cost or its declared scope differs')
    return {'path': str(PRIOR_PATH), 'sha256': PRIOR_SHA256,
            'observed_outer_wall_seconds': observed,
            'charged_outer_wall_seconds': float(PRIOR_CHARGED),
            'rounding_boundary': 'Charge the original observed interval rounded upward to nine decimal places.'}


def remaining_seconds(new_elapsed):
    if type(new_elapsed) not in (int, float) or not math.isfinite(new_elapsed) or new_elapsed < 0:
        raise ValueError('invalid measured new outer interval')
    return float(max(Decimal(0), TOTAL_BUDGET-PRIOR_CHARGED-Decimal(str(new_elapsed))))


def process_clock(*, raw=None, clock_ticks=None):
    """Linux process birth, conservatively rounded down by the kernel tick."""
    raw = Path('/proc/self/stat').read_text() if raw is None else raw
    clock_ticks = os.sysconf('SC_CLK_TCK') if clock_ticks is None else clock_ticks
    if type(clock_ticks) is not int or clock_ticks <= 0:
        raise ValueError('invalid independently observed Linux clock tick rate')
    start_ticks = int(raw.rsplit(')', 1)[1].split()[19])
    if start_ticks < 0:
        raise ValueError('invalid Linux process birth tick')
    return {'clock': 'CLOCK_BOOTTIME', 'clock_ticks_per_second': clock_ticks,
            'process_start_ticks': start_ticks,
            'process_start_lower_bound_seconds': float(Decimal(start_ticks)/clock_ticks),
            'scope': 'Kernel process-birth lower bound includes interpreter startup; conservative overcharge is less than one kernel tick.'}


def outer_elapsed(clock, *, now=None):
    now = time.clock_gettime(time.CLOCK_BOOTTIME) if now is None else now
    elapsed = float(Decimal(str(now))-Decimal(str(clock['process_start_lower_bound_seconds'])))
    remaining_seconds(elapsed)
    return elapsed


def stop_child(process):
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass  # The independently awaited process may have just exited.
    return process.wait()


def budget_result(*, new_outer_wall_seconds, returncode, timed_out, process_completed):
    remaining_seconds(new_outer_wall_seconds)
    combined = PRIOR_CHARGED+Decimal(str(new_outer_wall_seconds))
    qualified = (type(returncode) is int and returncode == 0 and timed_out is False
                 and process_completed is True and combined <= TOTAL_BUDGET)
    return {'status': 'COMPLETED_WITHIN_ORIGINAL_SCREENING_BUDGET' if qualified else 'UNKNOWN_SCREENING_OUTER_BUDGET_OR_COMPLETION',
            'qualified': qualified, 'scope': SCOPE, 'total_budget_seconds': float(TOTAL_BUDGET),
            'prior_charged_outer_wall_seconds': float(PRIOR_CHARGED),
            'declared_remaining_seconds': float(TOTAL_BUDGET-PRIOR_CHARGED),
            'new_outer_wall_seconds': new_outer_wall_seconds,
            'combined_outer_wall_seconds': float(combined),
            'nested_intervals_not_additive': True}


def validate_settings(environment):
    value = dict(environment)
    for key, length in (('UDM_SCREENING_SOURCE_COMMIT', 40), ('UDM_PREQUERY_COMMIT', 40),
                        ('UDM_SCREENING_AUTHORITY_SHA256', 64)):
        if not re.fullmatch('[0-9a-f]{'+str(length)+'}', value.get(key, '')):
            raise ValueError('independently supplied exact screening input required: '+key)
    if not value.get('UDM_SCREENING_ACTOR_IDENTITY', '').strip():
        raise ValueError('actual independent screening actor identity required')
    for key in ('UDM_REPO', 'UDM_RECORDS', 'UDM_OPERATOR', 'UDM_CONTROLLER_PYTHON', 'UDM_RUNTIME_PATHS'):
        if not isinstance(value.get(key), str) or not Path(value[key]).is_absolute():
            raise ValueError('absolute original transport setting required: '+key)
    expected = Path(value['UDM_REPO'])/'research/unified_consequence_runtime/archaeology/native-request-activation-v1/prospective'
    if Path(value['UDM_RECORDS']) != expected:
        raise ValueError('request version requires its exact committed records path')
    return value


def completed_process_metadata(out, environment):
    names = ('ORDERED_PROCESS_COSTS.json', 'SCREENING_ACTOR_ATTESTATION.json')
    values, descriptors = [], {}
    for name in names:
        path = out/name
        if path.is_symlink() or not path.is_file():
            return False, descriptors
        values.append(json.loads(path.read_text()))
        descriptors[name] = {'path': str(path), 'sha256': sha(path)}
    manifest, actor = values
    complete = (manifest.get('schema') == 'UDM_V45_SCREENING_OPERATOR_PROCESS_COSTS_V1'
        and actor.get('schema') == 'UDM_V45_SCREENING_ACTOR_ATTESTATION_V1'
        and manifest.get('completed') is True and manifest.get('retries_performed') is False
        and manifest.get('no_retry_or_substitution') is True
        and actor.get('completed_fixed_pool') is True and actor.get('source_unchanged') is True
        and actor.get('index_changes') == []
        and actor.get('actor_identity') == environment['UDM_SCREENING_ACTOR_IDENTITY']
        and actor.get('prequery_commit') == environment['UDM_PREQUERY_COMMIT']
        and actor.get('independent_screener') is True
        and all(actor.get(key) is False for key in ('search_or_policy_outcomes_accessed',
            'learner_future_source_accessed', 'native_test_reruns_or_case_retries_performed'))
        and actor.get('controller_manifest_sha256') == descriptors[names[0]]['sha256']
        and all(value.get('source_commit') == environment['UDM_SCREENING_SOURCE_COMMIT']
                and value.get('authority_sha256') == environment['UDM_SCREENING_AUTHORITY_SHA256']
                for value in values))
    return complete, descriptors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--child', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.child:
        validate_settings(os.environ)
        exec(compile(prepare_driver_source(), str(HERE/'ordered_screening_request_v1.py')+':original-transport', 'exec'),
             {'__name__': '__request_original_independent_screening_transport__',
              '__file__': str(OLD/'original_run_ordered_screening.py')})
        return 0
    environment = validate_settings(os.environ)
    out = Path(environment['UDM_OPERATOR'])
    receipt = out/'SCREENING_OUTER_BUDGET.json'
    command = [sys.executable, '-B', str(Path(__file__).resolve()), '--child']
    record = {'schema': SCHEMA, 'status': 'RUNNING', 'qualified': False, 'scope': SCOPE,
        'source_commit': environment['UDM_SCREENING_SOURCE_COMMIT'],
        'prequery_commit': environment['UDM_PREQUERY_COMMIT'],
        'authority_sha256': environment['UDM_SCREENING_AUTHORITY_SHA256'],
        'actor_identity': environment['UDM_SCREENING_ACTOR_IDENTITY'],
        'records_path': environment['UDM_RECORDS'], 'command': command,
        'started_at_unix': _STARTED_UNIX, 'returncode': None, 'timed_out': False,
        'original_freeze_sha256': OLD_FREEZE_SHA256, 'original_factory_sha256': OLD_FACTORY_SHA256,
        'original_controller_sha256': OLD_CONTROLLER_SHA256,
        'versioned_transport_sha256': sha(__file__), 'process_completed': False,
        'raw_native_outcomes_accessed': False, 'retry_or_pool_substitution': False,
        'scientific_verdicts': {'G'+str(i): 'UNKNOWN' for i in range(2, 7)}}
    with receipt.open('x') as handle:
        handle.write(json.dumps(record, sort_keys=True, indent=2)+'\n')
    cpu_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    process, clock = None, None
    try:
        clock = process_clock()
        record['outer_process_clock'] = clock
        record['prior_outer'] = prior_outer_cost()
        source = prepare_driver_source()
        record['prepared_original_source_sha256'] = hashlib.sha256(source.encode()).hexdigest()
        timeout = remaining_seconds(outer_elapsed(clock))
        record['child_timeout_seconds'] = timeout
        if timeout <= 0:
            raise TimeoutError('original total screening horizon exhausted before child launch')
        with (out/'ORDERED_DRIVER.stdout.log').open('xb') as stdout, (out/'ORDERED_DRIVER.stderr.log').open('xb') as stderr:
            process = subprocess.Popen(command, cwd=environment['UDM_REPO'], env=environment,
                                       stdout=stdout, stderr=stderr, start_new_session=True)
            record['child_started_at_unix'] = time.time()
            try:
                record['returncode'] = process.wait(timeout=remaining_seconds(outer_elapsed(clock)))
            except subprocess.TimeoutExpired:
                record['timed_out'] = True
                record['returncode'] = stop_child(process)
        record['process_completed'], record['original_completion_artifacts'] = completed_process_metadata(out, environment)
    except (Exception, KeyboardInterrupt) as error:
        record['obstruction'] = type(error).__name__+': '+str(error)
        record['process_completed'] = False
    finally:
        if process is not None and process.poll() is None:
            try:
                record['returncode'] = stop_child(process)
            except Exception as error:
                record['cleanup_obstruction'] = type(error).__name__+': '+str(error)
                record['process_completed'] = False
        cpu_after = resource.getrusage(resource.RUSAGE_CHILDREN)
        self_cpu = resource.getrusage(resource.RUSAGE_SELF)
        if clock is not None:
            record['finished_clock_boottime_seconds'] = time.clock_gettime(time.CLOCK_BOOTTIME)
            elapsed = outer_elapsed(clock, now=record['finished_clock_boottime_seconds'])
        else:
            elapsed = time.monotonic()-_STARTED
            record['process_completed'] = False
        record.update(budget_result(new_outer_wall_seconds=elapsed,
            returncode=record['returncode'], timed_out=record['timed_out'], process_completed=record['process_completed']))
        record.update(ended_at_unix=time.time(), child_user_cpu_seconds=cpu_after.ru_utime-cpu_before.ru_utime,
            child_system_cpu_seconds=cpu_after.ru_stime-cpu_before.ru_stime,
            parent_user_cpu_seconds=self_cpu.ru_utime, parent_system_cpu_seconds=self_cpu.ru_stime,
            cost_boundary='Original measured outer interval plus this kernel-birth-to-finalization interval includes new interpreter startup/preflight/child/cleanup. Original nested case/native/compiler clocks are not added again. Final receipt I/O, actor preparation/model fees and unobserved lifecycle costs remain UNKNOWN.')
        for name in ('ORDERED_DRIVER.stdout.log', 'ORDERED_DRIVER.stderr.log'):
            path = out/name
            if path.is_file() and not path.is_symlink():
                record[name] = {'path': str(path), 'sha256': sha(path)}
        receipt.write_text(json.dumps(record, sort_keys=True, indent=2, allow_nan=False)+'\n')
    print(json.dumps({key: record[key] for key in ('schema', 'status', 'qualified', 'new_outer_wall_seconds', 'combined_outer_wall_seconds')}))
    return 0 if record['qualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
