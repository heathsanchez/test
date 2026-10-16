"""Portable child scripts over the byte-identical, frozen v2 native controller.

Portable child scripts, host identity checks, and attempt accounting bind v3.
The qualified collection, execution, evidence, and independent replay algorithms
are bound unchanged into a private globals dictionary; old modules are untouched.
"""
from contextvars import ContextVar
from pathlib import Path
from types import FunctionType, SimpleNamespace

from . import native_execution_v2 as frozen

SCHEMA = 'UDM_GENERIC_NATIVE_PYTEST_V3'
CERTIFICATE_SCHEMA = 'UDM_NATIVE_ADMISSION_CERTIFICATE_V3'
POLICY_SCHEMA = 'UDM_NATIVE_EXECUTION_POLICY_V3'
ADMISSION_REVISION = '3.1'
canonical = frozen.canonical
fingerprint = frozen.fingerprint
sha256 = frozen.sha256
admission = frozen.admission
_LOADED_SOURCE_SHA256 = sha256(Path(__file__).read_bytes())
_FROZEN_SOURCE_PINS = {
    'native_execution_v2.py': '57e2fb40c6ff39f0959764e8f48f05ee99170b97995f9a584aaa8409af8871f1',
    'decisive_native_verify.py': '12269c8ca2dd586ccec4b162736375bcaac5717aaf07f441b67e5511b0ed4670',
    'native_admission_v2.py': '4056cb0fd40af3badbe41225919e660d560cac7bb2fda25580399e865778977e',
}


def _runner_hash():
    if sha256(Path(__file__).read_bytes()) != _LOADED_SOURCE_SHA256:
        raise ValueError('UNKNOWN_VERIFIER_SOURCE_MUTATION')
    for module, filename in ((frozen, 'native_execution_v2.py'),
                             (frozen.original, 'decisive_native_verify.py'),
                             (admission, 'native_admission_v2.py')):
        pin = _FROZEN_SOURCE_PINS[filename]
        if (sha256(Path(module.__file__).read_bytes()) != pin
                or getattr(module, '_LOADED_SOURCE_SHA256', pin) != pin):
            raise ValueError('UNKNOWN_FROZEN_SOURCE_MUTATION')
    return _LOADED_SOURCE_SHA256


def _replace(source, before, after):
    """Fail closed if the pinned script no longer has its reviewed edit site."""
    if source.count(before) != 1:
        raise ValueError('UNKNOWN_PORTABLE_SOURCE_ADAPTER')
    return source.replace(before, after)


_runner_hash()
_METADATA = '''try:
    import importlib.metadata as md
except ImportError:
    import importlib_metadata as md'''
_RUNTIME_HELPER = '''import os,sysconfig
def h(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def runtime_import_roots():
    return [sysconfig.get_path('stdlib'),sysconfig.get_path('platstdlib'),sysconfig.get_config_var('DESTSHARED')]
def stdlib_files(roots):
    paths=set()
    for location in sorted({p for p in roots if p}):
        root=pathlib.Path(location)
        if root.is_symlink():raise RuntimeError('UNKNOWN_RUNTIME_SYMLINK_DIRECTORY')
        root=root.resolve()
        for folder,dirs,files in os.walk(str(root)):
            dirs[:]=sorted(name for name in dirs if name not in ('site-packages','dist-packages'))
            if any(pathlib.Path(folder,name).is_symlink() for name in dirs):
                raise RuntimeError('UNKNOWN_RUNTIME_SYMLINK_DIRECTORY')
            for name in files:
                if name.endswith(('.py','.pyc','.pyo','.so','.pyd','.dll','.dylib')):
                    paths.add(pathlib.Path(folder,name).resolve())
    if not paths:raise RuntimeError('original standard library unavailable')
    return [[str(path),h(path)] for path in sorted(paths)]
def runtime_identity():
    rows=stdlib_files(runtime_import_roots())
    return {'implementation':sys.implementation.name,'version_info':list(sys.version_info),
        'executable_sha256':h(sys.executable),'base_prefix':sys.base_prefix,
        'stdlib_manifest_sha256':hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
'''
_RUNTIME = 'import hashlib,json,pathlib,sys\n' + _RUNTIME_HELPER + '\nprint(json.dumps(runtime_identity(),sort_keys=True))\n'
_ENVIRONMENT = _replace(frozen.original._ENVIRONMENT,
    'import hashlib, importlib.metadata as md, json, pathlib, sys',
    'import hashlib,json,pathlib,sys\n' + _METADATA)
