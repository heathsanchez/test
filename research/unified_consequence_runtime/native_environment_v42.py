"""Versioned typed-source transport for the existing environment operation.

Original metadata selection, fixed-package provisioning, build commands and
native authority remain intact. Only tracked materialization and topology
validation sites change; original sources and results are never rewritten.
"""
import inspect
from pathlib import Path
from types import FunctionType, SimpleNamespace

from . import native_environment_v3 as previous
from . import native_environment_selection_v41 as selection
from . import native_execution_v42 as execution
from . import native_admission_v42 as admission
from . import native_source_v42 as source
from . import decisive_task_admission as overlay

canonical, fingerprint, sha256 = previous.canonical, previous.fingerprint, previous.sha256
_LOADED_SHA256 = sha256(Path(__file__).read_bytes())
_SOURCE_PINS = {
    'native_environment_v2.py': '33d6f2a8905d1e1bb054c0f105c9ef92aab3e15adac9f8eee3bb1423cd15732d',
    'native_environment_v3.py': '7d18bc80ab96fdfc2128e5f8211aef5a2d88750a85bad4d5c96bb4b9bbad4501',
    'decisive_task_admission.py': '3420aa367537862bc6e3b221b263d9124cd3761cd0010f7e8eebcb40a2c72648',
    'native_environment_selection_v41.py': '951776b61bcb90df29e106e7555d1bcd972f218744b00faa9a17cc9a4827317a',
}


def _guard():
    if sha256(Path(__file__).read_bytes()) != _LOADED_SHA256:
        raise ValueError('UNKNOWN_V42_ENVIRONMENT_SOURCE_CHANGED')
    for module in (previous, previous.previous, overlay, selection):
        if sha256(Path(module.__file__).read_bytes()) != _SOURCE_PINS[Path(module.__file__).name]:
            raise ValueError('UNKNOWN_V42_FROZEN_ENVIRONMENT_SOURCE_CHANGED')
    previous._guard()
    admission.assert_source_identity()
    source._guard()
    execution._runner_hash()


def _snapshot(repo, commit):
    result = source.snapshot(repo, commit)
    source.require_executable(result[2])
    return result


_overlay_globals = dict(vars(overlay), _snapshot=_snapshot)
_original_overlay = FunctionType(overlay._commit_overlay.__code__, _overlay_globals,
                                 '_commit_overlay', overlay._commit_overlay.__defaults__,
                                 overlay._commit_overlay.__closure__)


def _commit_overlay(repo, base, author_tests):
    _guard()
    _, files, manifest = _snapshot(repo, base)
    source.validate_overlay_paths(repo, files, manifest, author_tests)
    return _original_overlay(repo, base, author_tests)


_v2 = previous.previous
_provision_source = inspect.getsource(_v2.provision)
_TRANSPORT_SITES = (
    ("        for row in base_manifest:\n"
     "            destination = build / row['path']; destination.write_bytes(base_files[row['path']])\n"
     "            destination.chmod(int(row['mode'], 8) & 0o777)\n",
     "        source.materialize(build, base_files, base_manifest, tracked_checkout=True)\n"),
    ("        if any(not (build / name).is_file() or (build / name).read_bytes() != raw for name, raw in base_files.items()):\n"
     "            raise ValueError('native build mutated tracked original source')\n",
     "        source.validate_materialized(build, base_files, base_manifest, strict=True)\n"),
)
for _before, _after in _TRANSPORT_SITES:
    if _provision_source.count(_before) != 1:
        raise ValueError('UNKNOWN_V42_ENVIRONMENT_TRANSPORT_BINDING_SITE')
    _provision_source = _provision_source.replace(_before, _after)
_v2_globals = dict(vars(_v2), _snapshot=_snapshot, _commit_overlay=_commit_overlay,
    tracked_archive=source.tracked_archive, derive_suite_contract=admission.derive_suite_contract,
    execution=execution, source=source)
exec(compile(_provision_source, __file__+':typed-base-build-transport', 'exec'), _v2_globals)
_v2_proxy = SimpleNamespace(**dict(_v2_globals))

# The original V3 bound_provision clones the original V2 code with these private
# dependencies. Its interpreter/package identity and command accounting remain
# unchanged, including independent pinned-package checks after project install.
_namespace = dict(vars(previous), previous=_v2_proxy, selection=selection,
                  execution=execution, _snapshot=source.snapshot, _guard=_guard)
for _name, _function in vars(previous).items():
    if (isinstance(_function, FunctionType)
            and _function.__module__ == previous.__name__ and _name != '_guard'):
        _bound = FunctionType(_function.__code__, _namespace, _name,
                              _function.__defaults__, _function.__closure__)
        _bound.__kwdefaults__ = _function.__kwdefaults__
        _namespace[_name] = _bound
        globals()[_name] = _bound
_original_provision = _namespace['provision']


def provision(spec, root, protocol_binding, *, catalog, runtimes,
              collection_seconds=60, execution_seconds=600):
    _guard()
    result = _original_provision(spec, root, protocol_binding,
        catalog=catalog, runtimes=runtimes,
        collection_seconds=collection_seconds, execution_seconds=execution_seconds)
    result = dict(result, schema='UDM_SOURCE_ENVIRONMENT_ADMISSION_V42',
        typed_source_operation={'environment_sha256': _LOADED_SHA256,
            'source_sha256': sha256(Path(source.__file__).read_bytes()),
            'admission_sha256': sha256(Path(admission.__file__).read_bytes()),
            'execution_sha256': execution._runner_hash(),
            'inherited_selection_sha256': _SOURCE_PINS['native_environment_selection_v41.py']})
    (Path(root)/'admission-v42.json').write_text(canonical(result)+'\n')
    return result


_guard()
del _name, _function, _bound, _before, _after
