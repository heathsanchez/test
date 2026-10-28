"""Original native replay plus independently compiled declaration authority.

The new comparison binds protected original source declarations to pytest's
actual outer callables.  Source is compiled, never executed, by the independent
compiler.  Trusted original tests and licensed plugins retain the original
execution ceiling; this operation provides no hostile-process sandbox claim.
"""
from __future__ import annotations

import ast
import base64
import copy
from contextvars import ContextVar
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from types import FunctionType, SimpleNamespace

from . import native_execution_v43 as previous
from . import native_admission_v45 as admission

SCHEMA = 'UDM_GENERIC_NATIVE_PYTEST_V45'
CERTIFICATE_SCHEMA = 'UDM_NATIVE_ADMISSION_CERTIFICATE_V45'
POLICY_SCHEMA = 'UDM_NATIVE_EXECUTION_POLICY_V45'
ADMISSION_REVISION = '4.5'
NAMESPACE_SCHEMA = 'UDM_NATIVE_TEST_NAMESPACE_CERTIFICATE_V45'
source, frozen, original = previous.source, previous.frozen, previous.original
canonical, fingerprint, sha256 = previous.canonical, previous.fingerprint, previous.sha256
_LOADED_SOURCE_SHA256 = sha256(Path(__file__).read_bytes())
_PREVIOUS_SHA256 = '7d449419909c94ce6186d984545ce218c15ee97dc407104bd4e903180c564827'
_compilations = ContextVar('udm_native_v45_original_declaration_compilations', default=())


def _runner_hash():
    previous._runner_hash()
    if sha256(Path(previous.__file__).read_bytes()) != _PREVIOUS_SHA256:
        raise ValueError('UNKNOWN_V45_FROZEN_NATIVE_SOURCE_CHANGED')
    if sha256(Path(__file__).read_bytes()) != _LOADED_SOURCE_SHA256:
        raise ValueError('UNKNOWN_V45_VERIFIER_SOURCE_CHANGED')
    admission.assert_source_identity()
    return _LOADED_SOURCE_SHA256


def _bind(function, namespace):
    result = FunctionType(function.__code__, namespace, function.__name__,
                          function.__defaults__, function.__closure__)
    result.__kwdefaults__ = function.__kwdefaults__
    return result


def _namespace(module, **updates):
    result = dict(vars(module), **updates)
    for name, function in vars(module).items():
        if isinstance(function, FunctionType) and function.__module__ == module.__name__:
            result[name] = _bind(function, result)
    result.update(updates)
    return result


# A private V42 context retains exact original source/environment/plugin checks
# while independently reconstructing V45 static namespace authority.
_typed_globals = dict(previous.previous._controller_globals, admission=admission)
_typed_controller_context = _bind(previous.previous._controller_context, _typed_globals)


def _typed_context(contract, authority, policy):
    result = _typed_controller_context(contract, authority, policy)
    source.require_executable(result[1])
    return result


_typed_execution = SimpleNamespace(**dict(vars(previous.previous), _context=_typed_context))
# Generated artifacts still use the original V43 builder and evidence grammar.
# Rebinding its context avoids dropping V45 namespace evidence or recursing into
# declaration compilation while the original builder reconstructs its base.
_build_globals = _namespace(previous.build, execution=_typed_execution, admission=admission,
                           CONTRACT_SCHEMA=SCHEMA, POLICY_SCHEMA=POLICY_SCHEMA)
build = SimpleNamespace(**_build_globals)

environment_identity, runtime_identity = previous.environment_identity, previous.runtime_identity
host_stdlib, attempt_snapshot = previous.host_stdlib, previous.attempt_snapshot
_PLUGINS, _ENVIRONMENT = previous._PLUGINS, previous._ENVIRONMENT

# The portable, typed code representation is inherited verbatim.  The only
# callable-identity change is refusing to follow user-supplied __wrapped__.
_unwrap = "    while hasattr(obj,'__wrapped__'):obj=obj.__wrapped__\n"
if previous._BOOTSTRAP.count(_unwrap) != 1:
    raise ValueError('UNKNOWN_V45_DIRECT_CALLABLE_BINDING_SITE')
_BOOTSTRAP = previous._BOOTSTRAP.replace(_unwrap, '')
_callable_site = "    obj=getattr(obj,'__func__',obj)\n    code=getattr(obj,'__code__',None)"
if _BOOTSTRAP.count(_callable_site) != 1:
    raise ValueError('UNKNOWN_V45_NATIVE_CALLABLE_TYPE_BINDING_SITE')
