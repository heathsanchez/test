"""Source-preserving environment preparation for externally licensed native v2.

This transports base production and independent author tests, never repaired
production. Setup grants neither collection authority nor native success.
"""
from __future__ import annotations

import base64
from email.parser import BytesParser
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import time
import tomllib
from urllib.parse import quote
import zipfile

from .decisive_task_admission import _validate_spec, _commit_overlay, overlay_author_tests
from .decisive_native_verify import _path, _snapshot, canonical, environment_identity, fingerprint, sha256
from .qualify_recursive_frontier import _command
from .native_admission_v2 import derive_suite_contract
from . import native_execution_v2 as execution


def tracked_archive(files, manifest):
    """Archive raw Git blob bytes without export-subst or host metadata."""
    if not isinstance(files, dict) or not isinstance(manifest, list):
        raise ValueError('tracked bytes and manifest required')
    rows = {}
    for row in manifest:
        if not isinstance(row, dict):
            raise ValueError('invalid tracked manifest row')
        name = row.get('path')
        if not _path(name).parts:
            raise ValueError('empty tracked source path')
        if name in rows or row.get('mode') not in ('100644', '100755'):
            raise ValueError('duplicate or nonregular tracked entry')
        rows[name] = row
    if set(rows) != set(files):
        raise ValueError('tracked archive manifest differs')
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode='w', format=tarfile.PAX_FORMAT) as archive:
        for name in sorted(files):
            _path(name); raw = files[name]
            if not isinstance(raw, bytes) or rows[name].get('sha256') != sha256(raw):
                raise ValueError('tracked archive digest differs')
            entry = tarfile.TarInfo(name)
            entry.size = len(raw); entry.mode = int(rows[name]['mode'], 8) & 0o777
            entry.uid = entry.gid = entry.mtime = 0
            entry.uname = entry.gname = ''
            archive.addfile(entry, io.BytesIO(raw))
    return gzip.compress(stream.getvalue(), mtime=0)


def ancestor_tag_refs(raw_ls_remote, ancestors):
    """Select only tags whose peeled commit is already proven base ancestry."""
    if not isinstance(raw_ls_remote, str) or not isinstance(ancestors, set) or any(
            not isinstance(x, str) or not re.fullmatch('[0-9a-f]{40}', x) for x in ancestors):
        raise ValueError('exact tag metadata and base ancestor set required')
    refs = {}
    for line in raw_ls_remote.splitlines():
        if not line:
            continue
        parts = line.split('\t')
        if len(parts) != 2 or not re.fullmatch('[0-9a-f]{40}', parts[0]):
            raise ValueError('malformed remote tag metadata')
        oid, ref = parts
        plain = ref[:-3] if ref.endswith('^{}') else ref
        if (not re.fullmatch(r'refs/tags/[A-Za-z0-9_+./()-]+', plain)
                or '..' in plain or '//' in plain or plain.endswith(('/', '.'))
                or any(part.startswith('.') or part.endswith('.lock') for part in plain.split('/'))
                or ref in refs):
            raise ValueError('unsafe or duplicate tag reference')
        refs[ref] = oid
    if any(ref[:-3] not in refs for ref in refs if ref.endswith('^{}')):
        raise ValueError('peeled tag lacks independent tag reference')
    result = []
    for ref in sorted(refs):
        if ref.endswith('^{}'):
            continue
        target = refs.get(ref + '^{}', refs[ref])
        if target in ancestors:
            result.append({'ref': ref, 'tag_object': refs[ref], 'target': target})
    return result


def _normalize(name):
    return re.sub('[-_.]+', '-', name).lower()


def _version(value):
    # Deliberately support a finite ordinary PEP 440 spelling grammar. Pip must
    # not discover malformed external authority after source transport starts.
    return isinstance(value, str) and re.fullmatch(
        r'(?:[0-9]+!)?[0-9]+(?:\.[0-9]+)*(?:(?:a|b|rc)[0-9]+)?'
        r'(?:\.post[0-9]+)?(?:\.dev[0-9]+)?(?:\+[a-z0-9]+(?:[.-][a-z0-9]+)*)?',
        value, re.IGNORECASE) is not None


