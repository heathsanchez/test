"""Read-only synthetic metadata probes; zero Git/network/native operations."""
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path('/workspace/udm-v54')
sys.path.insert(0, str(ROOT))
from research.unified_consequence_runtime import native_environment_selection_v4 as v4
from research.unified_consequence_runtime import native_environment_selection_v41 as v41

OUT = Path(__file__).resolve().parent
META = b'[project]\nrequires-python=">=3.11,<3.13"\n'
CAT = {'schema': v41.CATALOG_SCHEMA, 'profiles': [{
    'id': 'synthetic', 'python_version': '3.12.14',
    'python_implementation': 'CPython', 'pytest_version': '8.4.1',
    'packages': ['pytest==8.4.1', 'attrs==25.4.0'], 'plugins': []}]}
paths = [ROOT / 'research/unified_consequence_runtime' / name for name in (
    'native_environment_selection_v3.py', 'native_environment_selection_v4.py',
    'native_environment_selection_v41.py', 'native_environment_v3.py',
    'native_environment_v41.py', 'test_native_dependency_includes_v41.py')]
def hashes():
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

rows = []
before = hashes()
def probe(name, module, files):
    started = time.monotonic()
    record = {'name': name, 'metadata_only': True, 'native_calls': 0,
              'network_calls': 0, 'git_calls': 0, 'source_files': len(files)}
    try:
        value = module.select_profile(files, CAT)
        record.update(status=value['status'], reason=value['reason'],
                      constraints_status=value['constraints']['status'],
                      reasons=value['constraints']['reasons'],
                      evidence_count=len(value['constraints']['evidence']),
                      requirement_rows=value['constraints']['requirements'])
    except Exception as error:
        record.update(escaped_exception=type(error).__name__, detail=str(error))
    record['seconds'] = time.monotonic() - started
    rows.append(record)

for label, metadata in (
    ('pyproject', b'[project]\nrequires-python=">=3.11"\ndependencies=["-r deps/root.in"]\n'),
    ('setup_cfg', META),
    ('setup_py', META),
):
    files = {'pyproject.toml': metadata, 'deps/root.in': b'attrs>=25\n'}
    if label == 'setup_cfg':
        files['setup.cfg'] = b'[options]\ninstall_requires=-r deps/root.in\n'
    if label == 'setup_py':
        files['setup.py'] = b'from setuptools import setup\nsetup(install_requires=["-r deps/root.in"])\n'
    probe(label + '_not_activated', v41, files)

files = {'pyproject.toml': META,
         'tox.ini': b'[testenv:py311]\ndeps=-r deps/a.in\n[testenv:py312]\ndeps=-r deps/b.in\n',
         'deps/a.in': b'-r shared.in\n', 'deps/b.in': b'-r shared.in\n',
         'deps/shared.in': b'attrs>=25; python_version=="3.12"\n'}
probe('scoped_shared_marker', v41, files)

for target in ('deps/file:foo.in', 'file:deps.in', 'deps/has#hash.in'):
    files = {'pyproject.toml': META, 'tox.ini': ('[testenv]\ndeps=-r ' + target + '\n').encode(),
             target: b'attrs>=25\n'}
    probe('literal_path_' + target, v41, files)

def chain(count, tox, cycle):
    files = {'pyproject.toml': META}
    if tox:
        files['tox.ini'] = b'[testenv]\ndeps=-r deps/0.in\n'
    else:
        files['requirements-test.txt'] = b'-r deps/0.in\n'
    files.update({'deps/' + str(i) + '.in': (
        ('-r ' + str(i+1) + '.in\n') if i < count-1 else
        ('-r 0.in\n' if cycle else 'attrs>=25\n')).encode() for i in range(count)})
    return files

for count in (100, 1100):
    for cycle in (False, True):
        probe(f'tox_chain_{count}_cycle_{cycle}', v41, chain(count, True, cycle))
        probe(f'known_root_chain_{count}_cycle_{cycle}_v41', v41, chain(count, False, cycle))
        probe(f'known_root_chain_{count}_cycle_{cycle}_v4', v4, chain(count, False, cycle))

after = hashes()
report = {'scope': 'Synthetic metadata-only v4.1 core review; no Git calls or index-audit claim',
          'before_sha256': before, 'after_sha256': after, 'source_unchanged': before == after,
          'native_calls': 0, 'network_calls': 0, 'git_calls': 0, 'probes': rows,
          'total_seconds': sum(row['seconds'] for row in rows)}
(OUT / 'probe-results-and-costs.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'source_unchanged': before == after,
                  'cases': [{k:v for k,v in row.items() if k not in ('requirement_rows',)} for row in rows],
                  'total_seconds': report['total_seconds']}, indent=2))
