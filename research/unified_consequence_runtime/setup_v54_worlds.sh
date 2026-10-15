#!/usr/bin/env bash
# Fresh native worlds only: setup_v54_worlds.sh WORLDS VENV EVIDENCE
set -euo pipefail
if [[ $# -ne 3 ]]; then
  echo 'usage: setup_v54_worlds.sh WORLDS VENV EVIDENCE' >&2
  exit 2
fi

python3.12 - "$@" <<'PY'
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

worlds, venv, evidence = [Path(arg).resolve() for arg in sys.argv[1:]]
pins = {
    'django': ('https://github.com/django/django.git', 'c6be0bf3bb744d234947cefd6def9f31d9655800'),
    'requests': ('https://github.com/psf/requests.git', '8068356288978c4f54661ae6f95afe0e0831885e'),
    'rich': ('https://github.com/Textualize/rich.git', '9d8f9a372cc5916fd4781fec207ced7ddac2f08f'),
}
if venv.exists() or any((worlds/name).exists() for name in pins):
    raise SystemExit('Refusing to alter an existing V54 environment; choose fresh paths.')
if any(worlds/name == evidence or worlds/name in evidence.parents for name in pins):
    raise SystemExit('Evidence must be outside the resettable native worlds.')
worlds.mkdir(parents=True, exist_ok=True)
evidence.mkdir(parents=True, exist_ok=True)
records = []


def run(name, command, cwd, timeout, env=None):
    command = [str(arg) for arg in command]
    record = {'name': name, 'command': command, 'cwd': str(cwd),
              'timeout_seconds': timeout, 'started_at': datetime.now(timezone.utc).isoformat()}
    started = time.monotonic()
    try:
        process = subprocess.run(command, cwd=cwd, env=env,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
        code, output = process.returncode, process.stdout
    except subprocess.TimeoutExpired as exc:
        code, output = 124, (exc.stdout or b'') + b'\nSETUP_TIMEOUT\n'
    logfile = evidence/(name+'.log')
    logfile.write_bytes(output)
    record.update(exit_code=code, elapsed_seconds=round(time.monotonic()-started, 6),
                  log=str(logfile))
    records.append(record)
    (evidence/'command-results.json').write_text(json.dumps(records, indent=2)+'\n')
    print(json.dumps(record), flush=True)
    if code:
        sys.stderr.buffer.write(output)
        raise SystemExit(code if 0 < code < 256 else 1)


for name, (origin, commit) in pins.items():
    run(name+'-clone', ['git','clone','-q',origin,worlds/name], worlds, 60)
    run(name+'-checkout', ['git','checkout','-q',commit], worlds/name, 60)
run('create-venv', [sys.executable,'-m','venv',venv], worlds, 60)
python = venv/'bin/python'
dependencies = {'django': ['-e','.'], 'requests': ['-e','.','pytest<8'],
                'rich': ['-e','.','pytest<8','pytest-cov','attrs','typing-extensions<5']}
for name, arguments in dependencies.items():
    run(name+'-install', [python,'-m','pip','install','-q',*arguments], worlds/name, 120)
run('python-version', [python,'-VV'], worlds, 30)
run('pip-freeze', [python,'-m','pip','freeze','--all'], worlds, 30)
metadata = {}
for name, (origin, commit) in pins.items():
    run(name+'-reset', ['git','reset','--hard','-q','HEAD'], worlds/name, 60)
    run(name+'-clean', ['git','clean','-fdxq'], worlds/name, 60)
    def git(*args):
        return subprocess.check_output(['git','-C',str(worlds/name),*args],
                                       timeout=30, text=True).strip()
    metadata[name] = {'path': str(worlds/name), 'origin': git('remote','get-url','origin'),
                      'expected_commit': commit, 'commit': git('rev-parse','HEAD'),
                      'shallow': git('rev-parse','--is-shallow-repository') == 'true',
                      'status_porcelain': git('status','--porcelain')}
    if metadata[name]['commit'] != commit or metadata[name]['shallow']:
        raise SystemExit(name+' is not a complete clone at its original pin')
(evidence/'worlds.json').write_text(json.dumps(metadata, indent=2)+'\n')
commands = {
    'django-truncate': ('django', [python,'tests/runtests.py',
        'backends.test_utils.TestUtils.test_truncate_name','--verbosity','0'], 40),
    'django-pagination': ('django', [python,'tests/runtests.py',
        'pagination.tests.PaginationTests.test_orphans_value_larger_than_per_page_value',
        '--verbosity','0'], 40),
    'requests-iter-slices': ('requests', ['timeout','7s',python,'-m','pytest','-q',
        'tests/test_utils.py','-k','test_iter_slices'], 12),
    'rich-highlighter': ('rich', [python,'-m','pytest','-q',
        'tests/test_highlighter.py::test_highlight_json_string_only',
        'tests/test_highlighter.py::test_highlight_json_empty_string_only'], 40),
}
env = os.environ.copy()
env['PATH'] = str(venv/'bin')+os.pathsep+env['PATH']
for name, (world, command, timeout) in commands.items():
    run(name, command, worlds/world, timeout, env)
hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
          for path in evidence.iterdir() if path.is_file()}
(evidence/'file-sha256.json').write_text(json.dumps(hashes, indent=2)+'\n')
PY
