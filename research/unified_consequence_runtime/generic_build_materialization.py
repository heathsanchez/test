"""Source-pinned PEP517 build witness, never a scientific outcome warrant.

Derived from 35d79943 generic_build_materialization.py. The original pip wheel
operation is retained. This seam additionally retains its wheel and rebuilds
from immutable Git bytes without dependency resolution or build isolation.
Backend packages must already exist in the frozen interpreter. Generated build
metadata requiring unavailable Git history remains UNKNOWN; no sandbox claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

SCHEMA = 'UDM_AUTHENTICATED_GENERATED_WHEEL_V2'
BUILD_RECIPE = {'schema':'UDM_IMMUTABLE_PEP517_BUILD_V1',
    'source':'exact regular tracked Git files; no worktree extras or Git metadata',
    'command':['-I','-m','pip','--isolated','wheel','--use-pep517','--no-deps',
               '--no-build-isolation','--no-index','--no-cache-dir'],
    'dependencies':'externally prepared interpreter; no dependency installation',
    'comparison':'all normalized wheel member bytes; ZIP timestamps excluded'}


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def recipe_digest():
    return hashlib.sha256(json.dumps(BUILD_RECIPE,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def command(argv, *, cwd=None, timeout=300):
    started=time.monotonic()
    result = subprocess.run(argv, cwd=cwd, text=True, capture_output=True,
                            timeout=timeout, check=False)
    report={'argv':argv,'returncode':result.returncode,'seconds':time.monotonic()-started,
            'stdout_tail':result.stdout[-4000:],'stderr_tail':result.stderr[-4000:]}
    if result.returncode:
        raise RuntimeError('UNKNOWN_BUILD_EXECUTION: '+json.dumps(report,sort_keys=True))
    return report


def materialize_files(source_files, destination, *, source_commit, source_tree_sha256,
                      python=sys.executable, timeout=300, environment_sha256=None,
                      source_manifest=()):
    """Perform a fresh build; callers must supply independently snapshotted Git bytes."""
    from .generic_native_verify import _path, environment_identity, fingerprint
    from .generated_overlay_gate import wheel_content_digest
    started=time.monotonic()
    destination=Path(destination).absolute()
    if destination.resolve()!=destination or (destination.exists() and any(destination.iterdir())):
        raise ValueError('build destination must be canonical and empty')
    if 'pyproject.toml' not in source_files:
        raise ValueError('UNKNOWN_BUILD_CONTRACT: no pyproject.toml')
    destination.mkdir(parents=True,exist_ok=True)
    environment=environment_identity(python)
    environment_digest=fingerprint(environment)
    if environment_sha256 is not None and environment_sha256!=environment_digest:
        raise ValueError('build environment identity mismatch')
    wheelhouse=destination/'wheels';wheelhouse.mkdir()
    with tempfile.TemporaryDirectory(prefix='native-build-') as folder:
        source=Path(folder)/'source';source.mkdir()
        for name,raw in source_files.items():
            _path(name)
            if not isinstance(raw,bytes):raise ValueError('source build requires exact bytes')
            if name.endswith(('.pyc','.pyo')):continue
            path=source/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        for row in source_manifest:
            if row['path'] in source_files and not row['path'].endswith(('.pyc','.pyo')):
                (source/row['path']).chmod(int(row['mode'],8)&0o777)
        attempt={'schema':'udm.generic-build-attempt.v1','build_calls':1,
                 'source_commit':source_commit,'source_tree_sha256':source_tree_sha256,
                 'status':'STARTED'}
        (destination/'build-attempt.json').write_text(json.dumps(attempt,sort_keys=True)+'\n')
        build_started=time.monotonic()
        try:
            build=command([str(python),*BUILD_RECIPE['command'],'--wheel-dir',str(wheelhouse),str(source)],timeout=timeout)
            attempt['status']='BUILD_COMMAND_PASS'
        except (RuntimeError,subprocess.TimeoutExpired) as error:
            attempt.update(status='UNKNOWN_BUILD_EXECUTION',error=str(error))
            raise
        finally:
            attempt['build_seconds']=time.monotonic()-build_started
            attempt['total_seconds']=time.monotonic()-started
            (destination/'build-attempt.json').write_text(json.dumps(attempt,sort_keys=True)+'\n')
    wheels=sorted(wheelhouse.glob('*.whl'))
    if len(wheels)!=1 or any(p.is_symlink() or not p.is_file() for p in wheels):
        raise ValueError('UNKNOWN_BUILD_OUTPUT: expected one regular wheel')
    if fingerprint(environment_identity(python))!=environment_digest:
        raise ValueError('build modified independently frozen environment')
    wheel=wheels[0]
    evidence={'schema':SCHEMA,'source_commit':source_commit,'source_tree_sha256':source_tree_sha256,
              'wheel_path':str(wheel),'wheel_sha256':sha256(wheel),
              'wheel_content_sha256':wheel_content_digest(wheel),
              'build_recipe_sha256':recipe_digest(),'build_environment_sha256':environment_digest,
              'builder_sha256':sha256(__file__)}
    report={'schema':'udm.generic-build-materialization.v2','status':'BUILT_NOT_SCIENTIFICALLY_VERIFIED',
            'source_commit':source_commit,'source_tree_sha256':source_tree_sha256,
            'source_pyproject_sha256':hashlib.sha256(source_files['pyproject.toml']).hexdigest(),
            'wheel_filename':wheel.name,'wheel_sha256':evidence['wheel_sha256'],
            'interpreter':str(python),'build':build,'generated_wheel_evidence':evidence,
            'costs':{'build_calls':1,'build_seconds':build['seconds'],'total_seconds':time.monotonic()-started,
                     'wheel_bytes':wheel.stat().st_size},
            'limitations':['build backend executes source-controlled code',
                           'wheel build does not verify protected native outcomes',
                           'backend packages must already exist; Git metadata is not materialized',
                           'no all-effects reference monitor or arbitrary upstream build proof']}
    (destination/'build-receipt.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def materialize(source, destination, *, python=sys.executable, timeout=300, source_commit=None):
    """Build exact Git source and retain the actual wheel beside its receipt."""
    from .generic_native_verify import _snapshot
    source=Path(source).absolute();destination=Path(destination).absolute()
    if destination==source or source in destination.parents or destination in source.parents:
        raise ValueError('source/output overlap')
    if source_commit is None:
        source_commit=subprocess.check_output(['git','--no-replace-objects','-C',str(source),'rev-parse','HEAD'],text=True).strip()
    identity,files,manifest=_snapshot(source,source_commit)
    return materialize_files(files,destination,source_commit=source_commit,
        source_tree_sha256=identity['tracked_tree_sha256'],python=python,timeout=timeout,
        source_manifest=manifest)


def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True)
    p.add_argument('--python',default=sys.executable);p.add_argument('--commit')
    args=p.parse_args()
    print(json.dumps(materialize(args.source,args.out,python=args.python,source_commit=args.commit),indent=2))

if __name__=='__main__':main()
