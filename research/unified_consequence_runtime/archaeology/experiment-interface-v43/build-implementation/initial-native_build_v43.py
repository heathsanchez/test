"""Declared, Git-aware build transport over the qualified wheel authenticator.

This operation admits supplemental import bytes, never native outcomes or pytest
plugins.  Local SCM metadata is observed and replay-bound; it is not asserted to
be independently authenticated remote metadata merely because it has a hash.
"""
from __future__ import annotations

import ast
from contextvars import ContextVar
import copy
import importlib.metadata
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import time
import tomllib
from types import FunctionType, SimpleNamespace

from . import native_admission_v42 as admission
from . import native_environment_v42 as environment_operation
from . import native_environment_v2 as original_environment
from . import native_execution_v42 as execution
from . import native_source_v42 as source
from . import generated_overlay_gate as overlay
from . import generated_wheel_evidence as provenance
from . import generic_build_materialization as original_builder

SCHEMA = 'UDM_DECLARED_GENERATED_BUILD_EVIDENCE_V43'
CONTRACT_SCHEMA = 'UDM_GENERIC_NATIVE_PYTEST_V43'
POLICY_SCHEMA = 'UDM_NATIVE_EXECUTION_POLICY_V43'
WHEEL_SCHEMA = 'UDM_AUTHENTICATED_GENERATED_WHEEL_V43'
canonical, fingerprint, sha256 = execution.canonical, execution.fingerprint, execution.sha256
_LOADED_SHA256 = sha256(Path(__file__).read_bytes())
_PINS = ((original_builder, 'bf08dae2ef55a8a2aac368f5404a6e6c4777ddcc7f581f967a0e0f5c7693b980'),
         (provenance, '446515e2257cb0c932759b4e98972a6feefe70a7a65765846e113da488632772'),
         (overlay, '0628d8067bc46d1e918959ba47b05c95bedfdaa93cff6659e3888cc9670d9c89'))
_CONTRACT = {'schema', 'repository', 'repo_path', 'commit', 'git_tree',
             'tracked_tree_sha256', 'file_count', 'interpreter',
             'environment_sha256', 'protocol_binding', 'horizon_seconds'}
_POLICY = {'schema', 'collection_seconds', 'execution_seconds', 'pytest_version', 'plugins'}
BUILD_RECIPE = {
    'schema': 'UDM_EXACT_BASE_LOCAL_SCM_PEP517_BUILD_V43',
    'source': 'fresh Git init; local fetch of exact base ancestry only; raw typed base blobs',
    'scm': 'observed local tag OIDs targeting base ancestry only; no author-test descendants',
    'command': ['-I', '-B', '-m', 'pip', '--isolated', 'wheel', '--use-pep517',
                '--no-deps', '--no-build-isolation', '--no-index', '--no-cache-dir'],
    'environment': 'original independently checked interpreter, distribution files and host stdlib; clean env',
    'comparison': original_builder.BUILD_RECIPE['comparison'],
    'outputs': 'recognized immutable Hatch VCS version-file declaration only',
}
_ATTEMPTS = ContextVar('udm_v43_build_attempts', default=(0, 0.0, ()))


def _guard():
    if sha256(Path(__file__).read_bytes()) != _LOADED_SHA256:
        raise ValueError('UNKNOWN_V43_BUILD_SOURCE_CHANGED')
    for module, digest in _PINS:
        if sha256(Path(module.__file__).read_bytes()) != digest:
            raise ValueError('UNKNOWN_V43_QUALIFIED_BUILD_SOURCE_CHANGED')
    source._guard()
    execution._runner_hash()
    environment_operation._guard()


def attempt_snapshot():
    """Actual pip-wheel launch attempts, including failed process launches."""
    calls, seconds, records = _ATTEMPTS.get()
    return {'build_calls': calls, 'build_seconds': seconds, 'records': list(records)}


def recipe_digest():
    return fingerprint(BUILD_RECIPE)


