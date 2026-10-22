"""Frozen V44 infrastructure controls; no prospective scientific task or win.

Wheel bytes in parser controls are hostile data, never successful native evidence.
Successful observations in integration controls must come from real original
backend execution plus a separate fresh independent rebuild.
"""
from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

import pytest

ROOT = Path('/workspace/udm-v54')
FIXTURE = Path(__file__).parent / 'original_backend_fixture'
MODULE = 'research.unified_consequence_runtime.native_metadata_v44'
SELECTOR = 'research.unified_consequence_runtime.native_environment_selection_v44'


def metadata_module():
    assert importlib.util.find_spec(MODULE), 'V44 source-native metadata operation not implemented'
    return importlib.import_module(MODULE)


def selector_module():
    assert importlib.util.find_spec(SELECTOR), 'V44 source-native metadata selection not implemented'
    return importlib.import_module(SELECTOR)


def wheel(tmp_path, raw, *, extra=(), name='fixture-1.0.0.dist-info/METADATA', mode=0o100644):
    path = tmp_path / 'fixture-1.0.0-py3-none-any.whl'
    with zipfile.ZipFile(path, 'w') as archive:
        info = zipfile.ZipInfo(name)
        info.external_attr = mode << 16
        archive.writestr(info, raw)
        for other, data in extra:
            archive.writestr(other, data)
    return path


VALID = b'Metadata-Version: 2.1\nName: fixture\nVersion: 1.0.0\nRequires-Python: >=3.10\nRequires-Dist: attrs>=24\nRequires-Dist: pytest>=7; extra == "test"\nProvides-Extra: test\nClassifier: Programming Language :: Python :: 3\n\nDescription is not authority: Requires-Python: <1\n'


def test_strict_parser_preserves_declared_fields_and_ignores_description_body(tmp_path):
    value = metadata_module().parse_wheel_metadata(wheel(tmp_path, VALID))
    assert value['name'] == 'fixture'
    assert value['version'] == '1.0.0'
    assert value['requires_python'] == '>=3.10'
    assert value['requires_dist'] == ['attrs>=24', 'pytest>=7; extra == "test"']
    assert value['provides_extra'] == ['test']
    assert value['classifiers'] == ['Programming Language :: Python :: 3']


@pytest.mark.parametrize('raw', [
    b'\xff\xfeinvalid',
    VALID.replace(b'Name: fixture\n', b''),
    VALID.replace(b'Version: 1.0.0\n', b''),
    VALID.replace(b'Metadata-Version: 2.1\n', b''),
    VALID.replace(b'Name: fixture\n', b'Name: fixture\nName: forged\n'),
    VALID.replace(b'Version: 1.0.0\n', b'Version: 1.0.0\nVersion: 2.0.0\n'),
    VALID.replace(b'Requires-Python: >=3.10\n', b'Requires-Python: >=3.10\nRequires-Python: <2\n'),
    VALID.replace(b'Requires-Python: >=3.10\n', b'Requires-Python: not-a-specifier\n'),
    VALID.replace(b'Requires-Dist: attrs>=24\n', b'Requires-Dist: attrs=>24\n'),
    VALID.replace(b'Requires-Dist: attrs>=24\n', b'Requires-Dist: attrs @ https://example.invalid/wheel.whl\n'),
    VALID.replace(b'Provides-Extra: test\n', b'Provides-Extra: ../../outside\n'),
    b'Not a core metadata header\n\n' + VALID,
])
def test_malformed_or_conflicting_metadata_never_becomes_observed_authority(tmp_path, raw):
    with pytest.raises((ValueError, RuntimeError)):
        metadata_module().parse_wheel_metadata(wheel(tmp_path, raw))


