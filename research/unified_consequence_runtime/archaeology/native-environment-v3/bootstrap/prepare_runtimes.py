"""Prepare exact catalog runtimes before accessing any target source."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from email.parser import BytesParser
import hashlib
import json
import os
from pathlib import Path
import platform
import ssl
import subprocess
import sys
import urllib.request
import zipfile

from packaging.utils import canonicalize_name

from metadata_receipt import validate
from stdlib_cache import manifest, RUNTIME_SUFFIXES

HERE = Path(__file__).resolve().parent


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


def runtime_import_roots(interpreter):
    raw = subprocess.check_output([str(interpreter), '-I', '-B', '-c',
        "import json,sysconfig;print(json.dumps([sysconfig.get_path('stdlib'),sysconfig.get_path('platstdlib'),sysconfig.get_config_var('DESTSHARED')]))"],
        text=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    return sorted({str(Path(path).absolute()) for path in json.loads(raw) if path})


def warm_runtime(interpreter, receipt_path):
    """Compile original stdlib sources before freezing their executable caches."""
    roots = runtime_import_roots(interpreter)
    before = manifest(roots, exclude_bytecode=True)
    compilation = None; failure = None; stderr = ''
    try:
        process = subprocess.run([str(interpreter), '-I', '-B', str(HERE / 'stdlib_cache.py'),
            json.dumps(roots)], capture_output=True, text=True, timeout=600,
            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        stderr = process.stderr
        if process.returncode:
            raise ValueError('original stdlib compiler failed: ' + str(process.returncode))
        compilation = json.loads(process.stdout)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        failure = type(error).__name__ + ': ' + str(error)
    after = manifest(roots, exclude_bytecode=True)
    status = ('UNKNOWN_STDLIB_SOURCE_CHANGED' if before != after else
              'UNKNOWN_STDLIB_COMPILER_FAILURE' if failure else 'PREPARED_STDLIB_BYTECODE')
    receipt = {'schema': 'UDM_ORIGINAL_STDLIB_CACHE_PREPARATION_V3', 'status': status,
        'interpreter': str(interpreter), 'import_roots': roots,
        'source_manifest_before': before, 'source_manifest_after': after,
        'bytecode_manifest': manifest(roots, suffixes=('.pyc', '.pyo')),
        'compilation': compilation, 'compiler_error': failure, 'compiler_stderr': stderr}
    write_json(Path(receipt_path), receipt)
    if before != after:
        raise ValueError('original stdlib nonbytecode source bytes changed during preparation')
    if failure:
        raise ValueError(failure)
    return receipt


def audit_runtime_freeze(frozen):
    """Name host byte differences after fixtures; never adjust frozen authority."""
    runtimes = {}; good = True
    for ident, record in sorted(frozen['runtimes'].items()):
        before = dict(record['stdlib_files'])
        after = dict(manifest(record['import_roots'], suffixes=RUNTIME_SUFFIXES))
        executable = hashlib.sha256(Path(record['interpreter']).read_bytes()).hexdigest()
        row = {'added': sorted(after.keys() - before.keys()), 'removed': sorted(before.keys() - after.keys()),
               'changed': sorted(name for name in before.keys() & after.keys() if before[name] != after[name]),
               'executable_changed': executable != record['identity']['executable_sha256']}
        row['changes'] = {name: {'before': before.get(name), 'after': after.get(name)}
                         for name in row['added'] + row['removed'] + row['changed']}
        good = good and not (row['added'] or row['removed'] or row['changed'] or row['executable_changed'])
        runtimes[ident] = row
    return {'schema': 'UDM_POST_FIXTURE_RUNTIME_BYTE_AUDIT_V3',
            'status': 'PASS_FROZEN_RUNTIME_BYTES' if good else 'UNKNOWN_RUNTIME_BYTES_CHANGED',
            'runtimes': runtimes, 'frozen_authority_modified': False}


def download(record, directory):
    path = directory / record['filename']
    if path.name != record['filename'] or path.exists():
        raise ValueError('new simple artifact filename required')
    digest = hashlib.sha256()
    size = 0
    with urllib.request.urlopen(record['url'], context=ssl.create_default_context(),
                                timeout=120) as response, path.open('xb') as output:
        if response.status != 200 or not response.geturl().startswith('https://'):
            raise ValueError('verified HTTPS artifact transport required')
        while block := response.read(1024 * 1024):
            output.write(block)
            digest.update(block)
            size += len(block)
    if digest.hexdigest() != record['sha256'] or size != record['size']:
        raise ValueError('downloaded artifact digest or size differs')
    if path.suffix == '.whl':
        with zipfile.ZipFile(path) as bundle:
            names = [n for n in bundle.namelist()
                     if n.count('/') == 1 and n.endswith('.dist-info/METADATA')]
            if len(names) != 1:
                raise ValueError('one wheel METADATA required')
            raw = bundle.read(names[0])
            BytesParser().parsebytes(raw)
            if hashlib.sha256(raw).hexdigest() != record['metadata_sha256']:
                raise ValueError('wheel metadata digest differs')
    return {'filename': path.name, 'url': record['url'], 'bytes': size,
            'sha256': digest.hexdigest(), 'tls_verification': True}


def prepare(catalog_path, destination, output):
    if sys.version_info[:3] != (3, 12, 14):
        raise ValueError('bootstrap controller must be CPython 3.12.14')
    if platform.system() != 'Linux' or platform.machine() != 'x86_64':
        raise ValueError('catalog bootstrap requires Linux x86_64')
    destination = destination.absolute()
    if destination.exists() or destination.resolve() != destination:
        raise ValueError('new canonical isolated destination required')
    receipt = validate(catalog_path)
    catalog = json.loads(catalog_path.read_text())
    profiles = {p['python_version']: p for p in catalog['profiles']}
    if set(profiles) != {'3.6.5', '3.12.14'} or len(catalog['profiles']) != 2:
        raise ValueError('expected two independently fixed runtime profiles')
    legacy_pins = (HERE / 'legacy-pins.txt').read_text().splitlines()
    if sorted(legacy_pins) != sorted(profiles['3.6.5']['packages']):
        raise ValueError('legacy bootstrap closure differs from frozen catalog')
    destination.mkdir(parents=True)
    write_json(destination / 'metadata-receipt.json', receipt)
    write_json(destination / 'catalog.json', catalog)
    environment = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}

    def run(argv, name):
        with (destination / (name + '.log')).open('wb') as log:
            subprocess.run([str(x) for x in argv], env=environment, stdout=log,
                           stderr=subprocess.STDOUT, timeout=600, check=True)

    installer = json.loads((HERE / 'official-legacy-installer.json').read_text())
    installer_receipt = download(installer, destination)
    write_json(destination / 'installer-download.json', installer_receipt)
    base = destination / 'miniconda-base'
    run(['bash', destination / installer['filename'], '-b', '-p', base], 'legacy-installer')
    modern_python = Path(getattr(sys, '_base_executable', sys.executable)).absolute()
    modern_version = subprocess.check_output(
        [str(modern_python), '-B', '-c', 'import platform; print(platform.python_version())'],
        env=environment, text=True).strip()
    if modern_version != '3.12.14':
        raise ValueError('modern runtime must be exact setup-python CPython 3.12.14')
    runtime_map = {profiles['3.12.14']['id']: str(modern_python)}
    for version, profile in [('3.6.5', profiles['3.6.5'])]:
        folder = destination / profile['id']
        wheels = folder / 'wheels'
        wheels.mkdir(parents=True)
        artifacts = list(profile['package_artifacts'].values())
        if len({a['filename'] for a in artifacts}) != len(artifacts):
            raise ValueError('duplicate profile artifact filename')
        with ThreadPoolExecutor(max_workers=6) as pool:
            downloaded = list(pool.map(lambda a: download(a, wheels), artifacts))
        write_json(folder / 'download-receipts.json', downloaded)
        requirements = folder / 'pins.txt'
        requirements.write_text('\n'.join(profile['packages']) + '\n')
        source_python = base / 'bin/python'
        venv = folder / 'venv'
        run([source_python, '-B', '-m', 'venv', venv], profile['id'] + '-venv')
        python = venv / 'bin/python'
        run([python, '-B', '-m', 'pip', 'install', '--disable-pip-version-check',
             '--no-input', '--no-index', '--no-deps', '--find-links', wheels,
             '-r', requirements], profile['id'] + '-install')
        run([python, '-B', '-m', 'pip', 'check'], profile['id'] + '-pip-check')
        actual = json.loads(subprocess.check_output(
            [str(python), '-B', '-m', 'pip', 'list', '--format=json',
             '--disable-pip-version-check'], env=environment))
        expected = dict(pin.split('==') for pin in profile['packages'])
        normalize = lambda rows: {canonicalize_name(k): v for k, v in rows.items()}
        if normalize({r['name']: r['version'] for r in actual}) != normalize(expected):
            raise ValueError('installed distribution set differs from exact profile')
        actual_version = subprocess.check_output(
            [str(python), '-B', '-c', 'import platform; print(platform.python_version())'],
            env=environment, text=True).strip()
        if actual_version != version:
            raise ValueError('runtime version differs from catalog')
        write_json(folder / 'installed-packages.json', actual)
        runtime_map[profile['id']] = str(python)
    for ident, interpreter in sorted(runtime_map.items()):
        warm_runtime(interpreter, destination / (ident + '-stdlib-cache.json'))
    write_json(output, runtime_map)
    write_json(destination / 'preparation-receipt.json', {
        'schema': 'UDM_CATALOG_RUNTIME_PREPARATION_V3', 'status': 'PREPARED',
        'catalog_sha256': receipt['catalog_sha256'], 'runtimes': runtime_map,
        'target_source_accessed': False, 'native_tests_executed': False})
    return runtime_map


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=HERE.parent / 'ENVIRONMENT_CATALOG.json')
    parser.add_argument('--dest-root', type=Path, default=Path('qualification/runtime-bootstrap'))
    parser.add_argument('--out', type=Path, default=Path('qualification/RUNTIMES.json'))
    parser.add_argument('--audit-freeze', type=Path)
    args = parser.parse_args()
    if args.audit_freeze:
        result = audit_runtime_freeze(json.loads(args.audit_freeze.read_text()))
        write_json(args.out, result)
        print(json.dumps(result, sort_keys=True))
        if result['status'] != 'PASS_FROZEN_RUNTIME_BYTES': raise SystemExit(1)
        return
    print(json.dumps(prepare(args.catalog, args.dest_root, args.out), sort_keys=True))


if __name__ == '__main__':
    main()