_BOOTSTRAP = _BOOTSTRAP.replace(_callable_site,
    '    if _native_type(obj) is _native_method:obj=obj.__func__\n'
    '    code=obj.__code__ if _native_type(obj) is _native_function else None')
if _BOOTSTRAP.count('def code_hash(obj):') != 1:
    raise ValueError('UNKNOWN_V45_NATIVE_CALLABLE_TYPE_CAPTURE_SITE')
_BOOTSTRAP = _BOOTSTRAP.replace('def code_hash(obj):',
    'def code_hash(obj,_native_type=type,_native_function=types.FunctionType,_native_method=types.MethodType):')
_bootstrap_tree = ast.parse(_BOOTSTRAP)
_hash_node = next(node for node in _bootstrap_tree.body
                  if isinstance(node, ast.FunctionDef) and node.name == 'code_hash')
_CODE_HASH_SOURCE = ast.get_source_segment(_BOOTSTRAP, _hash_node)

_compiler_hash = _CODE_HASH_SOURCE.replace(
    '    code=obj.__code__ if _native_type(obj) is _native_function else None', '    code=obj')
_COMPILER = '''
import ast,base64,hashlib,json,pathlib,struct,sys,types
world=pathlib.Path.cwd().resolve()
''' + _compiler_hash + '''
payload=json.loads(pathlib.Path(sys.argv[1]).read_text())
from _pytest.assertion.rewrite import rewrite_asserts
def declaration_code(module, origin):
    current=module
    for name in origin.split('::'):
        matches=[code for code in current.co_consts if type(code) is types.CodeType and code.co_name==name]
        if len(matches)!=1:raise ValueError('ambiguous or missing original compiled declaration: '+origin)
        current=matches[0]
    return current
result={}
for path,row in sorted(payload['sources'].items()):
    raw=base64.b64decode(row['source'],validate=True)
    if hashlib.sha256(raw).hexdigest()!=row['source_sha256']:raise ValueError('original source differs')
    plain=compile(raw,path,'exec',dont_inherit=True)
    tree=ast.parse(raw,filename=path)
    rewrite_asserts(tree,raw,path)
    rewritten=compile(tree,path,'exec',dont_inherit=True)
    for prefix,origin in sorted(row['origins'].items()):
        hashes=sorted(set(code_hash(declaration_code(module,origin))
                          for module in (plain,rewritten)))
        result[prefix]={'path':path,'origin':origin,'source_sha256':row['source_sha256'],'code_sha256':hashes}
pathlib.Path(sys.argv[2]).write_text(json.dumps({'status':'COMPILED_ORIGINAL_DECLARATIONS_WITHOUT_EXECUTION',
    'declarations':result},sort_keys=True,separators=(',',':')))
'''


def declaration_attempt_snapshot():
    """Measured compiler launches, including refused/failed compilation attempts."""
    records = copy.deepcopy(list(_compilations.get()))
    return {'compilation_calls': sum(row['compilation_calls'] for row in records),
            'compilation_seconds': sum(row['seconds'] for row in records), 'records': records}


compilation_snapshot = declaration_attempt_snapshot