def _path(value):
    try:
        return source._name(value)
    except (TypeError, ValueError) as error:
        raise ValueError('UNKNOWN_GENERATED_DECLARATION_PATH') from error


def _packages(files):
    packages = {}
    for name in files:
        if name.endswith('/__init__.py'):
            root = name[:-len('/__init__.py')]
            module = root[4:] if root.startswith('src/') else root
            packages.setdefault(module, []).append(root)
    return packages


def _plugin_module(name):
    name = name[4:] if name.startswith('src/') else name
    return name[:-3].replace('/', '.')


def declared_outputs(files):
    """Derive bounded output authority solely from original backend metadata."""
    _guard()
    try:
        if not isinstance(files, dict) or any(not isinstance(raw, bytes) for raw in files.values()):
            raise ValueError('original source bytes required')
        for name in files:
            _path(name)
        data = tomllib.loads(files.get('pyproject.toml', b'').decode('utf-8'))
        build = data.get('build-system', {})
        if (original_environment._git_scm(files) != 'hatch-vcs'
                or build.get('build-backend') != 'hatchling.build'
                or build.get('backend-path')):
            raise ValueError('UNKNOWN_GENERATED_BUILD_BACKEND')
        hatch = data.get('tool', {}).get('hatch', {})
        if hatch.get('version', {}).get('source') != 'vcs':
            raise ValueError('UNKNOWN_GENERATED_BUILD_DECLARATION')
        hook = hatch.get('build', {}).get('hooks', {}).get('vcs', {})
        if not isinstance(hook, dict) or not isinstance(hook.get('version-file'), str):
            raise ValueError('UNKNOWN_GENERATED_BUILD_DECLARATION')
        name = _path(hook['version-file'])
        path = PurePosixPath(name)
        config = admission.configuration(files)
        testpaths = config['ini_options'].get('testpaths', [])
        if (name in files or path.suffix != '.py'
                or path.name in ('__init__.py', 'conftest.py', 'pytest.py', 'setup.py')
                or admission._test_scope(name, config)
                or any(part.startswith('.') or part in ('test', 'tests', 'testing')
                       or part.startswith('test_') for part in path.parts)
                or any(root == '.' or name == root.rstrip('/')
                       or name.startswith(root.rstrip('/') + '/') for root in testpaths)):
            raise ValueError('UNKNOWN_GENERATED_DECLARATION_PROTECTED_PATH')
        packages = _packages(files)
        roots = [(package, candidates) for package, candidates in packages.items()
                 if any(name.startswith(root + '/') for root in candidates)]
        if not roots or any(len(candidates) != 1 for _, candidates in roots):
            raise ValueError('UNKNOWN_GENERATED_DECLARATION_PACKAGE_ROOT')
        # All parents must be real original directory positions, never a tracked
        # file/alias.  No new package initializer gains source ownership.
        if any(parent.as_posix() in files for parent in path.parents if str(parent) != '.'):
            raise ValueError('UNKNOWN_GENERATED_DECLARATION_PARENT_ALIAS')
        manifest = getattr(files, 'manifest', None)
        if manifest is not None:
            source.safe_overlay((name,), manifest, files)
        module = _plugin_module(name)
        if module in config['plugin_requirements']:
            raise ValueError('UNKNOWN_GENERATED_PLUGIN_AUTHORITY')
        for filename, raw in files.items():
            if not filename.endswith('.py'):
                continue
            try:
                tree = ast.parse(raw, filename=filename)
            except (SyntaxError, UnicodeError):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                    continue
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if not any(isinstance(target, ast.Name) and target.id == 'pytest_plugins' for target in targets):
                    continue
                try:
                    value = ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    continue
                if value == module or isinstance(value, (tuple, list)) and module in value:
                    raise ValueError('UNKNOWN_GENERATED_PLUGIN_AUTHORITY')
        return (name,)
    except (KeyError, AttributeError, TypeError, UnicodeError, tomllib.TOMLDecodeError) as error:
        raise ValueError('UNKNOWN_GENERATED_BUILD_DECLARATION') from error