@pytest.mark.parametrize('name,extra,mode', [
    ('package/METADATA', (), 0o100644),
    ('fixture-1.0.0.dist-info/METADATA', [('other-1.0.0.dist-info/METADATA', VALID)], 0o100644),
    ('fixture-1.0.0.dist-info/METADATA', [('fixture-1.0.0.dist-info/METADATA', VALID)], 0o100644),
    ('fixture-1.0.0.dist-info/METADATA', [('../outside', b'x')], 0o100644),
    ('fixture-1.0.0.dist-info/METADATA', [('/absolute', b'x')], 0o100644),
    ('fixture-1.0.0.dist-info/METADATA', (), 0o120777),
])
def test_metadata_archive_identity_is_unambiguous_and_regular(tmp_path, name, extra, mode):
    with pytest.raises((ValueError, RuntimeError)):
        metadata_module().parse_wheel_metadata(wheel(tmp_path, VALID, name=name, extra=extra, mode=mode))


def git(repo, *argv):
    return subprocess.check_output(['git', '--no-optional-locks', '-C', str(repo), *argv],
        env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'), text=True).strip()


def make_repo(tmp_path, *, modifications=None):
    repo = tmp_path / 'source'
    shutil.copytree(FIXTURE, repo)
    for name, raw in (modifications or {}).items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    subprocess.check_call(['git', 'init', '-q', str(repo)], env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
    git(repo, '-c', 'core.fsmonitor=false', 'add', '.')
    git(repo, '-c', 'user.name=V44 Frozen Infrastructure', '-c', 'user.email=fixture@example.invalid', 'commit', '-q', '-m', 'Frozen original backend fixture')
    commit = git(repo, 'rev-parse', 'HEAD')
    from research.unified_consequence_runtime.decisive_native_verify import _snapshot
    return repo, commit, _snapshot(repo, commit)


def environment_sha():
    from research.unified_consequence_runtime.decisive_native_verify import environment_identity, fingerprint
    return fingerprint(environment_identity(sys.executable))


def genuine_observation(tmp_path, *, modifications=None):
    module = metadata_module()
    repo, commit, snapshot = make_repo(tmp_path, modifications=modifications)
    env = environment_sha()
    evidence = module.observe(repo, commit, sys.executable, tmp_path / 'observed', environment_sha256=env, timeout=90)
    assert isinstance(evidence, dict), 'Build receipt must retain executable evidence, never boolean success'
    observation = module.verify(repo, commit, sys.executable, evidence, tmp_path / 'independent', environment_sha256=env, timeout=90)
    checked = module.validate_observation(repo, commit, sys.executable, observation, environment_sha256=env)
    return module, repo, commit, snapshot, env, evidence, observation, checked


def test_real_original_backend_metadata_is_independently_rebuilt_before_use(tmp_path):
    module, repo, commit, snapshot, env, evidence, observation, checked = genuine_observation(tmp_path)
    assert checked['requires_python'] == '>=3.10'
    assert checked['provides_extra'] == ['test']
    assert checked['requires_dist'] == ["pytest>=7; extra == 'test'"]
    assert list((tmp_path / 'observed').rglob('*.whl'))
    assert list((tmp_path / 'independent').rglob('*.whl')), 'Actual independent original-backend build required'
    from research.unified_consequence_runtime.decisive_native_verify import _snapshot
    assert _snapshot(repo, commit) == snapshot
    assert git(repo, 'status', '--porcelain=v1') == ''
    assert 'PASS_NATIVE' not in json.dumps(observation), 'Metadata authority cannot self-promote to native warrant'


def test_dirty_worktree_does_not_replace_exact_original_backend_source(tmp_path):
    module, repo, commit, snapshot, env, evidence, observation, checked = genuine_observation(tmp_path)
    metadata_path = repo / 'source-metadata.json'
    metadata_path.write_bytes(b'dirty host bytes must not become source metadata\n')
    assert module.validate_observation(repo, commit, sys.executable, observation, environment_sha256=env) == checked
    assert metadata_path.read_bytes() == b'dirty host bytes must not become source metadata\n'


@pytest.mark.parametrize('field', ['source', 'environment', 'missing-independent-wheel', 'altered-independent-wheel'])
def test_retained_observation_rejects_wrong_input_or_missing_independent_evidence(tmp_path, field):
    module, repo, commit, snapshot, env, evidence, observation, checked = genuine_observation(tmp_path)
    supplied_commit, supplied_env = commit, env
    if field == 'source':
        supplied_commit = '0' * 40
    elif field == 'environment':
        supplied_env = '0' * 64
    else:
        independent = next((tmp_path / 'independent').rglob('*.whl'))
        if field == 'missing-independent-wheel':
            independent.unlink()
        else:
            independent.write_bytes(independent.read_bytes() + b'forged trailing bytes')
    with pytest.raises((ValueError, RuntimeError, OSError)):
        module.validate_observation(repo, supplied_commit, sys.executable, observation, environment_sha256=supplied_env)


def catalog():
    pytest_version = importlib.metadata.version('pytest')
    return {'schema': 'UDM_NATIVE_ENVIRONMENT_CATALOG_V3', 'profiles': [{
        'id': 'frozen-original-fixture-profile', 'python_version': '.'.join(map(str, sys.version_info[:3])),
        'python_implementation': 'CPython', 'pytest_version': pytest_version,
        'packages': ['pytest==' + pytest_version], 'plugins': []}]}


def test_verified_source_native_observation_resolves_declared_dynamic_fields(tmp_path):
    module, repo, commit, snapshot, env, evidence, observation, checked = genuine_observation(tmp_path)
    selector = selector_module()
    files = snapshot[1]
    cold = selector.select_profile(files, catalog())
    assert cold['status'] == 'UNKNOWN'
    assert cold['reason'] == 'UNKNOWN_DYNAMIC_METADATA'
    warm = selector.select_profile(files, catalog(), observation=observation)
    assert warm['status'] == 'CANDIDATE_SOURCE_ENVIRONMENT'
    selector.validate_selection(files, catalog(), warm, observation=observation)
    assert warm['selected_profile']['id'] == 'frozen-original-fixture-profile'


def test_observation_cannot_silently_replace_static_test_requirements(tmp_path):
    base = (FIXTURE / 'pyproject.toml').read_bytes()
    module, repo, commit, snapshot, env, evidence, observation, checked = genuine_observation(tmp_path,
        modifications={'pyproject.toml': base + b'\n[dependency-groups]\ntest = ["pytest<1"]\n'})
    value = selector_module().select_profile(snapshot[1], catalog(), observation=observation)
    assert value['status'] == 'UNKNOWN'
    assert 'pytest' in json.dumps(value)


def test_observation_for_different_source_cannot_be_used_by_selector(tmp_path):
    module, repo, commit, snapshot, env, evidence, observation, checked = genuine_observation(tmp_path)
    wrong = dict(snapshot[1])
    wrong['source-metadata.json'] = b'{"requires_python": "<2"}\n'
    with pytest.raises((ValueError, RuntimeError)):
        selector_module().select_profile(wrong, catalog(), observation=observation)


def test_setup_py_does_not_gain_override_authority_from_wheel_metadata(tmp_path):
    module, repo, commit, snapshot, env, evidence, observation, checked = genuine_observation(tmp_path,
        modifications={'setup.py': b'from setuptools import setup\nsetup(tests_require=arbitrary_dynamic_call())\n'})
    value = selector_module().select_profile(snapshot[1], catalog(), observation=observation)
    assert value['status'] == 'UNKNOWN'
    assert 'UNKNOWN' in json.dumps(value)


def test_malformed_python_fixture_data_is_inventory_not_executable_compatibility(tmp_path):
    module, repo, commit, snapshot, env, evidence, observation, checked = genuine_observation(tmp_path,
        modifications={'fixtures/intentional_bad_syntax.py': b'if = intentional fixture data\n'})
    assert selector_module().select_profile(snapshot[1], catalog(), observation=observation)['status'] == 'CANDIDATE_SOURCE_ENVIRONMENT'
