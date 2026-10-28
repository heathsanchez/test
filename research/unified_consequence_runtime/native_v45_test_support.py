"""Exact frozen-byte native controls in disposable repositories only."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import types
import unittest

import pytest

from . import native_execution_v43 as previous
from . import native_source_v42 as source

ROOT = Path(__file__).parent / 'archaeology/native-namespace-v45/control-freeze/fixtures'
ENV_ROOT = Path('/workspace/qualification/native-namespace-v45-environment')
MODERN = Path(os.environ.get('UDM_V45_MODERN_PYTHON', str(ENV_ROOT / 'modern-runtime-final/venv/bin/python')))
LEGACY = Path(os.environ.get('UDM_V45_LEGACY_PYTHON', str(ENV_ROOT / 'original-runtimes/cpython-3.6.5-pytest-5.4.3-linux-x86_64/venv/bin/python')))
PROTOCOL = hashlib.sha256(b'V45 sealed engineering controls only').hexdigest()


def implementation(name='native_execution_v45'):
    assert Path(__file__).with_name(name + '.py').is_file(), name + ' is not implemented'
    module = importlib.import_module(__package__ + '.' + name)
    if name != 'native_execution_v45':
        return module

    # Record the exact public inputs before dispatch. The original production
    # entrypoint performs every collection, execution and validation operation.
    def collect(contract, authority, output_dir, *, policy):
        _record_context(output_dir, contract=contract, authority=authority, policy=policy)
        return module.collect(contract, authority, output_dir, policy=policy)

    def verify(contract, candidate, output_dir, *, authority, admission_certificate, policy):
        _record_context(output_dir, contract=contract, candidate=candidate, authority=authority,
                        certificate=admission_certificate, policy=policy)
        return module.verify(contract, candidate, output_dir, authority=authority,
                             admission_certificate=admission_certificate, policy=policy)

    def validate_certificate(contract, authority, certificate, *, policy, output_dir=None):
        _record_context(output_dir, contract=contract, authority=authority, certificate=certificate, policy=policy)
        return module.validate_certificate(contract, authority, certificate, policy=policy, output_dir=output_dir)

    def validate_receipt(contract, candidate, authority, certificate, receipt, *, policy,
                         output_dir=None, independent=True):
        _record_context(output_dir, contract=contract, candidate=candidate, authority=authority,
                        certificate=certificate, receipt=receipt, policy=policy, independent=independent)
        return module.validate_receipt(contract, candidate, authority, certificate, receipt,
            policy=policy, output_dir=output_dir, independent=independent)
    return types.SimpleNamespace(**dict(vars(module), collect=collect, verify=verify,
        validate_certificate=validate_certificate, validate_receipt=validate_receipt))


def _record_context(output, **context):
    if output is None:
        folder = Path(tempfile.mkdtemp(prefix='udm-v45-input-context-'))
        path = folder / 'CONTEXT.json'
    else:
        output = Path(output).absolute()
        output.parent.mkdir(parents=True, exist_ok=True)
        path = output.parent / (output.name + '.CONTEXT.json')
    path.write_text(previous.canonical(dict(schema='UDM_NATIVE_V45_TEST_CONTEXT', **context)) + '\n')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def git(repo, *args):
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0')
    return subprocess.check_output(['git', '--no-replace-objects', '-C', str(repo), *args],
                                   env=env, stderr=subprocess.PIPE, text=True).strip()


def commit(repo):
    git(repo, 'add', '.')
    git(repo, '-c', 'user.name=V45 Frozen Control', '-c', 'user.email=v45@example.invalid',
        'commit', '-qm', 'exact original fixture bytes')
    return git(repo, 'rev-parse', 'HEAD')


@dataclass
class Project:
    repo: Path
    base: str
    commit: str
    files: dict
    manifest: list
    contract: dict
    policy: dict
    authority: dict

    def candidate(self, path, replacement):
        return {'replacements': [{'path': path, 'original_sha256': sha(self.files[path]),
                                  'replacement': replacement}]}


def make_project(root, *, control=None, before=None, after=None, interpreter=MODERN, environment=None,
                 derive_authority=True):
    root.mkdir()
    repo = root / 'source'
    repo.mkdir()
    if control:
        shutil.copytree(ROOT / control / 'baseline', repo, dirs_exist_ok=True, copy_function=shutil.copy)
    else:
        for path, raw in before.items():
            target = repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
    git(repo, 'init', '-q')
    base = commit(repo)
    if control:
        shutil.copytree(ROOT / control / 'augmented', repo, dirs_exist_ok=True, copy_function=shutil.copy)
    else:
        for path, raw in after.items():
            target = repo / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
    augmented = commit(repo)
    identity, files, manifest = source.snapshot(repo, augmented)
    environment = environment or previous.environment_identity(str(interpreter))
    policy = {'schema': 'UDM_NATIVE_EXECUTION_POLICY_V45', 'collection_seconds': 20,
              'execution_seconds': 20, 'pytest_version': environment['pytest_version'], 'plugins': []}
    contract = {'schema': 'UDM_GENERIC_NATIVE_PYTEST_V45', 'repository': 'fixture/native-v45',
                'repo_path': str(repo), 'commit': augmented, **identity, 'interpreter': str(interpreter),
                'environment_sha256': previous.fingerprint(environment), 'protocol_binding': PROTOCOL,
                'horizon_seconds': 20, 'generated_build': None}
    authority = (implementation('native_admission_v45').derive_suite_contract(
        repo, base, augmented, PROTOCOL, repository=contract['repository']) if derive_authority else None)
    return Project(repo, base, augmented, files, manifest, contract, policy, authority)


@pytest.fixture(scope='session')
def modern_environment():
    assert MODERN.is_file(), 'exact original modern interpreter is required'
    result = previous.environment_identity(str(MODERN))
    assert result['pytest_version'] == '8.4.1'
    return result


@pytest.fixture
def project_factory(tmp_path, modern_environment):
    count = 0

    def make(**kwargs):
        nonlocal count
        count += 1
        if kwargs.get('interpreter', MODERN) == MODERN:
            kwargs['environment'] = modern_environment
        return make_project(tmp_path / ('control-' + str(count)), **kwargs)
    return make


def ordinary_case(factory, augmented, baseline=b'def test_contract():\n    assert True\n', extra=None):
    files = {'pytest.ini': b'[pytest]\naddopts = --import-mode=importlib\n',
             'tests/test_native.py': baseline, 'subject.py': b'def value():\n    return 0\n'}
    files.update(extra or {})
    return factory(before=files, after={'tests/test_native.py': augmented})


def collect_and_run(case, output, candidate=None):
    worker = implementation()
    certificate = worker.collect(case.contract, case.authority, output / 'collection', policy=case.policy)
    receipt = worker.verify(case.contract, candidate or {'replacements': []}, output / 'native',
                            authority=case.authority, admission_certificate=certificate, policy=case.policy)
    if receipt['status'] in ('PASS_NATIVE', 'FAIL_NATIVE'):
        record_evidence(output, output / 'collection/admission-certificate.json', output / 'native/receipt.json')
    return certificate, receipt


def record_evidence(output, certificate, receipt, replay=None):
    records = [{'role': role, 'path': str(path.absolute()), 'sha256': sha(path.read_bytes())}
               for role, path in [('certificate', certificate), ('receipt', receipt)]
               + ([('independent_reexecution', replay)] if replay is not None else [])]
    (output / 'V45_NATIVE_EVIDENCE.json').write_text(json.dumps({
        'schema': 'UDM_NATIVE_V45_TEST_EVIDENCE', 'records': records}, sort_keys=True) + '\n')


class _RetainedFixtureDirectory:
    """Keep original adversarial fixture artifacts for independent inspection."""
    def __init__(self, prefix):
        parent = os.environ.get('UDM_V45_CONTROL_EVIDENCE_ROOT')
        if parent:
            Path(parent).mkdir(parents=True, exist_ok=True)
        self.name = tempfile.mkdtemp(prefix=prefix, dir=parent)

    def cleanup(self):
        pass


def inherited_adversarial_suite():
    """Bind all original adversarial test statements to the actual V45 worker."""
    from . import test_native_admission_v2_adversarial as controls
    worker = implementation()
    realm = dict(vars(controls), execution=worker, admission=worker.admission, frozen=worker.original,
                 sys=types.SimpleNamespace(executable=str(MODERN)),
                 tempfile=types.SimpleNamespace(TemporaryDirectory=_RetainedFixtureDirectory))
    methods = {}
    for name, value in vars(controls.NativeAdmissionV2AdversarialTests).items():
        if isinstance(value, types.FunctionType):
            methods[name] = types.FunctionType(value.__code__, realm, value.__name__,
                                               value.__defaults__, value.__closure__)
    refresh = methods['refresh']

    def refresh_v45(self):
        refresh(self)
        self.contract.update(schema=worker.SCHEMA, generated_build=None)

    def setup_v45(cls):
        cls.environment = worker.environment_identity(str(MODERN))
        cls.policy = {'schema': worker.POLICY_SCHEMA, 'collection_seconds': 15,
                      'execution_seconds': 15, 'pytest_version': cls.environment['pytest_version'], 'plugins': []}
    methods.update(refresh=refresh_v45, setUpClass=classmethod(setup_v45), __module__=__name__)
    return type('TestNativeV45InheritedAdversarial', (unittest.TestCase,), methods)


def reseal_reports(evidence, transform):
    result = json.loads(json.dumps(evidence))
    for name in ('report.json', 'checked-report.json'):
        report = json.loads(base64_decode(result['packet'][name]))
        transform(report)
        raw = previous.canonical(report).encode()
        import base64
        result['packet'][name] = base64.b64encode(raw).decode()
        result['packet_sha256'][name] = sha(raw)
    if 'execution' in result:
        transform(result['execution'])
    elif 'collection' in result:
        transform(result['collection'])
    return result


def base64_decode(value):
    import base64
    return base64.b64decode(value)