def _host_packages(environment):
    """Reconstruct the child's complete distribution hash from host file bytes."""
    prefix = Path(environment['prefix']).absolute()
    if prefix.resolve() != prefix:
        raise ValueError('UNKNOWN_BUILD_ENVIRONMENT_PREFIX')
    version = environment['runtime_identity']['version_info']
    site = prefix / 'lib' / ('python' + '.'.join(str(x) for x in version[:2])) / 'site-packages'
    rows = []
    for dist in sorted(importlib.metadata.distributions(path=[str(site)]),
                       key=lambda item: (item.metadata['Name'] or '').lower()):
        files = []
        if not dist.files:
            raise ValueError('UNKNOWN_BUILD_PACKAGE_FILE_AUTHORITY')
        for entry in sorted(dist.files, key=str):
            path = Path(dist.locate_file(entry)).absolute()
            if not path.resolve().is_relative_to(prefix) or not path.is_file():
                raise ValueError('UNKNOWN_BUILD_PACKAGE_FILE_OUTSIDE_ENVIRONMENT')
            files.append([str(entry), sha256(path.read_bytes())])
        rows.append([dist.metadata['Name'], dist.version, files])
    if (len(rows) != environment['distribution_count']
            or fingerprint(rows) != environment['distributions_sha256']):
        raise ValueError('UNKNOWN_BUILD_HOST_PACKAGE_IDENTITY')
    return fingerprint(rows)


def _metadata(repo, base, base_identity):
    ancestors_raw = execution.original._git(repo, 'rev-list', base)
    ancestors = ancestors_raw.decode().splitlines()
    if (not ancestors or ancestors[0] != base or len(set(ancestors)) != len(ancestors)
            or any(not re.fullmatch('[0-9a-f]{40}', item) for item in ancestors)):
        raise ValueError('UNKNOWN_BUILD_BASE_ANCESTRY')
    raw = execution.original._git(repo, 'for-each-ref', '--format=%(objectname)%09%(refname)', 'refs/tags')
    tags = []
    lines = []
    for line in raw.decode().splitlines():
        oid, ref = line.split('\t')
        target = execution.original._git(repo, 'rev-parse', ref + '^{}').decode().strip()
        tags.append({'ref': ref, 'tag_object': oid, 'target': target})
        lines.append(oid + '\t' + ref)
        if oid != target:
            lines.append(target + '\t' + ref + '^{}')
    selected = original_environment.ancestor_tag_refs('\n'.join(lines), set(ancestors))
    original_receipts = {}
    for filename in ('source-boundaries.json', 'scm-provenance.json'):
        path = repo.parent / filename
        if not path.exists():
            continue
        if path.is_symlink() or not path.is_file() or path.resolve() != path:
            raise ValueError('UNKNOWN_BUILD_SCM_RECEIPT_PATH')
        receipt = json.loads(path.read_bytes())
        metadata = receipt.get('scm_metadata', {}) if filename == 'source-boundaries.json' else receipt
        if filename == 'source-boundaries.json' and (receipt.get('base_commit') != base
                or receipt.get('base_identity') != base_identity):
            raise ValueError('UNKNOWN_BUILD_ORIGINAL_BASE_RECEIPT')
        if (metadata.get('backend') != 'hatch-vcs' or metadata.get('base_ancestry_only') is not True
                or metadata.get('tracked_source_preserved') is not True
                or metadata.get('ancestor_tags') != selected
                or metadata.get('ancestor_commits_sha256') != sha256(ancestors_raw)):
            raise ValueError('UNKNOWN_BUILD_ORIGINAL_SCM_RECEIPT')
        original_receipts[filename] = sha256(path.read_bytes())
    return {'scope': 'OBSERVED_LOCAL_BASE_REACHABLE_SCM; REMOTE_AUTHENTICITY_NOT_INFERRED_FROM_HASHES',
            'ancestor_commits': ancestors, 'all_observed_tags': tags, 'ancestor_tags': selected,
            'original_receipts_sha256': original_receipts}


