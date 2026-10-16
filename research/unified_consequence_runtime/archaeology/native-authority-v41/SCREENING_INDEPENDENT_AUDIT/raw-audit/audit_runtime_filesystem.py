#!/usr/bin/env python3
"""Independent, offline filesystem audit; never imports or runs target code.

Run with control Python, -I -B, and PYTHONDONTWRITEBYTECODE=1. The qualified
controller is read as text/AST only. No Git, network, subprocess, eval, or exec.
"""
import ast
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re

AUDIT = Path('/workspace/qualification/native-authority-v41-screening-audit')
OUT = AUDIT / 'raw-audit'
SEALED = Path('/workspace/qualification/native-authority-v41-screening-sealed')
PREP = Path('/workspace/qualification/native-authority-v41-profile-preparation')
SOURCE = AUDIT / 'committed-source/research/unified_consequence_runtime'
CATALOG = AUDIT / 'metadata-preaudit/source-binding/research/unified_consequence_runtime/archaeology/native-authority-v41/ENVIRONMENT_CATALOG.json'
EXPECTED_INVENTORY_KEYS = {'authority', 'catalog_sha256', 'runtime_paths_sha256', 'runtimes', 'schema'}
EXPECTED_RECORD_KEYS = {'interpreter', 'identity', 'import_roots', 'stdlib_files'}
EXPECTED_IDENTITY_KEYS = {'base_prefix', 'executable_sha256', 'implementation', 'stdlib_manifest_sha256', 'version_info'}
SUFFIXES = ('.py', '.pyc', '.pyo', '.so', '.pyd', '.dll', '.dylib')
SKIP_DIRS = ('site-packages', 'dist-packages')
CHECKS = []


def read_json(path):
    def unique(pairs):
        value = {}
        for k, v in pairs:
            if k in value:
                raise ValueError('duplicate JSON member: ' + k)
            value[k] = v
        return value
    return json.loads(Path(path).read_bytes(), object_pairs_hook=unique)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def fingerprint(value):
    return digest(canonical(value).encode())


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def file_ref(path):
    path = Path(path)
    return {'path': str(path), 'size': path.stat().st_size, 'sha256': file_hash(path)}


def check(name, actual, expected=True):
    ok = actual == expected
    CHECKS.append({'name': name, 'verified': ok, 'actual': actual, 'expected': expected})
    return ok


def write_json(name, value):
    path = OUT / name
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')
    return dict(file_ref(path), canonical_sha256=fingerprint(value))


def canonical_name(name):
    return re.sub(r'[-_.]+', '-', name).lower()


def source_walk(roots):
    """Independently transcribe qualified stdlib_files, including its filters.

    Additional diagnostics do not change the source-equivalent row list. In
    particular, os.walk of an absent root contributes no files in the source.
    """
    paths = set()
    diagnostics = []
    for location in sorted({p for p in roots if p}):
        root = Path(location)
        if root.is_symlink():
            raise RuntimeError('UNKNOWN_RUNTIME_SYMLINK_DIRECTORY: ' + str(root))
        resolved = root.resolve()
        info = {'path': str(root), 'resolved': str(resolved), 'exists': root.exists(),
                'is_directory': root.is_dir(), 'matched_paths_before_deduplication': 0,
                'excluded_directories': [], 'walk_errors': [], 'resolved_file_symlinks': []}
        def walk_error(error):
            info['walk_errors'].append(str(error))
        for folder, dirs, files in os.walk(str(resolved), onerror=walk_error):
            info['excluded_directories'].extend(str(Path(folder, name)) for name in dirs if name in SKIP_DIRS)
            dirs[:] = sorted(name for name in dirs if name not in SKIP_DIRS)
            if any(Path(folder, name).is_symlink() for name in dirs):
                raise RuntimeError('UNKNOWN_RUNTIME_SYMLINK_DIRECTORY: ' + str(folder))
            for name in files:
                if name.endswith(SUFFIXES):
                    path = Path(folder, name)
                    if path.is_symlink():
                        info['resolved_file_symlinks'].append({'path': str(path), 'resolved': str(path.resolve())})
                    paths.add(path.resolve())
                    info['matched_paths_before_deduplication'] += 1
        diagnostics.append(info)
    if not paths:
        raise RuntimeError('original standard library unavailable')
    return [[str(path), file_hash(path)] for path in sorted(paths)], diagnostics