def _compile_original_declarations(files, authority, interpreter):
    namespace = authority.get('namespace_certificate') if isinstance(authority, dict) else None
    if (not isinstance(namespace, dict) or set(namespace) != {'schema', 'wildcard_imports', 'required_declarations'}
            or namespace['schema'] != NAMESPACE_SCHEMA or not isinstance(namespace['wildcard_imports'], list)
            or not isinstance(namespace['required_declarations'], dict) or not namespace['required_declarations']):
        raise ValueError('UNKNOWN_V45_MISSING_DECLARATION_AUTHORITY')
    sources = {}
    for prefix, row in namespace['required_declarations'].items():
        if (not isinstance(row, dict) or set(row) != {'path', 'origin', 'source_sha256', 'ast_sha256'}
                or not isinstance(prefix, str) or not isinstance(row['origin'], str)
                or row['path'] not in files or sha256(files[row['path']]) != row['source_sha256']):
            raise ValueError('UNKNOWN_V45_ORIGINAL_DECLARATION_SOURCE')
        tree = ast.parse(files[row['path']], filename=row['path'])
        declaration = tree
        for name in row['origin'].split('::'):
            matches = [node for node in declaration.body
                       if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name]
            if len(matches) != 1:
                raise ValueError('UNKNOWN_V45_ORIGINAL_DECLARATION_ORIGIN')
            declaration = matches[0]
        if not isinstance(declaration, (ast.FunctionDef, ast.AsyncFunctionDef)) or sha256(
                ast.dump(declaration, include_attributes=False).encode()) != row['ast_sha256']:
            raise ValueError('UNKNOWN_V45_ORIGINAL_DECLARATION_AST')
        item = sources.setdefault(row['path'], {'source': base64.b64encode(files[row['path']]).decode(),
                                                'source_sha256': row['source_sha256'], 'origins': {}})
        item['origins'][prefix] = row['origin']
    output = Path(tempfile.mkdtemp(prefix='udm-v45-original-declarations-')).absolute()
    input_path, report_path = output / 'original-input.json', output / 'expected-code.json'
    payload = {'sources': sources}
    input_path.write_text(canonical(payload) + '\n')
    (output / 'compiler.py').write_text(_COMPILER)
    started = time.monotonic()
    record = {'status': 'UNKNOWN', 'compilation_calls': 0, 'seconds': 0.0,
              'interpreter': str(interpreter), 'input_sha256': fingerprint(payload),
              'compiler_sha256': sha256(_COMPILER.encode()), 'output': str(output)}
    try:
        with (output / 'stdout.log').open('wb') as stdout, (output / 'stderr.log').open('wb') as stderr:
            record['compilation_calls'] = 1
            process = subprocess.run([interpreter, '-I', '-B', str(output / 'compiler.py'),
                str(input_path), str(report_path)], cwd=output, env=original._env(output),
                stdout=stdout, stderr=stderr, timeout=60)
        record['process_exit_code'] = process.returncode
        if process.returncode != 0 or not report_path.is_file():
            raise ValueError('UNKNOWN_V45_ORIGINAL_DECLARATION_COMPILATION')
        report = json.loads(report_path.read_bytes())
        if (set(report) != {'status', 'declarations'}
                or report['status'] != 'COMPILED_ORIGINAL_DECLARATIONS_WITHOUT_EXECUTION'
                or set(report['declarations']) != set(namespace['required_declarations'])):
            raise ValueError('UNKNOWN_V45_ORIGINAL_COMPILER_REPORT')
        for prefix, row in report['declarations'].items():
            expected = namespace['required_declarations'][prefix]
            if (set(row) != {'path', 'origin', 'source_sha256', 'code_sha256'}
                    or any(row[key] != expected[key] for key in ('path', 'origin', 'source_sha256'))
                    or not isinstance(row['code_sha256'], list) or not row['code_sha256']
                    or any(not isinstance(digest, str) or len(digest) != 64 for digest in row['code_sha256'])):
                raise ValueError('UNKNOWN_V45_ORIGINAL_COMPILER_BINDING')
        record['status'] = report['status']
        record['report_sha256'] = sha256(report_path.read_bytes())
        return dict(report, artifacts=str(output), costs=record)
    except (OSError, TypeError, KeyError, SyntaxError, json.JSONDecodeError, subprocess.TimeoutExpired) as error:
        record['error'] = type(error).__name__ + ': ' + str(error)
        raise ValueError('UNKNOWN_V45_ORIGINAL_DECLARATION_COMPILATION') from error
    finally:
        record['seconds'] = time.monotonic() - started
        (output / 'compilation.json').write_text(canonical(record) + '\n')
        _compilations.set(_compilations.get() + (copy.deepcopy(record),))


_realm = dict(previous._controller_globals)
_realm.update(_namespace(previous, previous=_typed_execution, build=build, admission=admission,
                    SCHEMA=SCHEMA, CERTIFICATE_SCHEMA=CERTIFICATE_SCHEMA, POLICY_SCHEMA=POLICY_SCHEMA,
                    ADMISSION_REVISION=ADMISSION_REVISION, _BOOTSTRAP=_BOOTSTRAP, _runner_hash=_runner_hash,
                    _build_records=ContextVar('udm_native_v45_build_records', default=())))
# Rebind local V43 helpers to the complete original controller namespace.
for _name, _function in vars(previous).items():
    if isinstance(_function, FunctionType) and _function.__module__ == previous.__name__:
        _realm[_name] = _bind(_function, _realm)
_realm['_runner_hash'] = _runner_hash
_generated_context = _bind(previous._context, _realm)


def _context(contract, authority, policy):
    files, manifest, environment, plugins = _generated_context(contract, authority, policy)
    compiled = _compile_original_declarations(previous._tracked(files), authority, contract['interpreter'])
    previous._tracked(files).original_declaration_compilation = compiled
    previous._tracked(files).namespace_authority = copy.deepcopy(authority)
    return files, manifest, environment, plugins