def _context(contract, authority, policy):
    _guard()
    if (not isinstance(contract, dict) or set(contract) != _CONTRACT | {'generated_build'}
            or contract['schema'] != CONTRACT_SCHEMA
            or contract['generated_build'] is not None and not isinstance(contract['generated_build'], dict)):
        raise ValueError('wrong V43 build contract fields')
    if not isinstance(policy, dict) or set(policy) != _POLICY or policy['schema'] != POLICY_SCHEMA:
        raise ValueError('wrong V43 build policy fields')
    old_contract = {key: value for key, value in contract.items() if key != 'generated_build'}
    old_contract['schema'] = execution.SCHEMA
    old_policy = dict(policy, schema=execution.POLICY_SCHEMA)
    files, manifest, environment, _ = execution._context(old_contract, authority, old_policy)
    packages = _host_packages(environment)
    base = authority['baseline_commit']
    identity, base_files, base_manifest = source.snapshot(contract['repo_path'], base)
    source.require_executable(base_manifest)
    if identity != authority['baseline_source']:
        raise ValueError('UNKNOWN_BUILD_BASE_SOURCE_IDENTITY')
    outputs = declared_outputs(base_files)
    if declared_outputs(files) != outputs:
        raise ValueError('UNKNOWN_BUILD_ORIGINAL_DECLARATION_CHANGED')
    metadata = _metadata(Path(contract['repo_path']), base, identity)
    binding = {'contract_sha256': fingerprint(dict(contract, generated_build=None)),
               'authority_sha256': fingerprint(authority), 'policy_sha256': fingerprint(policy),
               'repository': contract['repository'], 'protocol_binding': contract['protocol_binding'],
               'base_commit': base, 'base_source': identity,
               'augmented_commit': contract['commit'],
               'augmented_source': {key: contract[key] for key in ('git_tree', 'tracked_tree_sha256', 'file_count')},
               'pyproject_sha256': sha256(base_files['pyproject.toml']), 'declared_outputs': list(outputs),
               'environment': environment, 'host_packages_sha256': packages, 'scm': metadata}
    return {'contract': contract, 'authority': authority, 'policy': policy,
            'files': base_files, 'manifest': base_manifest, 'binding': binding}


def _directory(path):
    path = Path(path).absolute()
    if path.resolve() != path or path.exists() or path.parent.resolve() != path.parent:
        raise ValueError('new canonical build evidence directory required')
    path.mkdir(parents=True)
    return path