def _validate_inputs(policy, packages):
    if not isinstance(packages, (list, tuple)) or not packages:
        raise ValueError('nonempty externally fixed package pins required')
    pins = {}
    for pin in packages:
        if not isinstance(pin, str) or pin.count('==') != 1:
            raise ValueError('exact external package pins required')
        name, version = pin.split('==')
        if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?', name) or not _version(version):
            raise ValueError('exact external package pins required')
        name = _normalize(name)
        if name in pins:
            raise ValueError('duplicate external package pin')
        pins[name] = version
    if (not isinstance(policy, dict) or set(policy) != {
            'schema', 'collection_seconds', 'execution_seconds', 'pytest_version', 'plugins'}
            or policy['schema'] != execution.POLICY_SCHEMA
            or any(type(policy[k]) is not int or not 1 <= policy[k] <= 600
                   for k in ('collection_seconds', 'execution_seconds'))
            or not _version(policy['pytest_version'])
            or pins.get('pytest') != policy['pytest_version']
            or not isinstance(policy['plugins'], list)):
        raise ValueError('externally fixed native policy and pytest pin required')
    modules = set()
    for row in policy['plugins']:
        if (not isinstance(row, dict) or set(row) != {'module', 'distribution', 'version'}
                or any(not isinstance(x, str) for x in row.values())
                or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*', row['module'])
                or not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9_.-]*[A-Za-z0-9])?', row['distribution'])
                or not _version(row['version'])
                or pins.get(_normalize(row['distribution'])) != row['version']
                or row['module'] in modules):
            raise ValueError('explicitly pinned independent plugin license required')
        modules.add(row['module'])


def _git_scm(files):
    data = tomllib.loads(files.get('pyproject.toml', b'').decode())
    build = data.get('build-system', {})
    if (not isinstance(build, dict) or not isinstance(build.get('requires', []), list)
            or any(not isinstance(value, str) for value in build.get('requires', []))
            or not isinstance(build.get('build-backend', ''), str)):
        raise ValueError('invalid original build-system configuration')
    requirements = {_normalize(re.split(r'[\s<>=!~\[]', value, 1)[0])
                    for value in build.get('requires', [])}
    backend = build.get('build-backend', '')
    if 'hatch-vcs' in requirements:
        if backend != 'hatchling.build':
            raise ValueError('unsupported declared Git SCM build backend')
        return 'hatch-vcs'
    if 'setuptools-scm' in requirements:
        if backend not in ('setuptools.build_meta', 'setuptools.build_meta:__legacy__'):
            raise ValueError('unsupported declared Git SCM build backend')
        return 'setuptools-scm'
    return None


