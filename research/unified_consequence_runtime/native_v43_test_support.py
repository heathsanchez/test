"""Disposable V43 acceptance infrastructure; never a prospective source task.

The oracle is the installed, original Hatch VCS backend. No fake backend,
installed fixture distribution, generated native oracle, or package download is
used. Git mutations are confined to disposable directories outside this tree.
"""
from __future__ import annotations

import base64
import copy
import csv
from dataclasses import dataclass
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import zipfile

import pytest

from . import decisive_native_verify as original
from . import native_admission_v42 as admission
from . import native_execution_v42 as previous
from . import native_source_v42 as source
from .generated_overlay_gate import wheel_content_digest


MODERN_PYTHON = Path('/workspace/qualification/native-authority-v41-profile-preparation/'
                     'modern-runtime-final/venv/bin/python')
CONTRACT_SCHEMA = 'UDM_GENERIC_NATIVE_PYTEST_V43'
POLICY_SCHEMA = 'UDM_NATIVE_EXECUTION_POLICY_V43'
CERTIFICATE_SCHEMA = 'UDM_NATIVE_ADMISSION_CERTIFICATE_V43'
PROTOCOL = hashlib.sha256(b'V43 fixture infrastructure, no prospective science').hexdigest()


def implementation(name):
    """Deliberately lazy: missing implementations fail each behavior, never skip."""
    return importlib.import_module(__package__ + '.' + name)


def clean_environment():
    env = dict(os.environ, GIT_OPTIONAL_LOCKS='0', PYTHONDONTWRITEBYTECODE='1',
               PIP_DISABLE_PIP_VERSION_CHECK='1')
    for key in list(env):
        if key.startswith(('SETUPTOOLS_SCM_', 'HATCH_', 'PYTEST_')) or key == 'PYTHONPATH':
            env.pop(key)
    return env


def git(repo, *args):
    return subprocess.check_output(
        ['git', '--no-replace-objects', '-C', str(repo), *args],
        env=clean_environment(), stderr=subprocess.PIPE, text=True).strip()


def commit(repo, message):
    git(repo, 'add', '.')
    git(repo, '-c', 'user.name=V43 Acceptance Fixture',
        '-c', 'user.email=v43-fixture@example.invalid', 'commit', '-qm', message)
    return git(repo, 'rev-parse', 'HEAD')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def objects(value):
    yield value
    if isinstance(value, dict):
        for child in value.values():
            yield from objects(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from objects(child)


def replace_values(value, replacements):
    if isinstance(value, dict):
        return {key: replace_values(child, replacements) for key, child in value.items()}
    if isinstance(value, list):
        return [replace_values(child, replacements) for child in value]
    if isinstance(value, tuple):
        return tuple(replace_values(child, replacements) for child in value)
    return replacements.get(value, value) if isinstance(value, (str, int, float)) else value


def wheel_artifact(evidence):
    paths = {Path(value) for value in objects(evidence)
             if isinstance(value, str) and value.endswith('.whl') and Path(value).is_absolute()}
    assert len(paths) == 1, 'build evidence must identify exactly one retained wheel artifact'
    return paths.pop()


def wheel_members(wheel):
    with zipfile.ZipFile(wheel) as archive:
        return {name: archive.read(name) for name in archive.namelist() if not name.endswith('/')}


def normalized_digest(members):
    return original.fingerprint({name: sha(raw) for name, raw in sorted(members.items())})


def rehash_record(members):
    records = [name for name in members if name.endswith('.dist-info/RECORD')]
    assert len(records) == 1
    output = io.StringIO(newline='')
    writer = csv.writer(output, lineterminator='\n')
    for name, raw in sorted(members.items()):
        if name == records[0]:
            continue
        digest = base64.urlsafe_b64encode(hashlib.sha256(raw).digest()).rstrip(b'=').decode()
        writer.writerow([name, 'sha256=' + digest, len(raw)])
    writer.writerow([records[0], '', ''])
    members[records[0]] = output.getvalue().encode()
    return members


def forged_wheel(evidence, destination, updates, *, extra_members=(), symlinks=()):
    """Change actual ZIP bytes and all supplied artifact/member/hash bindings.

    Digest consistency is transport integrity, not independent build authority.
    The original wheel location is not changed; each control has its own copy.
    """
    original_wheel = wheel_artifact(evidence)
    old_members = wheel_members(original_wheel)
    members = rehash_record(dict(old_members, **updates))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, 'w') as archive:
        for name, raw in sorted(members.items()):
            info = zipfile.ZipInfo(name)
            info.external_attr = ((stat.S_IFLNK if name in symlinks else stat.S_IFREG) | 0o644) << 16
            archive.writestr(info, raw)
        for name, raw in extra_members:
            archive.writestr(name, raw)
    replacements = {
        str(original_wheel): str(destination),
        sha(original_wheel.read_bytes()): sha(destination.read_bytes()),
        normalized_digest(old_members): normalized_digest(wheel_members(destination)),
    }
    for name in old_members.keys() & members.keys():
        if old_members[name] != members[name]:
            replacements[sha(old_members[name])] = sha(members[name])
    # Rebind any producer-supplied nested object fingerprints too. This does
    # not forge signatures or trusted authority; the independent build must
    # still reject a caller's internally consistent artifact claims.
    for item in reversed(list(objects(evidence))):
        if isinstance(item, (dict, list)):
            changed = replace_values(item, replacements)
            if changed != item:
                replacements[original.fingerprint(item)] = original.fingerprint(changed)
    return replace_values(copy.deepcopy(evidence), replacements)