_ENVIRONMENT = _replace(_ENVIRONMENT,
    'def h(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()', _RUNTIME_HELPER)
_ENVIRONMENT = _replace(_ENVIRONMENT, "'distribution_count':len(rows)",
    "'distribution_count':len(rows),'runtime_identity':runtime_identity(),'runtime_import_roots':runtime_import_roots()")
_ENVIRONMENT = _replace(_ENVIRONMENT,
    "if location != pathlib.Path(md.distribution('pytest').locate_file('pytest/__init__.py')).resolve():",
    "if location not in {pathlib.Path(md.distribution('pytest').locate_file(entry)).resolve()\n"
    "                    for entry in md.distribution('pytest').files or []}:")
_PLUGINS = _replace(frozen._PLUGINS,
    'import importlib.util,importlib.metadata as md,json,pathlib,hashlib,sys',
    'import importlib.util,json,pathlib,hashlib,sys\n' + _METADATA)
_BOOTSTRAP = _replace(frozen._BOOTSTRAP,
    'import hashlib,json,pathlib,sys,struct,types,inspect',
    '''import hashlib,json,pathlib,sys,struct,types,inspect
def is_relative_to(path,root):
    try:path.relative_to(root);return True
    except ValueError:return False''')
# Exactly two containment checks need the pre-3.9 pathlib spelling.
if _BOOTSTRAP.count('path.is_relative_to(world)') != 2:
    raise ValueError('UNKNOWN_PORTABLE_SOURCE_ADAPTER')
_BOOTSTRAP = _BOOTSTRAP.replace('path.is_relative_to(world)', 'is_relative_to(path,world)')
_BOOTSTRAP = _replace(_BOOTSTRAP, 'path=pathlib.Path(item.path).resolve()',
    "path=pathlib.Path(item.path if hasattr(item,'path') else item.fspath).resolve()")
_BOOTSTRAP = _replace(_BOOTSTRAP,
    '    def pytest_plugin_registered(self,plugin,plugin_name,manager):',
    '''    def pytest_plugin_registered(self,plugin,manager):
        plugin_name=manager.get_name(plugin)''')
_BOOTSTRAP = _replace(_BOOTSTRAP, '    def clean(c):',
    '''    def field(c,name):
        if not hasattr(c,name):return ['absent-code-field',name]
        result=getattr(c,name)
        return result.hex() if isinstance(result,bytes) else result
    def clean(c):''')
for _field in ('co_posonlyargcount', 'co_qualname', 'co_linetable', 'co_exceptiontable'):
    _before = 'c.' + _field + ('.hex()' if _field in ('co_linetable', 'co_exceptiontable') else '')
    _BOOTSTRAP = _replace(_BOOTSTRAP, _before, "field(c,'" + _field + "')")
_BOOTSTRAP = _replace(_BOOTSTRAP, "field(c,'co_exceptiontable')]",
    "field(c,'co_exceptiontable'),field(c,'co_lnotab') if not hasattr(c,'co_linetable') "
    "else ['superseded-code-field','co_lnotab','co_linetable']]")

_environment_globals = dict(vars(frozen.original), _ENVIRONMENT=_ENVIRONMENT)
_portable_environment_identity = FunctionType(frozen.original.environment_identity.__code__,
    _environment_globals, 'environment_identity', frozen.original.environment_identity.__defaults__)
_host_runtime_globals = dict(hashlib=frozen.original.hashlib, json=frozen.json,
                            pathlib=SimpleNamespace(Path=Path), sys=frozen.original.sys)
exec(_RUNTIME_HELPER, _host_runtime_globals)


def host_stdlib(roots):
    """Hash host-visible library bytes with the exact child inventory helper."""
    _runner_hash()
    return _host_runtime_globals['stdlib_files'](roots)


