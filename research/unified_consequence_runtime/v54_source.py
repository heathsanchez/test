"""Execute unchanged, pinned V54 AST phases against the pinned native worlds.

This is an operational adapter, not another implementation of V54 discovery.
The only original top-level assignments omitted are the four relocated paths and
OUT.mkdir. Original sh is wrapped for observation; its original acceptance rule
(including rejecting timeouts) remains intact and timeout receipts stay distinct.
"""
from __future__ import annotations

import ast
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import linecache
import os
from pathlib import Path
import signal
import subprocess
import time
from typing import Any, Mapping

SOURCE_COMMIT = '2dd5f41b6c7cec1004b8deaee4f976dd2a9ed21c'
SOURCE_PATH = 'experiments/METALOGIC_TWO_GENERATION_COMPOUNDING_V54.py'
SOURCE_SHA256 = '13c05aea8d6c1ce2db6d3d4b85c566ee3dbd2f3fcc1c3c8c14c1c2dece7f05ba'
WORLD_PINS = {
    'django': 'c6be0bf3bb744d234947cefd6def9f31d9655800',
    'requests': '8068356288978c4f54661ae6f95afe0e0831885e',
    'rich': '9d8f9a372cc5916fd4781fec207ced7ddac2f08f',
}
_SEGMENTS = {
    'imports': (1, 3),
    'substrate': (11, 93),
    'phase_a': (96, 121),
    'target': (124, 132),
    'target_definitions': (134, 160),
    'cold': (162, 162),
    'warm_prepare': (166, 167),
    'warm_assert': (172, 172),
    'warm_definition': (175, 192),
    'warm': (194, 197),
    'causal': (200, 214),
    'report': (216, 239),
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(repo: Path, *args: str) -> bytes:
    return subprocess.run(['git', '-C', str(repo), *args], check=True,
                          capture_output=True, timeout=30).stdout


class PinnedProgram:
    """Select whole original AST statements, retaining their original locations."""

    def __init__(self, source: bytes):
        if _sha(source) != SOURCE_SHA256:
            raise ValueError('original V54 source SHA256 does not match pin')
        self.source = source
        self.filename = f'git:{SOURCE_COMMIT}:{SOURCE_PATH}'
        self.tree = ast.parse(source, filename=self.filename)
        lines = source.splitlines(keepends=True)
        self.segments = {
            name: {'start_line': start, 'end_line': end,
                   'sha256': _sha(b''.join(lines[start - 1:end]))}
            for name, (start, end) in _SEGMENTS.items()
        }
        for name in self.segments:
            self.module(name)
        text = source.decode('utf-8')
        linecache.cache[self.filename] = (len(source), None, text.splitlines(True), self.filename)

    @classmethod
    def from_repo(cls, source_repo: Path) -> 'PinnedProgram':
        return cls(_git(Path(source_repo), 'show', f'{SOURCE_COMMIT}:{SOURCE_PATH}'))

    def module(self, name: str) -> ast.Module:
        start, end = _SEGMENTS[name]
        nodes = []
        for node in self.tree.body:
            if start <= node.lineno <= end:
                if node.end_lineno > end:
                    raise ValueError(f'segment {name} cuts an original AST statement')
                nodes.append(node)
        if not nodes:
            raise ValueError(f'empty original segment {name}')
        return ast.Module(body=nodes, type_ignores=[])

    def bootstrap_names(self) -> set[str]:
        return {node.id for name in ('imports', 'substrate')
                for node in ast.walk(self.module(name))
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)}

    def execute(self, name: str, namespace: dict) -> None:
        exec(compile(self.module(name), self.filename, 'exec'), namespace)


