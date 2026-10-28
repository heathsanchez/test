"""Source-only closed wildcard authority over the frozen V42/V2 derivation.

Only direct inert production namespaces are extended. Imported/reexported
origins, executable initializers, general namespace writes and ordering hooks
remain UNKNOWN. Declaration witnesses authorize no execution by themselves.
"""
from __future__ import annotations

import ast
import copy
import inspect
from pathlib import Path, PurePosixPath
import re
from types import FunctionType, SimpleNamespace

from . import native_admission_v42 as previous

# Retain the predecessor's public and private helper surface for consumers.
for _name, _value in vars(previous).items():
    if isinstance(_value, FunctionType):
        globals()[_name] = _value

SCHEMA = 'UDM_NATIVE_SUITE_AUTHORITY_V45'
NAMESPACE_SCHEMA = 'UDM_NATIVE_TEST_NAMESPACE_CERTIFICATE_V45'
CONFIG_SCHEMA = previous.CONFIG_SCHEMA
canonical, fingerprint, sha256 = previous.canonical, previous.fingerprint, previous.sha256
source = previous.source
_PREVIOUS_SHA256 = '96671d481728559ea0b7f751d2a7774dd92fef6c5677b24fdd6a81a21b90e92f'
_LOADED_SOURCE_SHA256 = sha256(Path(__file__).read_bytes())
_PRIMITIVES = {'globals', 'locals', 'vars', 'setattr', 'delattr', 'exec', 'eval'}


def assert_source_identity():
    previous.assert_source_identity()
    if sha256(Path(previous.__file__).read_bytes()) != _PREVIOUS_SHA256:
        raise ValueError('UNKNOWN_V45_FROZEN_ADMISSION_SOURCE_CHANGED')
    if sha256(Path(__file__).read_bytes()) != _LOADED_SOURCE_SHA256:
        raise ValueError('UNKNOWN_V45_ADMISSION_SOURCE_CHANGED')


def _unknown(reason):
    raise ValueError('UNKNOWN_SUITE_CONTRACT: ' + reason)


def _protected(name, config):
    return (previous._matches(name, config['function_patterns'] + config['class_patterns'] + ['test', 'Test'])
            or name.startswith('pytest_') or name in _PRIMITIVES)


def _literal(node):
    try:
        ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        _unknown('nonliteral production namespace binding unsupported')


def _plain_function(node):
    if node.decorator_list:
        _unknown('production decorator namespace effect unsupported')
    annotations = [arg.annotation for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs]
    annotations += [node.returns]
    if node.args.vararg:
        annotations.append(node.args.vararg.annotation)
    if node.args.kwarg:
        annotations.append(node.args.kwarg.annotation)
    for expression in node.args.defaults + node.args.kw_defaults + annotations:
        if expression is not None:
            _literal(expression)


def _closed_exports(raw, path, config):
    """Enumerate plain local declarations, never evaluate an imported module."""
    try:
        tree = ast.parse(raw, filename=path)
    except (SyntaxError, UnicodeError, ValueError) as error:
        raise ValueError('UNKNOWN_SUITE_CONTRACT: authoritative production Python unsupported: ' + path) from error
    names = set(); all_names = None; plain_classes = {'object'}

    def bind(name, *, literal_all=False):
        if name in names:
            _unknown('duplicate production namespace binding unsupported')
        if (_protected(name, config)
                or name == '__all__' and not literal_all
                or name.startswith('__') and name.endswith('__') and name not in ('__all__', '__doc__')):
            _unknown('protected or dynamic production export unsupported')
        names.add(name)

    def assignment(node, *, module):
        nonlocal all_names
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if any(not isinstance(target, ast.Name) for target in targets):
            _unknown('production namespace write unsupported')
        if isinstance(node, ast.AnnAssign) and node.annotation is not None:
            _literal(node.annotation)
        _literal(node.value)
        for target in targets:
            if module:
                bind(target.id, literal_all=target.id == '__all__')
            if target.id == '__all__':
                if not module or len(targets) != 1:
                    _unknown('unsupported export protocol')
                value = ast.literal_eval(node.value)
                if (not isinstance(value, (list, tuple)) or any(not isinstance(name, str)
                        or not name.isidentifier() for name in value) or len(set(value)) != len(value)):
                    _unknown('nonliteral or duplicate export protocol unsupported')
                all_names = list(value)

    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue
        if isinstance(node, ast.Pass):
            continue
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            assignment(node, module=True)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            bind(node.name); _plain_function(node)
        elif isinstance(node, ast.ClassDef):
            bind(node.name)
            if (node.decorator_list or node.keywords or any(not isinstance(base, ast.Name)
                    or base.id not in plain_classes for base in node.bases)):
                _unknown('opaque production class initialization unsupported')
            for statement in node.body:
                if isinstance(statement, ast.Pass):
                    continue
                if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str):
                    continue
                if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if statement.name in ('__init_subclass__', '__class_getitem__'):
                        _unknown('production class initialization hook unsupported')
                    _plain_function(statement)
                elif isinstance(statement, (ast.Assign, ast.AnnAssign)):
                    assignment(statement, module=False)
                else:
                    _unknown('effectful production class initialization unsupported')
            plain_classes.add(node.name)
        else:
            # Named imports are reexports too: origin closure is outside this subset.
            _unknown('production import/reexport or initializer effect unsupported')
    exports = sorted(name for name in names if not name.startswith('_')) if all_names is None else sorted(all_names)
    if any(name not in names or _protected(name, config) for name in exports):
        _unknown('unresolved or protected export protocol unsupported')
    return exports