def package_inventory(interpreter, profile):
    """Same filesystem metadata/RECORD interpretation as source, no imports.

    importlib.metadata is the control interpreter's standard library. Explicit
    path enumeration reads target metadata only and never imports target code.
    """
    venv = Path(interpreter).absolute().parent.parent
    site = venv / 'lib' / ('python' + '.'.join(profile['python_version'].split('.')[:2])) / 'site-packages'
    expected = {canonical_name(pin.split('==', 1)[0]): pin.split('==', 1)[1] for pin in profile['packages']}
    found = {}
    all_found = []
    rows = []
    ownership = {}
    problems = []
    for dist in importlib.metadata.distributions(path=[str(site)]):
        name = canonical_name(dist.metadata['Name'] or '')
        all_found.append([name, dist.version])
        if name not in expected:
            continue
        if name in found:
            problems.append('duplicate pinned distribution: ' + name)
        if dist.version != expected[name]:
            problems.append('pinned version differs: ' + name)
        found[name] = dist.version
        files = []
        owned = set()
        if not dist.files:
            problems.append('distribution file authority absent: ' + name)
        for entry in sorted(dist.files or [], key=str):
            path = Path(dist.locate_file(entry)).absolute()
            if not path.resolve().is_relative_to(venv.resolve()) or not path.is_file():
                problems.append('distribution file unavailable or outside venv: ' + name + ': ' + str(entry))
                continue
            files.append([str(entry), file_hash(path)])
            owned.add(str(path.resolve()))
        rows.append([name, dist.version, files])
        ownership[name] = owned
    return {'venv': str(venv), 'site_packages': str(site), 'expected': expected,
            'found': found, 'all_found': sorted(all_found), 'rows': sorted(rows),
            'problems': problems, 'ownership': ownership}


def builtin_plugin_names(site):
    """Read only literal list/set/tuple constants and name/star expansions."""
    source = Path(site) / '_pytest/config/__init__.py'
    known = {}
    def strings(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return {node.value}
        if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
            result = set()
            for entry in node.elts:
                result.update(strings(entry))
            return result
        if isinstance(node, ast.Starred):
            return strings(node.value)
        if isinstance(node, ast.Name) and node.id in known:
            return known[node.id]
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.BitOr)):
            return strings(node.left) | strings(node.right)
        raise ValueError('nonliteral pytest builtin plugin definition')
    for node in ast.parse(source.read_bytes()).body:
        if isinstance(node, ast.Assign):
            names = [x.id for x in node.targets if isinstance(x, ast.Name)]
            if set(names) & {'essential_plugins', 'default_plugins', 'builtin_plugins'}:
                value = strings(node.value)
                for name in names:
                    known[name] = value
    return known.get('builtin_plugins', set()), file_ref(source)