def provision(spec, root, protocol_binding, *, policy, packages):
    """Prepare exact original bytes and an independently specified environment.

    ``packages`` is the complete pinned dependency closure, including build
    dependencies. Pip never adds undeclared dependencies. The caller owns all
    plugin and time licenses; this function does not derive or widen them.
    """
    _validate_inputs(policy, packages)
    repository, base, head, test_paths = _validate_spec(spec)
    if not isinstance(protocol_binding, str) or not re.fullmatch('[0-9a-f]{64}', protocol_binding):
        raise ValueError('exact frozen protocol binding required')
    root = Path(root).absolute()
    if root.resolve() != root or root.exists():
        raise ValueError('new canonical provisioning directory required')
    if any(name.startswith('SETUPTOOLS_SCM_PRETEND_') for name in os.environ):
        raise ValueError('synthetic SCM versions are not source authority')
    started = time.monotonic(); root.mkdir(parents=True)
    repo = root / 'source'; venv = root / 'venv'; build = root / 'base-build'
    remote = 'https://github.com/' + repository + '.git'
    costs = []; boundaries = {}; authority = None; contract = None
    frozen_policy = json.loads(canonical(policy))
    policy = frozen_policy

    def command(argv, phase, timeout=240):
        result = _command(argv, root / (phase + '.log'), timeout=timeout)
        costs.append({'phase': phase, 'argv': [str(x) for x in argv], **result})
        if result['status'] != 'PASS':
            raise RuntimeError('UNKNOWN_SETUP:' + phase)
        return root / (phase + '.log')

    def save(status, reason=None):
        value = {'status': status, 'contract': contract, 'authority': authority,
                 'native_suite_authority': authority, 'policy': frozen_policy,
                 'costs': costs, 'source_boundaries': boundaries,
                 'total_wall_seconds': time.monotonic() - started}
        if reason is not None:
            value['reason'] = reason
        (root / 'admission.json').write_text(canonical(value) + '\n')
        return value

    def archive(name, files, manifest):
        raw = tracked_archive(files, manifest); path = root / name; path.write_bytes(raw)
        return {'path': str(path), 'sha256': sha256(raw), 'bytes': len(raw),
                'format': 'RAW_TRACKED_BYTES_TAR_GZIP_V2', 'export_subst': False}

    try:
        command(['git', 'init', '-q', repo], 'git-init')
        command(['git', '-C', repo, 'fetch', '--depth=1', '--no-tags', remote, base], 'base-fetch')
        command(['git', '-C', repo, '-c', 'core.autocrlf=false', 'checkout', '-q', '--detach', base], 'base-checkout')
        base_identity, base_files, base_manifest = _snapshot(repo, base)
        boundaries.update(repository=repository, base_commit=base, author_test_head_commit=head,
            base_identity=base_identity, base_manifest=base_manifest,
            base_source_archive=archive('base-source.tar.gz', base_files, base_manifest),
            head_production_fetched=False, author_tests=[], production_preserved=False)
        scm = _git_scm(base_files)
        if scm is not None:
            command(['git', '-C', repo, 'fetch', '--unshallow', '--no-tags', remote, base], 'base-ancestry-fetch')
            ancestors_path = command(['git', '-C', repo, 'rev-list', base], 'base-ancestor-commits')
            metadata_path = command(['git', 'ls-remote', '--tags', remote], 'remote-tag-metadata')
            selected = ancestor_tag_refs(metadata_path.read_text(), set(ancestors_path.read_text().splitlines()))
            if selected:
                command(['git', '-C', repo, 'fetch', '--no-tags', remote,
                         *[row['tag_object'] + ':' + row['ref'] for row in selected]], 'ancestor-tags-fetch')
                for index, row in enumerate(selected):
                    # Fetch immutable OIDs: a remote tag-name race must never
                    # transport a new target before a subsequent check rejects it.
                    tag_object = command(['git', '-C', repo, 'rev-parse', row['ref']],
                                         'tag-object-' + str(index)).read_text().strip()
                    target = command(['git', '-C', repo, 'rev-parse', row['ref'] + '^{}'],
                                     'tag-target-' + str(index)).read_text().strip()
                    if tag_object != row['tag_object'] or target != row['target']:
                        raise ValueError('ancestor tag target changed during transport')
            final_identity, final_files, _ = _snapshot(repo, base)
            if final_identity != base_identity or final_files != base_files:
                raise ValueError('SCM metadata transport changed base source')
            boundaries['scm_metadata'] = {'backend': scm, 'base_ancestry_only': True,
                'ancestor_commits_sha256': sha256(ancestors_path.read_bytes()),
                'remote_tag_metadata_sha256': sha256(metadata_path.read_bytes()),
                'ancestor_tags': selected, 'tracked_source_preserved': True}
            (root / 'scm-provenance.json').write_text(canonical(boundaries['scm_metadata']) + '\n')
        author_tests = {}
        for index, name in enumerate(test_paths):
            endpoint = f'repos/{repository}/contents/{quote(name, safe="/")}?ref={head}'
            response_path = command(['gh', 'api', endpoint], 'author-test-' + str(index))
            response = json.loads(response_path.read_text())
            if (response.get('path') != name or response.get('type') != 'file'
                    or response.get('encoding') != 'base64'):
                raise ValueError('UNKNOWN_INTERFACE: exact author-test transport required')
            raw = base64.b64decode(response['content'], validate=False)
            blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
            if blob != response.get('sha') or len(raw) != response.get('size'):
                raise ValueError('author-test transport digest mismatch')
            author_tests[name] = raw
            boundaries['author_tests'].append({'path': name, 'sha256': sha256(raw),
                'git_blob': blob, 'bytes': len(raw), 'endpoint': endpoint,
                'transport_json': str(response_path), 'transport_sha256': sha256(response_path.read_bytes())})
        commit = _commit_overlay(repo, base, author_tests)
        identity, augmented_files, manifest = _snapshot(repo, commit)
        if augmented_files != overlay_author_tests(base_files, author_tests):
            raise ValueError('author overlay changed original production')
        boundaries.update(augmented_commit=commit, augmented_identity=identity, augmented_manifest=manifest,
            production_preserved=True, contract_source_archive=archive('contract-source.tar.gz', augmented_files, manifest))
        (root / 'source-boundaries.json').write_text(canonical(boundaries) + '\n')
        authority_started = time.monotonic()
        try:
            authority = derive_suite_contract(repo, base, commit, protocol_binding, repository=repository)
        except ValueError as error:
            costs.append({'phase': 'native-suite-authority', 'status': 'UNKNOWN_CONTRACT',
                          'seconds': time.monotonic() - authority_started})
            return save('UNKNOWN_CONTRACT', str(error))
        costs.append({'phase': 'native-suite-authority', 'status': 'PASS',
                      'seconds': time.monotonic() - authority_started})
        (root / 'native-suite-authority.json').write_text(canonical(authority) + '\n')
        if not set(authority['configuration']['plugin_requirements']) <= {row['module'] for row in policy['plugins']}:
            return save('UNKNOWN_CONTRACT', 'original native configuration lacks independent plugin license')
        command([sys.executable, '-m', 'venv', venv], 'venv')
        python = venv / 'bin/python'
        command([python, '-m', 'pip', 'install', '--disable-pip-version-check', '--no-input', '--no-deps', *packages], 'fixed-packages')
        command(['git', 'clone', '--local', '--no-hardlinks', '--no-checkout', repo, build], 'base-build-clone')
        command(['git', '-C', build, '-c', 'core.autocrlf=false', 'checkout', '-q', '--detach', base], 'base-build-checkout')
        # Explicitly materialize raw blobs even if the original attributes specify checkout transformations.
        for row in base_manifest:
            destination = build / row['path']; destination.write_bytes(base_files[row['path']])
            destination.chmod(int(row['mode'], 8) & 0o777)
        wheels = root / 'wheels'; wheels.mkdir()
        command([python, '-m', 'pip', 'wheel', '--disable-pip-version-check', '--no-input',
                 '--no-deps', '--no-build-isolation', '--wheel-dir', wheels, build], 'base-native-wheel')
        artifacts = sorted(wheels.glob('*.whl'))
        if len(artifacts) != 1:
            raise ValueError('one independently built base wheel required')
        wheel = artifacts[0]
        with zipfile.ZipFile(wheel) as bundle:
            metadata_names = [name for name in bundle.namelist() if name.endswith('.dist-info/METADATA')]
            if len(metadata_names) != 1:
                raise ValueError('one original wheel metadata record required')
            metadata = BytesParser().parsebytes(bundle.read(metadata_names[0]))
        distribution = metadata.get('Name'); version = metadata.get('Version')
        if (not isinstance(distribution, str) or not _version(version)
                or _normalize(distribution) in {'pytest'} | {
                    _normalize(row['distribution']) for row in policy['plugins']}):
            raise ValueError('project wheel collides with independently licensed native runner')
        if any(not (build / name).is_file() or (build / name).read_bytes() != raw for name, raw in base_files.items()):
            raise ValueError('native build mutated tracked original source')
        wheel_receipt = {'path': str(wheel), 'sha256': sha256(wheel.read_bytes()), 'bytes': wheel.stat().st_size,
                         'base_commit': base, 'base_identity': base_identity, 'distribution': distribution,
                         'version': version, 'synthetic_version': False}
        (root / 'native-wheel.json').write_text(canonical(wheel_receipt) + '\n')
        command([python, '-m', 'pip', 'install', '--disable-pip-version-check', '--no-input', '--no-deps',
                 str(wheel) + '[test,tests]'], 'project')
        command([python, '-m', 'pip', 'check'], 'pip-check')
        command([python, '-m', 'pip', 'freeze', '--all'], 'pip-freeze')
        environment_started = time.monotonic()
        environment = environment_identity(python)
        costs.append({'phase': 'environment-identity', 'status': 'PASS',
                      'seconds': time.monotonic() - environment_started})
        if environment['pytest_version'] != policy['pytest_version']:
            raise ValueError('installed pytest differs from external policy')
        (root / 'environment.json').write_text(canonical(environment) + '\n')
        contract = {'schema': execution.SCHEMA, 'repository': repository, 'repo_path': str(repo),
            'commit': commit, **identity, 'interpreter': str(python), 'environment_sha256': fingerprint(environment),
            'protocol_binding': protocol_binding, 'horizon_seconds': policy['execution_seconds']}
        # This validates the caller's license and installed identity, without collecting tests.
        validation_started = time.monotonic()
        _, _, _, plugin_identity = execution._context(contract, authority, frozen_policy)
        costs.append({'phase': 'external-policy-validation', 'status': 'PASS',
                      'seconds': time.monotonic() - validation_started})
        (root / 'plugin-identity.json').write_text(canonical(plugin_identity) + '\n')
        (root / 'contract.json').write_text(canonical(contract) + '\n')
        (root / 'policy.json').write_text(canonical(frozen_policy) + '\n')
        return save('PREPARED')
    except (RuntimeError, ValueError, KeyError, OSError, subprocess.SubprocessError) as error:
        if (venv / 'bin/python').is_file():
            result = _command([venv / 'bin/python', '-m', 'pip', 'freeze', '--all'], root / 'pip-freeze-after-failure.log')
            costs.append({'phase': 'pip-freeze-after-failure', **result})
        (root / 'source-boundaries.json').write_text(canonical(boundaries) + '\n')
        return save('UNKNOWN_SETUP', str(error))