def _route(module, files, config):
    if not isinstance(module, str) or not re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*', module):
        _unknown('absolute original production module required')
    parts = module.split('.'); candidates = []
    for root in ('', 'src/'):
        stem = root + '/'.join(parts)
        candidates += [(root, path) for path in (stem + '.py', stem + '/__init__.py') if path in files]
    if len(candidates) != 1:
        _unknown('unresolved or ambiguous flat/src production module')
    root, target = candidates[0]
    alternate = 'src/' if root == '' else ''
    for index in range(1, len(parts) + 1):
        stem = alternate + '/'.join(parts[:index])
        if stem + '.py' in files or stem + '/__init__.py' in files:
            _unknown('ambiguous original production import route')
    paths = []
    for index in range(1, len(parts)):
        stem = root + '/'.join(parts[:index])
        initializer = stem + '/__init__.py'
        if initializer not in files or stem + '.py' in files:
            _unknown('unresolved original production package initializer')
        paths.append(initializer)
    paths.append(target)
    rows = {row['path']: row for row in files.manifest}
    route = []
    for path in paths:
        if (path not in rows or rows[path]['mode'] not in ('100644', '100755')
                or previous._test_scope(path, config)
                or any(path == item.rstrip('/') or path.startswith(item.rstrip('/') + '/')
                       for item in config['ini_options'].get('testpaths', []) if item != '.')):
            _unknown('production wildcard route has test source or unsupported source kind')
        _closed_exports(files[path], path, config)
        route.append({'path': path, 'source_sha256': sha256(files[path]),
                      'mode': rows[path]['mode'], 'git_blob': rows[path]['blob']})
    return target, route


def _module_bindings(tree):
    names = set()
    def class_globals(node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            return
        if isinstance(node, ast.Global):
            names.update(node.names)
        for child in ast.iter_child_nodes(node):
            class_globals(child)

    def statement(node):
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            names.add(node.id)
        if isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) and node.name:
            names.add(node.name)
        if isinstance(node, ast.MatchMapping) and node.rest:
            names.add(node.rest)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
            expressions = list(node.decorator_list) + node.args.defaults + node.args.kw_defaults
            expressions += [arg.annotation for arg in node.args.posonlyargs + node.args.args + node.args.kwonlyargs]
            expressions.append(node.returns)
            if node.args.vararg:
                expressions.append(node.args.vararg.annotation)
            if node.args.kwarg:
                expressions.append(node.args.kwarg.annotation)
            for expression in expressions:
                if expression is not None:
                    statement(expression)
            return
        if isinstance(node, ast.ClassDef):
            names.add(node.name)
            for child in node.body:
                class_globals(child)
            for expression in node.decorator_list + node.bases + [keyword.value for keyword in node.keywords]:
                statement(expression)
            return
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names.update(alias.asname or alias.name.split('.')[0] for alias in node.names if alias.name != '*')
            return
        for child in ast.iter_child_nodes(node):
            statement(child)
    for node in tree.body:
        statement(node)
    return names


