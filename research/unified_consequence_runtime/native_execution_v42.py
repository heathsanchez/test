"""Typed-source transport over the original independently replayed native worker.

Only the source boundary and its transport sites are versioned. Collection,
required assertions, imports, plugins, outcomes and evidence replay retain the
original controller code objects. This is bounded research authority.
"""
from pathlib import Path
import inspect
from types import FunctionType, SimpleNamespace

from . import native_execution_v3 as previous
from . import native_admission_v42 as admission
from . import native_source_v42 as source

frozen = previous.frozen
SCHEMA = 'UDM_GENERIC_NATIVE_PYTEST_V42'
CERTIFICATE_SCHEMA = 'UDM_NATIVE_ADMISSION_CERTIFICATE_V42'
POLICY_SCHEMA = 'UDM_NATIVE_EXECUTION_POLICY_V42'
ADMISSION_REVISION = '4.2'
canonical, fingerprint, sha256 = previous.canonical, previous.fingerprint, previous.sha256
_LOADED_SOURCE_SHA256 = sha256(Path(__file__).read_bytes())
_DEPENDENCIES = (
    (previous, 'fead622b61319dc21af1ef302a98b42203090bcc997838fc078c71ddc4ea6cd9'),
    (admission, '96671d481728559ea0b7f751d2a7774dd92fef6c5677b24fdd6a81a21b90e92f'),
    (source, 'f16d4a05a6d3fccde048921559ab130872806afc84757ec8da95d7c2193c8b98'),
)


def _runner_hash():
    previous._runner_hash()
    if sha256(Path(__file__).read_bytes()) != _LOADED_SOURCE_SHA256:
        raise ValueError('UNKNOWN_V42_VERIFIER_SOURCE_MUTATION')
    for module, digest in _DEPENDENCIES:
        if sha256(Path(module.__file__).read_bytes()) != digest:
            raise ValueError('UNKNOWN_V42_SOURCE_BOUNDARY_MUTATION')
    source._guard()
    return _LOADED_SOURCE_SHA256


environment_identity = previous.environment_identity
runtime_identity = previous.runtime_identity
host_stdlib = previous.host_stdlib
attempt_snapshot = previous.attempt_snapshot
_BOOTSTRAP, _PLUGINS = previous._BOOTSTRAP, previous._PLUGINS
_ENVIRONMENT = previous._ENVIRONMENT
original = SimpleNamespace(**dict(vars(previous.original), _snapshot=source.snapshot,
                                   source_identity=source.source_identity))
_controller_globals = dict(previous._controller_globals, SCHEMA=SCHEMA,
    CERTIFICATE_SCHEMA=CERTIFICATE_SCHEMA, POLICY_SCHEMA=POLICY_SCHEMA,
    ADMISSION_REVISION=ADMISSION_REVISION, original=original, admission=admission,
    source=source, _runner_hash=_runner_hash)


def _typed_roots(files):
    """Supplement original roots for flat src modules, including file aliases.

    These names assert original source ownership; they confer no import or
    plugin license. The unchanged child refuses installed substitutions.
    """
    roots = set(previous._roots(files))
    roots.update(Path(name).stem for name in files
                 if len(Path(name).parts) == 2 and Path(name).parts[0] == 'src'
                 and Path(name).suffix == '.py')
    return sorted(roots)


_controller_globals['_typed_roots'] = _typed_roots

# Explicitly reviewed transport substitutions in the pinned original controller.
# No Path/subprocess monkeypatch changes its interpretation of source or evidence.
_run_source = inspect.getsource(previous.frozen._run)
_TRANSPORT_SITES = (
    ("        for name,raw in files.items():\n"
     "            if name.endswith(('.pyc','.pyo')):expected.pop(name,None);continue\n"
     "            p=world/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)\n"
     "        for row in manifest:\n"
     "            if row['path'] in expected:(world/row['path']).chmod(int(row['mode'],8)&0o777)\n",
     "        source.validate_candidate(candidate,files,manifest)\n"
     "        source.materialize(world,files,manifest,skip_bytecode=True)\n"
     "        expected={name:raw for name,raw in files.items() if not name.endswith(('.pyc','.pyo'))}\n"),
    ("        mutations=[name for name,raw in expected.items() if not (world/name).is_file()\n"
     "            or (world/name).resolve()!=world/name or (world/name).read_bytes()!=raw]\n",
     "        mutations=source.validate_materialized(world,files,manifest,candidate=candidate,skip_bytecode=True)\n"),
    ('canonical(_roots(files))', 'canonical(_typed_roots(files))'),
)
for _before, _after in _TRANSPORT_SITES:
    if _run_source.count(_before) != 1:
        raise ValueError('UNKNOWN_V42_NATIVE_TRANSPORT_BINDING_SITE')
    _run_source = _run_source.replace(_before, _after)
exec(compile(_run_source, __file__+':typed-native-transport', 'exec'), _controller_globals)
_controller_run = _controller_globals['_run']

for _name in ('_context', '_roots', '_collection', '_binding', 'collect',
              'validate_certificate', '_status', 'verify', 'validate_receipt'):
    _function = getattr(previous.frozen, _name)
    _bound = FunctionType(_function.__code__, _controller_globals, _name,
                          _function.__defaults__, _function.__closure__)
    _bound.__kwdefaults__ = _function.__kwdefaults__
    globals()[_name] = _controller_globals[_name] = _bound
_controller_context = _context


def _context(contract, authority, policy):
    _runner_hash()
    result = _controller_context(contract, authority, policy)
    source.require_executable(result[1])
    return result


def _run(contract, files, manifest, environment, plugins, out, mode, seconds, candidate):
    _runner_hash()
    source.require_executable(manifest)
    token = previous._attempt_mode.set(mode)
    try:
        return _controller_run(contract, files, manifest, environment, plugins,
                               out, mode, seconds, candidate)
    finally:
        previous._attempt_mode.reset(token)


_controller_globals.update(_context=_context, _run=_run)
_runner_hash()