def charged_build_calls(receipt):
    values = [item['build_calls'] for item in objects(receipt)
              if isinstance(item, dict) and 'build_calls' in item]
    assert values, 'independent verification must retain actual charged build calls'
    assert all(type(value) is int and value >= 0 for value in values)
    return max(values)


def assert_no_native_success(value):
    assert not any(item in ('PASS_NATIVE', 'FAIL_NATIVE', 'ADMITTED_NATIVE_COLLECTION')
                   for item in objects(value) if isinstance(item, str)), value


@dataclass
class Project:
    root: Path
    repo: Path
    package: str
    base: str
    augmented: str
    environment: dict
    policy: dict
    contract: dict
    authority: dict
    files: dict
    manifest: list

    @property
    def generated_path(self):
        return 'src/' + self.package + '/_version.py'

    @property
    def wheel_generated_path(self):
        return self.package + '/_version.py'

    @property
    def nodes(self):
        return ['tests/test_native.py::test_existing', 'tests/test_native.py::test_protected']

    def candidate(self, value=1):
        name = 'src/' + self.package + '/subject.py'
        return {'replacements': [{'path': name, 'original_sha256': sha(self.files[name]),
                                  'replacement': 'def value():\n    return ' + str(value) + '\n'}]}

    def with_evidence(self, evidence):
        return dict(self.contract, generated_build=evidence)

    def inventory(self):
        return source.snapshot(self.repo, self.augmented)