def environment_identity(interpreter):
    _runner_hash()
    before = sha256(Path(interpreter).read_bytes())
    identity = _portable_environment_identity(interpreter)
    if not (before == sha256(Path(interpreter).read_bytes()) == identity['executable_sha256']
            == identity['runtime_identity']['executable_sha256']):
        raise ValueError('UNKNOWN_ENVIRONMENT_HOST_EXECUTABLE')
    roots = identity.get('runtime_import_roots')
    if (not isinstance(roots, list) or len(roots) != 3
            or any(not isinstance(root, str) or not Path(root).is_absolute() for root in roots)):
        raise ValueError('UNKNOWN_ENVIRONMENT_RUNTIME_IMPORT_ROOTS')
    if fingerprint(host_stdlib(roots)) != identity['runtime_identity']['stdlib_manifest_sha256']:
        raise ValueError('UNKNOWN_ENVIRONMENT_HOST_STDLIB')
    return identity


def runtime_identity(interpreter):
    """Pin the executable and original standard library before pytest exists."""
    _runner_hash()
    result = frozen.subprocess.run([str(interpreter), '-I', '-B', '-c', _RUNTIME],
        env=frozen.original._env('/nonexistent'), capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise RuntimeError('native runtime identity unavailable: ' + result.stderr[-1000:])
    return frozen.json.loads(result.stdout)


# This proxy changes only the child environment script, without changing the old
# verifier module or the globals dictionary used by any old verifier function.
original = SimpleNamespace(**dict(vars(frozen.original), environment_identity=environment_identity))
_attempt_counts = ContextVar('udm_native_v3_attempt_counts', default=(0, 0))
_attempt_mode = ContextVar('udm_native_v3_attempt_mode', default=None)


def attempt_snapshot():
    """Read controller launch attempts even after evidence/source refusal.

    Counters are local to the calling context. Only native worker Popen entries
    are charged; environment and plugin identity subprocesses are separate work.
    Failed process launches are conservatively included as invocation attempts.
    """
    native, collection = _attempt_counts.get()
    return {'native_calls': native, 'collection_calls': collection,
            'subprocess_attempts': native + collection}


def _observed_popen(*args, **kwargs):
    mode = _attempt_mode.get()
    if mode in ('run', 'collect'):
        native, collection = _attempt_counts.get()
        _attempt_counts.set((native + int(mode == 'run'), collection + int(mode == 'collect')))
    return frozen.subprocess.Popen(*args, **kwargs)


_subprocess = SimpleNamespace(**dict(vars(frozen.subprocess), Popen=_observed_popen))
_controller_globals = dict(vars(frozen), SCHEMA=SCHEMA, CERTIFICATE_SCHEMA=CERTIFICATE_SCHEMA,
    POLICY_SCHEMA=POLICY_SCHEMA, ADMISSION_REVISION=ADMISSION_REVISION,
    original=original, subprocess=_subprocess,
    _BOOTSTRAP=_BOOTSTRAP, _PLUGINS=_PLUGINS, _runner_hash=_runner_hash)
_CONTROLLER_FUNCTIONS = ('_context', '_roots', '_run', '_collection', '_binding', 'collect',
    'validate_certificate', '_status', 'verify', 'validate_receipt')
for _name in _CONTROLLER_FUNCTIONS:
    _function = getattr(frozen, _name)
    _bound = FunctionType(_function.__code__, _controller_globals, _name,
                          _function.__defaults__, _function.__closure__)
    _bound.__kwdefaults__ = _function.__kwdefaults__
    globals()[_name] = _controller_globals[_name] = _bound
_controller_context = _context
_controller_run = _run


def _context(contract, authority, policy):
    _runner_hash()
    return _controller_context(contract, authority, policy)


def _run(contract, files, manifest, environment, plugins, out, mode, seconds, candidate):
    token = _attempt_mode.set(mode)
    try:
        return _controller_run(contract, files, manifest, environment, plugins, out, mode, seconds, candidate)
    finally:
        _attempt_mode.reset(token)


_controller_globals['_context'] = _context
_controller_globals['_run'] = _run
