#!/usr/bin/env python3
"""Bounded, unsuppressed two-process TypeLookup replay; records raw outcomes."""
import argparse, hashlib, json, os, pathlib, re, signal, subprocess, time

p = argparse.ArgumentParser()
p.add_argument('--executable', required=True)
p.add_argument('--library-dir', required=True)
p.add_argument('--out', required=True)
p.add_argument('--label', required=True)
p.add_argument('--repetitions', type=int, default=5)
a = p.parse_args()
out = pathlib.Path(a.out).resolve(); out.mkdir(parents=True, exist_ok=True)
lib = pathlib.Path(a.library_dir).resolve()
exe = pathlib.Path(a.executable).resolve()
records = []
for trial in range(a.repetitions):
    domain = str(100 + trial)
    env = os.environ.copy()
    env['LD_LIBRARY_PATH'] = str(lib) + ':' + env.get('LD_LIBRARY_PATH', '')
    env['TSAN_OPTIONS'] = f'halt_on_error=0 exitcode=66 log_path={out}/tsan-{trial}'
    children = []; files = []
    started = time.monotonic(); timed_out = False; mappings = {}
    try:
        for role in ('discover', 'announce'):
            if role == 'announce':
                time.sleep(1)
            stream = (out / f'{trial}-{role}.log').open('w'); files.append(stream)
            child = subprocess.Popen(['setarch', os.uname().machine, '-R', str(exe), role, domain], env=env,
                                     stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
            children.append((role, child))
        deadline = started + 45
        while any(c.poll() is None for _, c in children) and time.monotonic() < deadline:
            for role, child in children:
                try:
                    maps = pathlib.Path(f'/proc/{child.pid}/maps').read_text()
                    paths = sorted({line.split()[-1] for line in maps.splitlines() if 'libfastdds.so' in line})
                    if paths:
                        mappings[role] = paths
                except (FileNotFoundError, ProcessLookupError, PermissionError):
                    pass
            time.sleep(.1)
        timed_out = any(c.poll() is None for _, c in children)
    finally:
        for _, child in children:
            if child.poll() is None:
                os.killpg(child.pid, signal.SIGKILL)
            child.wait()
        for stream in files:
            stream.close()
    logs = '\n'.join(f.read_text(errors='replace') for f in out.glob(f'tsan-{trial}.*'))
    discovery = (out / f'{trial}-discover.log').read_text(errors='replace')
    match = re.search(r'TypeLookup discovery: (\d+) writers, (\d+) type objects resolved', discovery)
    mapped_ok = len(mappings) == 2 and all(all(pathlib.Path(x).resolve().parent == lib for x in v) for v in mappings.values())
    record = {'trial': trial, 'label': a.label, 'elapsed_s': round(time.monotonic()-started, 3),
              'exits': {role:c.returncode for role,c in children}, 'timeout': timed_out,
              'writers': int(match[1]) if match else None, 'resolved_types': int(match[2]) if match else None,
              'tsan_warnings': logs.count('WARNING: ThreadSanitizer:'),
              'typelookup_race': 'WARNING: ThreadSanitizer: data race' in logs and 'TypeLookupManager' in logs,
              'mapped_libraries': mappings, 'mapped_ok': mapped_ok}
    records.append(record)
    (out / 'results.json').write_text(json.dumps(records, indent=2)+'\n')
    print(json.dumps(record), flush=True)
# An exit status or timeout alone is never evidence of the targeted race.
if a.label == 'baseline':
    ok = all(not r['timeout'] and r['mapped_ok'] and all(x in (0,66) for x in r['exits'].values()) for r in records) and any(r['typelookup_race'] for r in records)
elif a.label == 'negative-control':
    ok = all(not r['timeout'] and r['mapped_ok'] and r['writers']==200 and r['resolved_types']==0 and r['exits']['discover']==1 and r['exits']['announce']==0 and r['tsan_warnings']==0 for r in records)
else:
    ok = all(not r['timeout'] and r['mapped_ok'] and r['writers']==200 and r['resolved_types']==200 and set(r['exits'].values())=={0} and r['tsan_warnings']==0 for r in records)
(out / 'verdict.json').write_text(json.dumps({'label':a.label,'passed':ok,'boundary':'finite replay; no sanitizer suppressions; no exhaustive concurrency claim'},indent=2)+'\n')
raise SystemExit(0 if ok else 1)