def static_plugins(profile, packages):
    if not profile['plugins']:
        return [], None
    site = Path(packages['site_packages'])
    builtins, builtin_source = builtin_plugin_names(site)
    result = []
    for row in profile['plugins']:
        name = row['module']
        module = '_pytest.' + name if name in builtins else name
        relative = Path(*module.split('.'))
        candidates = [site / (str(relative) + '.py'), site / relative / '__init__.py']
        existing = [p for p in candidates if p.is_file()]
        check(profile['id'] + ': plugin unique static source: ' + name, len(existing), 1)
        if not existing:
            continue
        path = existing[0].resolve()
        dist_name = canonical_name(row['distribution'])
        check(profile['id'] + ': plugin package version: ' + name, packages['found'].get(dist_name), row['version'])
        check(profile['id'] + ': plugin file owned by licensed distribution: ' + name,
              str(path) in packages['ownership'].get(dist_name, set()))
        result.append(dict(row, path=str(path), sha256=file_hash(path)))
    return result, builtin_source


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = read_json(CATALOG)
    runtime_paths_file = PREP / 'RUNTIMES.json'
    runtime_paths = read_json(runtime_paths_file)
    inventories = []
    for number in range(7):
        path = SEALED / ('case-%03d.RUNTIME_INVENTORY.json' % number)
        value = read_json(path)
        inventories.append((path, value))
    inventory = inventories[0][1]
    check('all seven inventories byte-identical', len({file_hash(p) for p, _ in inventories}), 1)
    check('all seven inventories JSON-identical', all(v == inventory for _, v in inventories))
    check('inventory exact top-level field set', sorted(inventory), sorted(EXPECTED_INVENTORY_KEYS))
    check('inventory schema', inventory['schema'], 'UDM_NATIVE_FRONTIER_RUNTIME_INVENTORY_V3')
    check('inventory authority', inventory['authority'], 'SOURCE_INDEPENDENT_RUNTIME_IDENTITY_ONLY_NO_TASK_ADMISSION')
    check('catalog schema', catalog['schema'], 'UDM_NATIVE_ENVIRONMENT_CATALOG_V3')
    check('catalog canonical fingerprint binding', inventory['catalog_sha256'], fingerprint(catalog))
    check('runtime-path canonical fingerprint binding', inventory['runtime_paths_sha256'], fingerprint(runtime_paths))
    profiles = {p['id']: p for p in catalog['profiles']}
    check('unique catalog profile IDs', len(profiles), len(catalog['profiles']))
    check('inventory profile set', sorted(inventory['runtimes']), sorted(profiles))
    check('external runtime-path profile set', sorted(runtime_paths), sorted(profiles))
    metadata = CATALOG.parent / catalog['package_metadata_file']
    if not metadata.is_file():
        metadata = SOURCE / 'archaeology/native-authority-v41' / catalog['package_metadata_file']
    metadata_binding = None
    check('catalog package-metadata retained file available', metadata.is_file())
    if metadata.is_file():
        metadata_binding = file_ref(metadata)
        check('catalog package-metadata raw SHA256 binding', catalog['package_metadata_sha256'], file_hash(metadata))
    runtimes = {}
    host_stdlib_rows = {}
    host_package_rows = {}
    limitations = [
        'Filesystem-only audit: no candidate interpreters, native controller, tests, target imports, Git, or network were executed.',
        'Implementation, version_info, base_prefix, and sysconfig-derived root provenance are retained claims. Their internal catalog consistency is checked; they were not independently queried from an executable.',
        'The qualified stdlib walk excludes site-packages/dist-packages and includes only .py/.pyc/.pyo/.so/.pyd/.dll/.dylib filenames. It resolves matching file symlinks and deduplicates resolved paths; absent roots can contribute zero files.',
        'Installed package file rows follow distribution metadata/RECORD, matching the source. They do not assert that every unlisted site-packages file belongs to the pinned package set.',
        'Static plugin path/version/ownership/byte checks do not execute import resolution or establish runtime plugin behavior.'
    ]
    for ident, record in inventory['runtimes'].items():
        p = profiles[ident]
        identity = record['identity']
        pin_pairs = []
        malformed_pins = []
        for pin in p['packages']:
            matched = re.fullmatch(r'([A-Za-z0-9][A-Za-z0-9_.-]*)==([A-Za-z0-9][A-Za-z0-9_.+-]*)', pin)
            if not matched or '*' in pin:
                malformed_pins.append(pin)
            else:
                pin_pairs.append([canonical_name(matched[1]), matched[2]])
        check(ident + ': exact unconditional literal package pins', malformed_pins, [])
        check(ident + ': package names unique after canonicalization', len({x[0] for x in pin_pairs}), len(pin_pairs))
        pins = dict(pin_pairs)
        check(ident + ': pytest package pin vs profile', pins.get('pytest'), p['pytest_version'])
        check(ident + ': complete package-artifact name set', sorted(p['package_artifacts']), sorted(pins))
        check(ident + ': plugin definitions have exact schema and exact package/version binding',
              all(isinstance(row, dict) and set(row) == {'module', 'distribution', 'version'}
                  and all(isinstance(v, str) for v in row.values())
                  and re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*', row['module'])
                  and pins.get(canonical_name(row['distribution'])) == row['version'] for row in p['plugins']))
        check(ident + ': plugin modules unique', len({row['module'] for row in p['plugins']}), len(p['plugins']))
        check(ident + ': exact record fields', sorted(record), sorted(EXPECTED_RECORD_KEYS))
        check(ident + ': exact identity fields', sorted(identity), sorted(EXPECTED_IDENTITY_KEYS))
        check(ident + ': interpreter path binding', record['interpreter'], str(Path(runtime_paths[ident]).absolute()))
        check(ident + ': runtime version claim vs catalog', '.'.join(map(str, identity['version_info'][:3])), p['python_version'])
        check(ident + ': implementation claim vs catalog', identity['implementation'].lower(), p['python_implementation'].lower())
        check(ident + ': import roots sorted/deduplicated/absolute', record['import_roots'] == sorted(set(record['import_roots'])) and all(Path(x).is_absolute() for x in record['import_roots']))
        check(ident + ': manifest row shape', all(isinstance(x, list) and len(x) == 2 and isinstance(x[0], str) and Path(x[0]).is_absolute() and re.fullmatch('[a-f0-9]{64}', x[1]) for x in record['stdlib_files']))
        executable = Path(record['interpreter'])
        actual_executable_hash = file_hash(executable)
        check(ident + ': current executable host SHA256', actual_executable_hash, identity['executable_sha256'])
        current_rows, roots = source_walk(record['import_roots'])
        host_stdlib_rows[ident] = current_rows
        check(ident + ': complete source-equivalent stdlib rows', current_rows == record['stdlib_files'])
        check(ident + ': current stdlib canonical fingerprint', fingerprint(current_rows), identity['stdlib_manifest_sha256'])
        check(ident + ': recorded stdlib canonical fingerprint', fingerprint(record['stdlib_files']), identity['stdlib_manifest_sha256'])
        missing_roots = [r['path'] for r in roots if not r['is_directory']]
        if missing_roots:
            limitations.append(ident + ': these retained roots are absent/non-directory and contribute zero files under the qualified walk: ' + ', '.join(missing_roots))
        check(ident + ': existing root walk without read errors', [e for r in roots if r['exists'] for e in r['walk_errors']], [])
        packages = package_inventory(executable, p)
        host_package_rows[ident] = packages['rows']
        check(ident + ': pinned package versions and uniqueness', packages['found'], packages['expected'])
        check(ident + ': pinned package file authority', packages['problems'], [])
        check(ident + ': all installed distribution name/version pairs equal pins', packages['all_found'], sorted(map(list, packages['expected'].items())))
        prep_dir = executable.absolute().parent.parent.parent
        retained = {}
        for name in ('runtime-identity.json', 'pinned-package-files.json', 'installed-packages.json', 'plugin-identity.json'):
            candidate = prep_dir / name
            if candidate.is_file():
                retained[name] = file_ref(candidate)
                old = read_json(candidate)
                if name == 'runtime-identity.json':
                    check(ident + ': runtime record equals retained preparation', record == old)
                elif name == 'pinned-package-files.json':
                    check(ident + ': current pinned package rows equal retained preparation', packages['rows'] == old)
                elif name == 'installed-packages.json':
                    old_names = sorted([canonical_name(x['name']), x['version']] for x in old)
                    check(ident + ': current installed package pairs equal retained preparation', packages['all_found'], old_names)
        preparation_metadata = [file_ref(prep_dir / name) for name in (
            'environment.json', 'metadata-receipt.json', 'download-receipts.json',
            'pins.txt', 'pip-check.log', 'commands.json') if (prep_dir / name).is_file()]
        if (executable.absolute().parent.parent / 'pyvenv.cfg').is_file():
            preparation_metadata.append(file_ref(executable.absolute().parent.parent / 'pyvenv.cfg'))
        plugins, builtin_source = static_plugins(p, packages)
        if 'plugin-identity.json' in retained:
            check(ident + ': static plugin identities equal retained preparation', plugins == read_json(prep_dir / 'plugin-identity.json'))
        wheel_rows = []
        for name, artifact in sorted(p['package_artifacts'].items()):
            wheel = prep_dir / 'wheels' / artifact['filename']
            row = dict(artifact_name=name, path=str(wheel), exists=wheel.is_file())
            check(ident + ': retained wheel available: ' + name, wheel.is_file())
            if wheel.is_file():
                row.update(size=wheel.stat().st_size, sha256=file_hash(wheel))
                check(ident + ': retained wheel SHA256: ' + name, row['sha256'], artifact['sha256'])
                check(ident + ': retained wheel size: ' + name, row['size'], artifact['size'])
            wheel_rows.append(row)
        runtimes[ident] = {
            'interpreter': str(executable), 'interpreter_resolved': str(executable.resolve()),
            'interpreter_is_symlink': executable.is_symlink(), 'executable_host_sha256': actual_executable_hash,
            'retained_identity': identity, 'stdlib_row_count': len(current_rows),
            'stdlib_host_canonical_sha256': fingerprint(current_rows), 'root_diagnostics': roots,
            'stdlib_rows_match_inventory': current_rows == record['stdlib_files'],
            'stdlib_missing_or_extra_paths': {'missing': sorted(set(x[0] for x in record['stdlib_files']) - set(x[0] for x in current_rows)), 'extra': sorted(set(x[0] for x in current_rows) - set(x[0] for x in record['stdlib_files']))},
            'package_count': len(packages['rows']), 'package_file_count': sum(len(x[2]) for x in packages['rows']),
            'package_manifest_canonical_sha256': fingerprint(packages['rows']),
            'site_packages': packages['site_packages'], 'installed_name_version_pairs': packages['all_found'],
            'retained_preparation_files': retained, 'plugin_definitions': p['plugins'],
            'additional_retained_preparation_metadata': preparation_metadata,
            'static_plugin_files': plugins, 'static_builtin_plugin_definition_source': builtin_source,
            'retained_wheel_artifacts': wheel_rows,
        }
    inventories_ref = write_json('RUNTIME_HOST_STDLIB_FILES.json', host_stdlib_rows)
    packages_ref = write_json('RUNTIME_HOST_PINNED_PACKAGE_FILES.json', host_package_rows)
    source_refs = [file_ref(SOURCE / n) for n in ('qualify_native_frontier_v3.py', 'native_environment_v3.py', 'native_environment_selection_v3.py', 'native_execution_v3.py', 'native_execution_v2.py', 'decisive_native_verify.py')]
    report = {
        'schema': 'V41_OFFLINE_RUNTIME_FILESYSTEM_AUDIT_V1',
        'authority': 'OFFLINE_RETAINED_EVIDENCE_AND_CURRENT_HOST_BYTES_ONLY_NO_NATIVE_REPLAY',
        'status': 'FILESYSTEM_CHECKS_VERIFIED' if all(x['verified'] for x in CHECKS) else 'FILESYSTEM_CHECKS_HAVE_DIFFERENCES',
        'audit_script': file_ref(Path(__file__)), 'source_method_files': source_refs,
        'catalog': dict(file_ref(CATALOG), canonical_sha256=fingerprint(catalog)),
        'package_metadata': metadata_binding,
        'external_runtime_paths': dict(file_ref(runtime_paths_file), canonical_sha256=fingerprint(runtime_paths)),
        'inventories': [dict(file_ref(path), canonical_sha256=fingerprint(value)) for path, value in inventories],
        'checks_count': len(CHECKS), 'checks_verified': sum(x['verified'] for x in CHECKS),
        'failed_checks': [x for x in CHECKS if not x['verified']], 'checks': CHECKS,
        'runtimes': runtimes, 'current_full_stdlib_file_inventory': inventories_ref,
        'current_full_pinned_package_file_inventory': packages_ref,
        'limitations': limitations,
    }
    report_ref = write_json('RUNTIME_AUDIT.json', report)
    print(json.dumps({'report': report_ref, 'status': report['status'], 'checks_count': len(CHECKS),
                      'checks_verified': report['checks_verified'], 'failed_checks': report['failed_checks'],
                      'runtimes': {k: {n: v[n] for n in ('stdlib_row_count', 'package_count', 'package_file_count', 'stdlib_rows_match_inventory')} for k, v in runtimes.items()}}, sort_keys=True))


if __name__ == '__main__':
    main()