def make_project(root, flavor, environment, *, expected=0, generated=True,
                 declared=None, extra_files=None, aliases=None, test_tail=''):
    root.mkdir(parents=True)
    repo = root / 'source'
    repo.mkdir()
    package = 'native_' + flavor + '_v43'
    (repo / 'src' / package).mkdir(parents=True)
    (repo / 'tests').mkdir()
    version_file = declared or 'src/' + package + '/_version.py'
    pyproject = (
        '[build-system]\nrequires = ["hatchling==1.27.0", "hatch-vcs==0.5.0"]\n'
        'build-backend = "hatchling.build"\n\n'
        '[project]\nname = "native-' + flavor + '-v43"\ndynamic = ["version"]\n'
        'requires-python = ">=3.12"\n\n'
        '[tool.hatch.version]\nsource = "vcs"\n\n'
        '[tool.hatch.build.hooks.vcs]\nversion-file = ' + json.dumps(version_file) + '\n\n'
        '[tool.hatch.build.targets.wheel]\npackages = ["src/' + package + '"]\n\n'
        '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n'
        'addopts = "--import-mode=importlib"\n'
    )
    (repo / 'pyproject.toml').write_text(pyproject)
    init = ('from ._version import __version__\n' if generated else '')
    (repo / 'src' / package / '__init__.py').write_text(
        init + 'from .subject import value\nFLAVOR = ' + repr(flavor) + '\n')
    (repo / 'src' / package / 'subject.py').write_text('def value():\n    return 0\n')
    old = ('from ' + package + ' import __version__, value\n'
           'def test_existing():\n    assert __version__ == "1.0.0"\n') if generated else (
           'from ' + package + ' import value\n'
           'def test_existing():\n    assert isinstance(value(), int)\n')
    test = repo / 'tests/test_native.py'
    test.write_text(old)
    for name, raw in (extra_files or {}).items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    for name, target in (aliases or {}).items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.symlink_to(target)
    git(repo, 'init', '-q')
    base = commit(repo, 'original ' + flavor + ' fixture source')
    git(repo, 'tag', 'v1.0.0', base)
    test.write_text(old + '\ndef test_protected():\n    assert value() == ' + str(expected) + '\n' + test_tail)
    augmented = commit(repo, 'author assertion augmentation only')
    identity, files, manifest = source.snapshot(repo, augmented)
    policy = {'schema': POLICY_SCHEMA, 'collection_seconds': 20, 'execution_seconds': 20,
              'pytest_version': environment['pytest_version'], 'plugins': []}
    contract = {'schema': CONTRACT_SCHEMA, 'repository': 'fixture/native-' + flavor + '-v43',
                'repo_path': str(repo), 'commit': augmented, **identity,
                'interpreter': str(MODERN_PYTHON), 'environment_sha256': original.fingerprint(environment),
                'protocol_binding': PROTOCOL, 'horizon_seconds': policy['execution_seconds'],
                'generated_build': None}
    authority = admission.derive_suite_contract(repo, base, augmented, PROTOCOL,
                                                 repository=contract['repository'])
    return Project(root, repo, package, base, augmented, environment, policy,
                   contract, authority, files, manifest)


@pytest.fixture(scope='session')
def modern_environment():
    assert MODERN_PYTHON.is_file(), 'the frozen independently prepared modern interpreter is required'
    environment = previous.environment_identity(str(MODERN_PYTHON))
    assert environment['pytest_version'] == '8.4.1'
    return environment


@pytest.fixture
def project_factory(tmp_path, modern_environment):
    counter = 0

    def make(flavor='alpha', **kwargs):
        nonlocal counter
        counter += 1
        return make_project(tmp_path / ('fixture-' + str(counter)), flavor, modern_environment, **kwargs)
    return make


@pytest.fixture(params=('alpha', 'beta'))
def project(request, project_factory):
    return project_factory(request.param)


def original_backend_build(project, output, *, commit_id=None):
    """Independent oracle: original pip command on an exact tagged Git clone."""
    output.mkdir()
    checkout = output / 'source'
    git(output, 'clone', '--quiet', '--no-local', '--no-hardlinks', str(project.repo), str(checkout))
    git(checkout, 'checkout', '--quiet', '--detach', commit_id or project.base)
    before = source.snapshot(checkout, commit_id or project.base)
    wheels = output / 'wheels'
    wheels.mkdir()
    argv = [str(MODERN_PYTHON), '-I', '-B', '-m', 'pip', '--isolated', 'wheel',
            '--use-pep517', '--no-deps', '--no-build-isolation', '--no-index', '--no-cache-dir',
            '--wheel-dir', str(wheels), str(checkout)]
    result = subprocess.run(argv, env=clean_environment(), capture_output=True, text=True, timeout=90)
    (output / 'stdout.log').write_text(result.stdout)
    (output / 'stderr.log').write_text(result.stderr)
    assert result.returncode == 0, result.stdout + result.stderr
    found = list(wheels.glob('*.whl'))
    assert len(found) == 1
    assert source.snapshot(checkout, commit_id or project.base) == before
    assert (checkout / project.generated_path).is_file()
    return found[0]


def mutate_packet_import_hash(receipt, path):
    """Keep raw reports, checked reports, and supplied packet hashes consistent."""
    changed = copy.deepcopy(receipt)
    for row in changed['execution']['import_manifest']:
        if row['path'] == path:
            row['sha256'] = '0' * 64
    for name in ('report.json', 'checked-report.json'):
        report = json.loads(base64.b64decode(changed['packet'][name]))
        for row in report['import_manifest']:
            if row['path'] == path:
                row['sha256'] = '0' * 64
        raw = original.canonical(report).encode()
        changed['packet'][name] = base64.b64encode(raw).decode()
        changed['packet_sha256'][name] = sha(raw)
    return changed