def _build(context, output_dir):
    """Repeat only base-reachable Git transport and the original wheel operation."""
    out = _directory(output_dir)
    binding = context['binding']
    started = time.monotonic()
    report = {'schema': 'UDM_EXACT_BASE_BUILD_RECEIPT_V43', 'status': 'STARTED',
              'binding': binding, 'recipe_sha256': recipe_digest(),
              'builder_sha256': _LOADED_SHA256, 'commands': [],
              'costs': {'build_calls': 0, 'build_seconds': 0.0, 'command_calls': 0, 'total_seconds': 0.0}}
    receipt_path = out / 'build-receipt.json'
    def save():
        report['costs']['total_seconds'] = time.monotonic() - started
        receipt_path.write_text(canonical(report) + '\n')
    save()
    clean = execution.original._env(out / 'home')
    clean.update(GIT_OPTIONAL_LOCKS='0', GIT_TERMINAL_PROMPT='0', GIT_CONFIG_NOSYSTEM='1',
                 GIT_CONFIG_GLOBAL='/dev/null')
    def command(argv, phase, *, wheel=False):
        before = time.monotonic()
        row = {'phase': phase, 'argv': [str(value) for value in argv], 'status': 'STARTED'}
        report['commands'].append(row)
        report['costs']['command_calls'] += 1
        if wheel:
            report['costs']['build_calls'] += 1
            calls, seconds, records = _ATTEMPTS.get()
            _ATTEMPTS.set((calls + 1, seconds, (*records, str(receipt_path))))
        save()
        try:
            with (out / (phase + '.stdout.log')).open('wb') as stdout, (out / (phase + '.stderr.log')).open('wb') as stderr:
                result = subprocess.run(row['argv'], env=clean, cwd=out, stdout=stdout, stderr=stderr,
                                        timeout=300, check=False)
            row.update(returncode=result.returncode, status='PASS' if result.returncode == 0 else 'UNKNOWN')
            if result.returncode:
                raise ValueError('UNKNOWN_BUILD_EXECUTION:' + phase)
        except (OSError, subprocess.SubprocessError) as error:
            row.update(status='UNKNOWN', error=type(error).__name__ + ': ' + str(error))
            raise ValueError('UNKNOWN_BUILD_EXECUTION:' + phase) from error
        finally:
            row['seconds'] = time.monotonic() - before
            if wheel:
                report['costs']['build_seconds'] += row['seconds']
                calls, seconds, records = _ATTEMPTS.get()
                _ATTEMPTS.set((calls, seconds + row['seconds'], records))
            save()
    try:
        checkout = out / 'base-build'
        command(['git', 'init', '-q', checkout], 'git-init')
        command(['git', '--no-replace-objects', '-C', checkout, 'fetch', '--no-tags',
                 '--no-recurse-submodules', context['contract']['repo_path'], binding['base_commit']], 'base-local-fetch')
        for index, tag in enumerate(binding['scm']['ancestor_tags']):
            command(['git', '--no-replace-objects', '-C', checkout, 'fetch', '--no-tags',
                     '--no-recurse-submodules', context['contract']['repo_path'],
                     tag['tag_object'] + ':' + tag['ref']], 'base-tag-' + str(index))
        command(['git', '--no-replace-objects', '-C', checkout, '-c', 'core.autocrlf=false',
                 'checkout', '-q', '--detach', binding['base_commit']], 'base-checkout')
        if execution.original._git(checkout, 'rev-list', '--all').decode().splitlines() != binding['scm']['ancestor_commits']:
            raise ValueError('UNKNOWN_BUILD_NONBASE_REACHABILITY')
        if _metadata(checkout, binding['base_commit'], binding['base_source'])['ancestor_tags'] != binding['scm']['ancestor_tags']:
            raise ValueError('UNKNOWN_BUILD_TAG_TRANSPORT')
        source.materialize(checkout, context['files'], context['manifest'], tracked_checkout=True)
        wheels = out / 'wheels'
        wheels.mkdir()
        command([context['contract']['interpreter'], *BUILD_RECIPE['command'], '--wheel-dir', wheels, checkout],
                'base-native-wheel', wheel=True)
        source.validate_materialized(checkout, context['files'], context['manifest'], strict=True)
        generated = {}
        for name in binding['declared_outputs']:
            source._parents(checkout, name)
            path = checkout / name
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or path.resolve() != path:
                raise ValueError('UNKNOWN_BUILD_GENERATED_TOPOLOGY')
            generated[name] = path.read_bytes()
        artifacts = sorted(wheels.glob('*.whl'))
        if len(artifacts) != 1 or artifacts[0].is_symlink() or not artifacts[0].is_file():
            raise ValueError('UNKNOWN_BUILD_OUTPUT')
        # Reconstruct every original binding after backend execution, including
        # host package files, SCM metadata and original source/test identities.
        if _context(context['contract'], context['authority'], context['policy'])['binding'] != binding:
            raise ValueError('UNKNOWN_BUILD_SOURCE_OR_ENVIRONMENT_CHANGED')
        wheel = artifacts[0]
        evidence = {'schema': WHEEL_SCHEMA, 'source_commit': binding['base_commit'],
                    'source_tree_sha256': binding['base_source']['tracked_tree_sha256'],
                    'wheel_path': str(wheel), 'wheel_sha256': sha256(wheel.read_bytes()),
                    'wheel_content_sha256': overlay.wheel_content_digest(wheel),
                    'build_recipe_sha256': recipe_digest(),
                    'build_environment_sha256': fingerprint(binding['environment']),
                    'builder_sha256': _LOADED_SHA256}
        report.update(status='BUILT_NOT_SCIENTIFICALLY_VERIFIED', generated_wheel_evidence=evidence,
                      generated_sha256={name: sha256(raw) for name, raw in sorted(generated.items())})
        report['costs']['wheel_bytes'] = wheel.stat().st_size
        save()
        return report
    except Exception as error:
        report.update(status='UNKNOWN_BUILD', error=type(error).__name__ + ': ' + str(error))
        save()
        raise