class _ObservedSubprocess:
    """Bound native processes and reap their process groups after a timeout."""

    def __init__(self, owner: 'OriginalV54'):
        self.owner = owner

    def __getattr__(self, name: str) -> Any:
        return getattr(subprocess, name)

    def run(self, args: Any, **kwargs: Any) -> subprocess.CompletedProcess:
        timeout = kwargs.pop('timeout', self.owner.reset_timeout)
        timeout = min(timeout, self.owner.maximum_timeout)
        check = kwargs.pop('check', False)
        kwargs['start_new_session'] = True
        cwd = str(Path(kwargs.get('cwd', '.')).resolve())
        if cwd not in {str(path) for path in self.owner.world_paths.values()}:
            raise PermissionError('native subprocess cwd is outside the pinned worlds')
        started = time.monotonic()
        receipt = {'command': args, 'cwd': cwd, 'timeout_seconds': timeout,
                   'phase': self.owner.phase, 'started_at': _now()}
        self.owner.process_calls.append(receipt)
        try:
            with subprocess.Popen(args, **kwargs) as process:
                try:
                    stdout, stderr = process.communicate(timeout=timeout)
                except subprocess.TimeoutExpired:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    stdout, stderr = process.communicate()
                    receipt.update(returncode=process.returncode, status='timeout')
                    raise subprocess.TimeoutExpired(args, timeout, output=stdout, stderr=stderr)
                receipt.update(returncode=process.returncode,
                               status=('timeout' if process.returncode == 124 else
                                       'pass' if process.returncode == 0 else 'native_failure'))
                result = subprocess.CompletedProcess(args, process.returncode, stdout, stderr)
                if check:
                    result.check_returncode()
                return result
        except BaseException as error:
            receipt.setdefault('status', 'error')
            receipt['exception'] = type(error).__name__
            raise
        finally:
            receipt['duration_seconds'] = time.monotonic() - started


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class OriginalV54:
    """Thin phase interface around the original, source-pinned V54 experiment."""

    def __init__(self, source_repo: Path, world_paths: Mapping[str, Path], output: Path,
                 *, maximum_timeout: float = 45, reset_timeout: float = 30):
        if set(world_paths) != set(WORLD_PINS):
            raise ValueError('world paths must name exactly django, requests, rich')
        if not (0 < reset_timeout <= maximum_timeout <= 60):
            raise ValueError('operational timeouts must be positive and at most 60 seconds')
        self.program = PinnedProgram.from_repo(Path(source_repo))
        self.world_paths = {name: Path(path).resolve() for name, path in world_paths.items()}
        if len(set(self.world_paths.values())) != 3:
            raise ValueError('native world paths must be distinct')
        for name, path in self.world_paths.items():
            try:
                head = _git(path, 'rev-parse', 'HEAD').decode().strip()
            except (OSError, subprocess.SubprocessError) as error:
                raise ValueError(f'{name} world pin cannot be verified') from error
            if head != WORLD_PINS[name]:
                raise ValueError(f'{name} world pin mismatch: {head}')
        self.output = Path(output).resolve()
        if any(self.output == path or path in self.output.parents
               for path in self.world_paths.values()):
            raise ValueError('output must be outside resettable native worlds')
        self.output.mkdir(parents=True, exist_ok=True)
        self.maximum_timeout = maximum_timeout
        self.reset_timeout = reset_timeout
        self.native_calls: list[dict] = []
        self.process_calls: list[dict] = []
        self.phase = 'bootstrap'
        self.executed_segments: list[dict] = []
        self.env: dict[str, Any] = {'__name__': 'original_v54',
            'OUT': self.output, 'DJ': self.world_paths['django'],
            'RQ': self.world_paths['requests'], 'RH': self.world_paths['rich']}
        self.source_provenance = {
            'commit': SOURCE_COMMIT, 'path': SOURCE_PATH, 'sha256': SOURCE_SHA256,
            'segments': deepcopy(self.program.segments), 'world_pins': dict(WORLD_PINS),
            'relocated_paths': {name: str(path) for name, path in self.world_paths.items()},
            'output': str(self.output),
            'omitted_original_path_lines': [5, 6, 7, 8, 9],
            'original_timeout_acceptance': 'timeout is rejected; receipts distinguish it from native test failure',
        }
        (self.output / 'ORIGINAL_V54.py').write_bytes(self.program.source)
        (self.output / 'source-provenance.json').write_text(json.dumps(self.source_provenance, indent=2))
        self._execute('imports')
        self._execute('substrate')
        self.env['subprocess'] = _ObservedSubprocess(self)
        self._original_sh = self.env['sh']
        self.env['sh'] = self._observed_sh
        self._acquired = self._target_prepared = self._cold_searched = False
        self._warm_prepared = self._warm_operator_applied = self._warm_searched = False

    def _execute(self, name: str) -> None:
        self.phase = name
        receipt = {'name': name, **self.program.segments[name], 'started_at': _now()}
        self.executed_segments.append(receipt)
        started = time.monotonic()
        try:
            self.program.execute(name, self.env)
            receipt['status'] = 'completed'
        except BaseException as error:
            receipt.update(status='error', exception=type(error).__name__)
            raise
        finally:
            receipt['duration_seconds'] = time.monotonic() - started
            (self.output / 'executed-segments.json').write_text(json.dumps(self.executed_segments, indent=2))

    def _candidate_snapshot(self, cwd: Path) -> dict[str, str]:
        paths = {
            self.world_paths['django']: ['django/db/backends/utils.py', 'django/core/paginator.py'],
            self.world_paths['requests']: ['src/requests/utils.py'],
            self.world_paths['rich']: ['rich/highlighter.py'],
        }
        return {relative: _sha((cwd / relative).read_bytes()) for relative in paths[cwd]}

    def _observed_sh(self, cmd: str, cwd: Path, timeout: float = 40) -> tuple[bool, str]:
        cwd = Path(cwd).resolve()
        receipt = {'id': len(self.native_calls), 'command': cmd, 'cwd': str(cwd),
                   'phase': self.phase, 'timeout_seconds': min(timeout, self.maximum_timeout),
                   'started_at': _now(), 'candidate_source_sha256': self._candidate_snapshot(cwd)}
        started = time.monotonic()
        before_process = len(self.process_calls)
        try:
            passed, output = self._original_sh(cmd, cwd, timeout)
            process = self.process_calls[-1] if len(self.process_calls) > before_process else {}
            receipt.update(passed=passed, output=output, returncode=process.get('returncode'),
                           status=process.get('status', 'error'))
            return passed, output
        except BaseException as error:
            receipt.update(passed=False, status='error', exception=type(error).__name__)
            raise
        finally:
            receipt['duration_seconds'] = time.monotonic() - started
            self.native_calls.append(receipt)
            with (self.output / 'native-calls.jsonl').open('a') as handle:
                handle.write(json.dumps(receipt) + '\n')

    def acquire_o1(self) -> dict:
        if not self._acquired:
            self._execute('phase_a')
            self._acquired = True
        return deepcopy({
            'operator': self.env['O1'], 'repair_survivors_1': self.env['r1'],
            'repair_survivors_2': self.env['r2'], 'common': self.env['common'],
            'old_closure_obstruction': self.env['old_closure_obstruction_O1'],
            'scope_word': self.env['scope_word'], 'harm_first_word': self.env['harm_first'],
            'help_lines': [self.env['l1'], self.env['l2']], 'harm_line': self.env['harm_line'],
        })

    def prepare_target(self) -> dict:
        if not self._acquired:
            raise RuntimeError('acquire_o1 must complete before prepare_target')
        if not self._target_prepared:
            self._execute('target')
            self._execute('target_definitions')
            self._execute('warm_definition')
            self._target_prepared = True
            self.state_snapshot('target-pristine')
        return self.target_state()

    def target_scope(self) -> dict:
        if not self._target_prepared:
            raise RuntimeError('prepare_target must complete before target access')
        return {'world': 'requests', 'relative_path': 'src/requests/utils.py',
                'line_no': self.env['line_no'], 'first_word': self.env['scope_word']}

    def target_state(self) -> dict:
        scope = self.target_scope()
        path = self.env['rq_path']
        return {'path': str(path), 'source_sha256': _sha(path.read_bytes()),
                'line': path.read_text().splitlines()[self.env['line_no'] - 1],
                'line_no': self.env['line_no'], 'scope': scope}

    def state_snapshot(self, name: str | None = None) -> dict:
        snapshot = {**self.target_state(), 'source_text': self.env['rq_path'].read_text()}
        if name is not None:
            if not name or any(character not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for character in name):
                raise ValueError('snapshot name must contain only letters, digits, hyphens, underscores')
            (self.output / f'state-{name}.json').write_text(json.dumps(snapshot, indent=2))
        return snapshot

    def cold_search(self) -> list[dict]:
        self.target_scope()
        if not self._cold_searched:
            self._execute('cold')
            self._cold_searched = True
            self.state_snapshot('double-broken')
        return deepcopy(self.env['cold_survivors'])

    def make_double_broken(self) -> dict:
        self.target_scope()
        self.phase = 'make_double_broken'
        self.env['make_double_broken']()
        self._warm_prepared = self._warm_operator_applied = False
        return self.target_state()

    def prepare_warm(self, operator: Mapping[str, str]) -> dict:
        if not self._acquired or dict(operator) != self.env.get('O1'):
            raise PermissionError('prepare_warm requires the acquired O1')
        self.target_scope()
        self._execute('warm_prepare')
        self._warm_prepared = True
        self._warm_operator_applied = False
        self.state_snapshot('warm-before-O1')
        return self.target_state()

    def apply_operator(self, operator: Mapping[str, str], task_scope: Mapping | None = None) -> dict:
        operator = dict(operator)
        if not any(operator == self.env.get(name) for name in ('O1', 'O2')):
            raise PermissionError('operator has not been acquired from the original source')
        expected = self.target_scope()
        if task_scope is not None and dict(task_scope) != expected:
            raise PermissionError('operator task scope does not match the learned native target scope')
        path = self.env['rq_path']
        before = path.read_bytes()
        line = path.read_text().splitlines()[self.env['line_no'] - 1]
        if not expected['first_word'] or self.env['line_first_word'](line) != expected['first_word']:
            raise PermissionError('current target line is outside the learned first-word scope')
        current = self.env['sites'](path, operator['src'], self.env['line_no'])
        if len(current) != 1:
            raise PermissionError('operator requires exactly one live source token on the target line')
        self.phase = 'apply_operator'
        self.env['mutate'](path, current[0], operator['dst'])
        if self._warm_prepared and operator == self.env.get('O1'):
            self._warm_operator_applied = True
            self.state_snapshot('warm-after-O1')
        return {'operator': operator, 'scope': expected, 'site': list(current[0]),
                'before_sha256': _sha(before), 'after_sha256': _sha(path.read_bytes()),
                'state': self.target_state()}

    def warm_search(self) -> dict:
        if not self._warm_prepared or not self._warm_operator_applied:
            raise RuntimeError('prepare_warm and runtime application of acquired O1 are required')
        if not self._warm_searched:
            self._execute('warm_assert')
            self.warm_residual_native = deepcopy(self.native_calls[-1])
            self._execute('warm')
            self._warm_searched = True
        return deepcopy({'operator': self.env['O2'], 'survivors': self.env['warm_survivors'],
                         'unique_pairs': self.env['unique_pairs'],
                         'A1_obstruction': self.env['old_A1_obstruction_O2'],
                         'residual_native': self.warm_residual_native})

    def execute_native(self) -> dict:
        self.target_scope()
        self.phase = 'execute_native'
        self.env['test_rq']()
        receipt = deepcopy(self.native_calls[-1])
        return {'passed': receipt['passed'], 'status': receipt['status'],
                'native_call_id': receipt['id'], 'returncode': receipt['returncode'],
                'source_sha256': self.target_state()['source_sha256'], 'native_call': receipt}

    def native_summary(self) -> dict:
        return {status: sum(call['status'] == status for call in self.native_calls)
                for status in ('pass', 'native_failure', 'timeout', 'error')}