def _derive_realm(files, baseline, config):
    """Each invocation owns all parser state and original function globals."""
    witnesses = {}; declarations = {}; visited = set()
    realm = dict(previous._namespace, SCHEMA=SCHEMA, assert_source_identity=assert_source_identity)
    for name, function in vars(previous.previous).items():
        if (isinstance(function, FunctionType) and function.__module__ == previous.previous.__name__
                and name != 'assert_source_identity'):
            bound = FunctionType(function.__code__, realm, name, function.__defaults__, function.__closure__)
            bound.__kwdefaults__ = function.__kwdefaults__
            realm[name] = bound

    def record(path, prefix, origin, declaration):
        declarations[prefix] = {'path': path, 'origin': origin,
            'source_sha256': sha256(files[path]),
            'ast_sha256': sha256(ast.dump(declaration, include_attributes=False).encode())}

    # Instrument the two original node-emission sites; retain the original C3 algorithm.
    class_source = inspect.getsource(previous.previous._class_test_nodes)
    sites = (
        ("nodes.append(path + '::' + statement.name); routes.add(statement.name)",
         "nodes.append(path + '::' + statement.name); routes.add(statement.name)\n"
         "                _record(path, nodes[-1], statement.name, statement)"),
        ("nodes.append(path + '::' + name + '::' + method)\n                routes.add(ancestor + '::' + method)",
         "nodes.append(path + '::' + name + '::' + method)\n"
         "                _record(path, nodes[-1], ancestor + '::' + method, statement)\n"
         "                routes.add(ancestor + '::' + method)"),
    )
    for before, after in sites:
        if class_source.count(before) != 1:
            _unknown('original C3 declaration instrumentation site changed')
        class_source = class_source.replace(before, after)
    realm['_record'] = record
    exec(compile(class_source, __file__ + ':original-C3-origins', 'exec'), realm)

    def parse(raw, filename='<unknown>', **kwargs):
        tree = ast.parse(raw, filename=filename, **kwargs)
        visited.add(filename)
        occupied = _module_bindings(tree); imported = set()
        for node in tree.body:
            if not isinstance(node, ast.ImportFrom) or not any(alias.name == '*' for alias in node.names):
                continue
            if node.level or len(node.names) != 1:
                _unknown('relative or mixed wildcard import unsupported')
            path, route = _route(node.module, files, config)
            old_path, old_route = _route(node.module, baseline, config)
            if path != old_path or route != old_route:
                _unknown('production namespace changed across author test overlay')
            exports = _closed_exports(files[path], path, config)
            if occupied.intersection(exports) or imported.intersection(exports):
                _unknown('wildcard export collides with original module binding')
            imported.update(exports)
            witness = {'test_path': filename, 'line': node.lineno, 'module': node.module,
                       'path': path, 'source_sha256': sha256(files[path]),
                       'exports': exports, 'route': route}
            witnesses[(filename, node.lineno, node.module)] = witness
            node.names = [ast.alias(name=name) for name in exports]
        return tree

    # Only the original parser's AST input changes. Raw bytes/source snapshots do not.
    parser_globals = dict(realm, ast=SimpleNamespace(**dict(vars(ast), parse=parse)))
    function = realm['_test_nodes']
    node_parser = FunctionType(function.__code__, parser_globals, function.__name__,
                               function.__defaults__, function.__closure__)
    node_parser.__kwdefaults__ = function.__kwdefaults__
    realm['_test_nodes'] = node_parser
    return realm, witnesses, declarations, visited


def derive_suite_contract(repo, base_commit, augmented_commit, protocol_binding, *, repository):
    assert_source_identity()
    _, baseline, _ = previous._snapshot(repo, base_commit)
    _, files, _ = previous._snapshot(repo, augmented_commit)
    config = previous.configuration(files)
    realm, witnesses, declarations, visited = _derive_realm(files, baseline, config)
    # Invoke the original typed-delta wrapper over the original V2 derivation.
    wrapper_globals = dict(vars(previous), _namespace=realm,
                           _original_derive=realm['derive_suite_contract'],
                           assert_source_identity=assert_source_identity)
    wrapper = FunctionType(previous.derive_suite_contract.__code__, wrapper_globals,
                           'derive_suite_contract', previous.derive_suite_contract.__defaults__)
    result = wrapper(repo, base_commit, augmented_commit, protocol_binding, repository=repository)
    current_paths = sorted(visited)
    witnesses.clear(); declarations.clear()
    for path in current_paths:
        if path in files:
            realm['_test_nodes'](path, files[path], function_patterns=config['function_patterns'],
                                 class_patterns=config['class_patterns'])
    required = result['required_test_nodes']
    if any(prefix not in declarations for prefix in required):
        _unknown('original required declaration has no exact C3 origin')
    result['namespace_certificate'] = {'schema': NAMESPACE_SCHEMA,
        'wildcard_imports': [copy.deepcopy(witnesses[key]) for key in sorted(witnesses)],
        'required_declarations': {prefix: copy.deepcopy(declarations[prefix]) for prefix in required}}
    assert_source_identity()
    return result


def validate_suite_contract(contract, authority):
    assert_source_identity()
    if not isinstance(authority, dict) or authority.get('schema') != SCHEMA:
        raise ValueError('wrong V45 native suite authority schema')
    try:
        expected = derive_suite_contract(contract['repo_path'], authority.get('baseline_commit'),
            contract['commit'], contract['protocol_binding'], repository=contract['repository'])
    except (KeyError, TypeError) as error:
        raise ValueError('invalid V45 native suite contract source') from error
    if authority != expected:
        raise ValueError('V45 native suite namespace, original assertions or source differs')
    return fingerprint(expected)


def validate_candidate(candidate, files):
    assert_source_identity()
    return previous.validate_candidate(candidate, files)


def revalidate_candidate_namespace(candidate, files, authority):
    """Conservatively retain original import routes; candidates grant no authority."""
    validate_candidate(candidate, files)
    try:
        certificate = authority['namespace_certificate']
        if authority['schema'] != SCHEMA or certificate['schema'] != NAMESPACE_SCHEMA:
            raise ValueError('wrong namespace schema')
        dependencies = {}
        for witness in certificate['wildcard_imports']:
            for row in witness['route']:
                dependencies[row['path']] = row['source_sha256']
        if any(path not in files or sha256(files[path]) != digest for path, digest in dependencies.items()):
            _unknown('namespace production source identity differs')
        if any(row['path'] in dependencies for row in candidate['replacements']):
            _unknown('candidate changes source-bound wildcard namespace dependency')
    except (KeyError, TypeError) as error:
        raise ValueError('UNKNOWN_SUITE_CONTRACT: missing candidate namespace authority') from error
    return None


assert_source_identity()
del _name, _value