def _check_declarations(data, authority, files):
    tracked = previous._tracked(files)
    compiled = getattr(tracked, 'original_declaration_compilation', None)
    namespace = authority.get('namespace_certificate') if isinstance(authority, dict) else None
    if (not isinstance(compiled, dict) or not isinstance(namespace, dict)
            or namespace.get('schema') != NAMESPACE_SCHEMA
            or set(compiled['declarations']) != set(authority['required_test_nodes'])
            or set(namespace['required_declarations']) != set(authority['required_test_nodes'])):
        raise ValueError('UNKNOWN_V45_MISSING_INDEPENDENT_DECLARATION_COMPILATION')
    for prefix in authority['required_test_nodes']:
        expected = compiled['declarations'][prefix]
        matches = [row for row in data.get('test_items', []) if isinstance(row, dict)
                   and (row.get('nodeid') == prefix or row.get('nodeid', '').startswith(prefix + '[')
                        or row.get('nodeid', '').startswith(prefix + '::'))]
        if not matches or any(row.get('path') != expected['path']
                or row.get('sha256') != expected['source_sha256']
                or row.get('code_sha256') not in expected['code_sha256'] for row in matches):
            raise ValueError('UNKNOWN_V45_DIRECT_DECLARATION_BINDING: ' + prefix)


def _collection(data, authority, files):
    result = previous._collection(data, authority, files)
    _check_declarations(data, authority, files)
    return result


def _validate_candidate(candidate, files):
    tracked = previous._tracked(files)
    authority = getattr(tracked, 'namespace_authority', None)
    if authority is None:
        raise ValueError('UNKNOWN_V45_CANDIDATE_NAMESPACE_AUTHORITY')
    admission.revalidate_candidate_namespace(candidate, tracked, authority)
    return admission.validate_candidate(candidate, tracked)


_admission = SimpleNamespace(**dict(vars(admission), validate_candidate=_validate_candidate))
_realm.update(_context=_context, _collection=_collection, admission=_admission,
              _validate_candidate=_validate_candidate)
_controller_run = _bind(previous._controller_run, _realm)
for _name in ('_roots', '_binding', 'collect', '_status', 'verify'):
    globals()[_name] = _realm[_name] = _bind(getattr(frozen, _name), _realm)
_controller_validate_certificate = _bind(frozen.validate_certificate, _realm)
_controller_validate_receipt = _bind(frozen.validate_receipt, _realm)


def _run(contract, files, manifest, environment, plugins, out, mode, seconds, candidate):
    _runner_hash()
    _validate_candidate(candidate, files)
    token = previous.previous.previous._attempt_mode.set(mode)
    try:
        result = _controller_run(contract, files, manifest, environment, plugins,
                                 out, mode, seconds, candidate)
        compiled = previous._tracked(files).original_declaration_compilation
        retained = Path(out) / 'original-declaration-compiler'
        retained.mkdir()
        for path in Path(compiled['artifacts']).iterdir():
            if path.is_file():
                shutil.copyfile(path, retained / path.name)
        (Path(out) / 'original-declaration-compilation.json').write_text(canonical(
            dict(compiled, retained_artifacts=str(retained.absolute()))) + '\n')
        return result
    finally:
        previous.previous.previous._attempt_mode.reset(token)


def validate_certificate(contract, authority, certificate, *, policy, output_dir=None):
    return _realm['_v43_validate_certificate'](contract, authority, certificate,
                                               policy=policy, output_dir=output_dir)


def validate_receipt(contract, candidate, authority, certificate, receipt, *, policy,
                     output_dir=None, independent=True):
    files, _, _, _ = _context(contract, authority, policy)
    try:
        _check_declarations(certificate['collection'], authority, files)
        _check_declarations(receipt['execution'], authority, files)
    except (KeyError, TypeError) as error:
        raise ValueError('UNKNOWN_V45_MISSING_DECLARATION_RECEIPT') from error
    return _realm['_v43_validate_receipt'](contract, candidate, authority, certificate, receipt,
        policy=policy, output_dir=output_dir, independent=independent)


_realm.update(_run=_run, _controller_run=_controller_run,
    _controller_validate_certificate=_controller_validate_certificate,
    _controller_validate_receipt=_controller_validate_receipt,
    _v43_validate_certificate=_bind(previous.validate_certificate, _realm),
    _v43_validate_receipt=_bind(previous.validate_receipt, _realm),
    validate_certificate=validate_certificate, validate_receipt=validate_receipt)
build_snapshot = _realm['build_snapshot']
_runner_hash()