def _qualified_authenticator(materialize):
    """Reuse the qualified validator/rebuild function code with an explicit seam."""
    builder = SimpleNamespace(SCHEMA=WHEEL_SCHEMA, recipe_digest=recipe_digest,
                              sha256=lambda path: sha256(Path(path).read_bytes()),
                              __file__=__file__, materialize_files=materialize)
    namespace = dict(vars(provenance), build=builder)
    validate = FunctionType(provenance.validate_evidence.__code__, namespace, 'validate_evidence',
                            provenance.validate_evidence.__defaults__)
    validate.__kwdefaults__ = provenance.validate_evidence.__kwdefaults__
    namespace['validate_evidence'] = validate
    authenticate = FunctionType(provenance.authenticated_generated_modules.__code__, namespace,
                                'authenticated_generated_modules', provenance.authenticated_generated_modules.__defaults__)
    authenticate.__kwdefaults__ = provenance.authenticated_generated_modules.__kwdefaults__
    return validate, authenticate


def _additions(context, wheel_evidence):
    validate, _ = _qualified_authenticator(None)
    binding = context['binding']
    wheel = validate(wheel_evidence, source_commit=binding['base_commit'],
                     source_tree_sha256=binding['base_source']['tracked_tree_sha256'],
                     environment_sha256=fingerprint(binding['environment']))
    additions = overlay.generated_overlay(wheel, context['files'],
        expected_wheel_sha256=wheel_evidence['wheel_sha256'], allow_declared_addopts=True)
    if set(additions) != set(binding['declared_outputs']):
        raise ValueError('UNKNOWN_BUILD_UNDECLARED_GENERATED_SET')
    for name, raw in additions.items():
        try:
            tree = ast.parse(raw, filename=name)
        except (SyntaxError, UnicodeError) as error:
            raise ValueError('UNKNOWN_GENERATED_PYTHON') from error
        if admission._collection_declarations(tree):
            raise ValueError('UNKNOWN_GENERATED_PLUGIN_AUTHORITY')
    return additions


def prepare(contract, authority, policy, output_dir):
    """Build the exact original base; produce transport evidence only."""
    context = _context(contract, authority, policy)
    report = _build(context, output_dir)
    additions = _additions(context, report['generated_wheel_evidence'])
    if {name: sha256(raw) for name, raw in additions.items()} != report['generated_sha256']:
        raise ValueError('UNKNOWN_BUILD_GENERATED_SOURCE_WHEEL_DIFFER')
    evidence = {'schema': SCHEMA, 'binding': context['binding'],
                'wheel_evidence': report['generated_wheel_evidence'],
                'generated_sha256': {name: sha256(raw) for name, raw in sorted(additions.items())},
                'preparation': {'output': str(Path(output_dir).absolute()), 'costs': report['costs']}}
    (Path(output_dir) / 'generated-build-evidence.json').write_text(canonical(evidence) + '\n')
    return evidence


def _read(contract, authority, policy, evidence):
    context = _context(contract, authority, policy)
    if (not isinstance(evidence, dict) or set(evidence) != {'schema', 'binding', 'wheel_evidence',
            'generated_sha256', 'preparation'} or evidence['schema'] != SCHEMA
            or evidence['binding'] != context['binding']):
        raise ValueError('UNKNOWN_BUILD_EVIDENCE_BINDING')
    preparation = evidence['preparation']
    if (not isinstance(preparation, dict) or set(preparation) != {'output', 'costs'}
            or not isinstance(preparation['output'], str) or not Path(preparation['output']).is_absolute()
            or not isinstance(preparation['costs'], dict)
            or set(preparation['costs']) != {'build_calls', 'build_seconds', 'command_calls', 'total_seconds', 'wheel_bytes'}
            or preparation['costs']['build_calls'] != 1
            or any(type(value) not in (int, float) or not math.isfinite(value) or value < 0
                   for value in preparation['costs'].values())):
        raise ValueError('UNKNOWN_BUILD_EVIDENCE_COST_FIELDS')
    additions = _additions(context, evidence['wheel_evidence'])
    if evidence['generated_sha256'] != {name: sha256(raw) for name, raw in sorted(additions.items())}:
        raise ValueError('UNKNOWN_BUILD_GENERATED_DIGEST')
    return context, additions


def read_generated(contract, authority, policy, evidence):
    """Validate retained bindings and bytes; this makes no rebuild claim."""
    return _read(contract, authority, policy, evidence)[1]


def verify(contract, authority, policy, evidence, output_dir):
    """Independently repeat the qualified original build authentication."""
    context, expected = _read(contract, authority, policy, evidence)
    binding = context['binding']
    def materialize(files, destination, **kwargs):
        if (files != context['files'] or kwargs['source_commit'] != binding['base_commit']
                or kwargs['source_tree_sha256'] != binding['base_source']['tracked_tree_sha256']
                or kwargs['python'] != contract['interpreter']
                or kwargs['environment_sha256'] != fingerprint(binding['environment'])
                or kwargs['source_manifest'] != context['manifest']):
            raise ValueError('UNKNOWN_INDEPENDENT_BUILD_SOURCE')
        return _build(context, destination)
    _, authenticate = _qualified_authenticator(materialize)
    started = time.monotonic()
    try:
        additions, report = authenticate(context['files'], evidence['wheel_evidence'],
            source_commit=binding['base_commit'], source_tree_sha256=binding['base_source']['tracked_tree_sha256'],
            interpreter=contract['interpreter'], environment_sha256=fingerprint(binding['environment']),
            output_dir=output_dir, source_manifest=context['manifest'], allow_declared_addopts=True)
        if additions != expected or _additions(context, report['generated_wheel_evidence']) != expected:
            raise ValueError('independent build generated bytes differ')
        receipt = {'schema': 'UDM_INDEPENDENT_GENERATED_BUILD_VERIFICATION_V43',
                   'status': 'INDEPENDENT_BUILD_AUTHENTICATED_NOT_NATIVE_OUTCOME',
                   'evidence_sha256': fingerprint(evidence), 'binding': binding,
                   'build': report, 'costs': dict(report['costs'], verification_seconds=time.monotonic() - started)}
        (Path(output_dir) / 'verification.json').write_text(canonical(receipt) + '\n')
        return additions, receipt
    except Exception as error:
        out = Path(output_dir)
        if out.is_dir() and out.resolve() == out.absolute():
            (out / 'verification.json').write_text(canonical({'schema': 'UDM_INDEPENDENT_GENERATED_BUILD_VERIFICATION_V43',
                'status': 'UNKNOWN_BUILD_AUTHENTICATION', 'error': type(error).__name__ + ': ' + str(error),
                'seconds': time.monotonic() - started, 'attempts': attempt_snapshot()}) + '\n')
        raise


_guard()
