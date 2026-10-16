"""Finite source-metadata environment choice, without provisioning or execution.

The external catalog supplies all package, interpreter and plugin authority.
This module only constrains that finite catalog; a candidate is no native warrant.
Unsupported or conflicting metadata remains UNKNOWN. No project code is run.
"""
from __future__ import annotations

import ast
import configparser
import hashlib
import json
from pathlib import PurePosixPath, Path
import re
import tomllib

import packaging
from packaging.markers import Variable
from packaging.requirements import InvalidRequirement, Requirement
from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.utils import canonicalize_name
from packaging.version import InvalidVersion, Version


CONSTRAINT_SCHEMA = 'UDM_NATIVE_ENVIRONMENT_CONSTRAINTS_V3'
CATALOG_SCHEMA = 'UDM_NATIVE_ENVIRONMENT_CATALOG_V3'
SELECTION_SCHEMA = 'UDM_NATIVE_ENVIRONMENT_SELECTION_V3'
_SETUP_KEYS = {'python_requires', 'classifiers', 'install_requires', 'extras_require', 'tests_require'}
_TEST_GROUPS = {'test', 'tests', 'testing'}


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _hash(raw):
    return hashlib.sha256(raw).hexdigest()


class _Unknown(ValueError):
    def __init__(self, reason, detail):
        self.reason, self.detail = reason, str(detail)
        super().__init__(reason + ': ' + self.detail)


def _unknown(reason, detail):
    raise _Unknown(reason, detail)


def _path(name):
    if (not isinstance(name, str) or not name or '\\' in name or '\x00' in name
            or PurePosixPath(name).is_absolute() or str(PurePosixPath(name)) != name
            or '..' in PurePosixPath(name).parts):
        _unknown('UNKNOWN_SOURCE_INPUT', 'noncanonical source path')
    return name


def _strings(value, detail):
    if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
        _unknown('UNKNOWN_METADATA_GRAMMAR', detail)
    return value


def _requirement(value):
    try:
        if not isinstance(value, str):
            raise InvalidRequirement('requirement is not text')
        result = Requirement(value)
        if result.url or any(x.operator == '===' for x in result.specifier):
            raise InvalidRequirement('URL or arbitrary equality is not external pin authority')
        return result
    except InvalidRequirement as error:
        _unknown('UNKNOWN_REQUIREMENT_GRAMMAR', str(error))


def _specifier(value):
    try:
        if not isinstance(value, str) or not value.strip():
            raise InvalidSpecifier('nonempty Python version constraint required')
        for spec in SpecifierSet(value):
            if not re.fullmatch(r'[0-9]+(?:\.[0-9]+){0,2}(?:\.\*)?', spec.version):
                raise InvalidSpecifier('unsupported Python release range')
        return value
    except InvalidSpecifier as error:
        _unknown('UNKNOWN_REQUIREMENT_GRAMMAR', str(error))


def _python_witnesses(specifiers, minors=()):
    """Ordinary release interval boundaries provide finite satisfiability witnesses."""
    releases = {(2, 0, 0), (3, 0, 0)}
    for minor in minors:
        releases.add(tuple(map(int, minor.split('.'))) + (0,))
    for value in specifiers:
        for spec in SpecifierSet(value):
            pieces = tuple(map(int, spec.version.removesuffix('.*').split('.')))
            releases.add(pieces + (0,) * (3 - len(pieces)))
    witnesses = set()
    for release in releases:
        witnesses.add(release)
        for index in range(3):
            for delta in (-1, 1):
                if release[index] + delta >= 0:
                    witnesses.add(release[:index] + (release[index] + delta,) + (0,) * (2 - index))
    return [Version('.'.join(map(str, release))) for release in sorted(witnesses)]


def _literal(node, symbols, visiting=()):
    if isinstance(node, ast.Name):
        if node.id not in symbols or node.id in visiting or len(symbols[node.id]) != 1:
            _unknown('UNKNOWN_DYNAMIC_METADATA', 'unresolved or multiply assigned metadata: ' + node.id)
        return _literal(symbols[node.id][0], symbols, (*visiting, node.id))
    if isinstance(node, (ast.List, ast.Tuple)):
        return [_literal(x, symbols, visiting) for x in node.elts]
    if isinstance(node, ast.Dict):
        result = {}
        for key, value in zip(node.keys, node.values):
            if key is None:
                _unknown('UNKNOWN_DYNAMIC_METADATA', 'dynamic dictionary expansion')
            key = _literal(key, symbols, visiting)
            if key in result:
                _unknown('UNKNOWN_DYNAMIC_METADATA', 'duplicate metadata dictionary key')
            result[key] = _literal(value, symbols, visiting)
        return result
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'dict':
        if len(node.args) > 1:
            _unknown('UNKNOWN_DYNAMIC_METADATA', 'unsupported dict constructor')
        result = _literal(node.args[0], symbols, visiting) if node.args else {}
        if not isinstance(result, dict):
            _unknown('UNKNOWN_DYNAMIC_METADATA', 'dictionary metadata required')
        result = dict(result)
        for kw in node.keywords:
            if kw.arg is None:
                _unknown('UNKNOWN_DYNAMIC_METADATA', 'dynamic keyword expansion')
            # Other setup fields (e.g. long_description=open(...)) are not interpreted.
            if kw.arg in _SETUP_KEYS:
                if kw.arg in result:
                    _unknown('UNKNOWN_DYNAMIC_METADATA', 'overridden metadata key: ' + kw.arg)
                result[kw.arg] = _literal(kw.value, symbols, visiting)
        return result
    if isinstance(node, ast.Constant) and isinstance(node.value, (str, int, bool, type(None))):
        return node.value
    _unknown('UNKNOWN_DYNAMIC_METADATA', 'metadata is outside literal AST grammar')


def _setup_metadata(tree):
    symbols = {}
    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    symbols.setdefault(target.id, []).append(node.value)
    setup_names = {'setup'}; module_aliases = {'setuptools': 'setuptools', 'distutils': 'distutils'}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for value in node.names:
                if value.name in ('setuptools', 'distutils', 'distutils.core'):
                    module_aliases[value.asname or value.name.split('.')[0]] = value.name if value.asname else value.name.split('.')[0]
        if isinstance(node, ast.ImportFrom) and node.module in ('setuptools', 'distutils.core'):
            setup_names.update(x.asname or x.name for x in node.names if x.name == 'setup')
        if isinstance(node, ast.ImportFrom) and node.module == 'distutils':
            module_aliases.update({x.asname or x.name: 'distutils.core' for x in node.names if x.name == 'core'})
    def setup_call(node):
        if isinstance(node, ast.Name):
            return node.id in setup_names
        if isinstance(node, ast.Attribute) and node.attr == 'setup':
            value = node.value
            if isinstance(value, ast.Name):
                return module_aliases.get(value.id) in ('setuptools', 'distutils', 'distutils.core')
            return (isinstance(value, ast.Attribute) and value.attr == 'core'
                    and isinstance(value.value, ast.Name) and module_aliases.get(value.value.id) == 'distutils')
        return False
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and setup_call(node.func)]
    if calls and any(name in symbols for name in setup_names | module_aliases.keys()):
        _unknown('UNKNOWN_DYNAMIC_METADATA', 'rebound setup import')
    callable_names = setup_names | module_aliases.keys()
    imported_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_names.extend(x.asname or x.name.split('.')[0] for x in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported_names.extend(x.asname or x.name for x in node.names)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if calls and node.name in callable_names:
                _unknown('UNKNOWN_DYNAMIC_METADATA', 'defined setup authority binding')
        elif isinstance(node, ast.arg) and calls and node.arg in callable_names:
            _unknown('UNKNOWN_DYNAMIC_METADATA', 'parameter shadows setup authority')
        elif (isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del))
              and calls and node.id in callable_names):
            _unknown('UNKNOWN_DYNAMIC_METADATA', 'stored/deleted setup authority binding')
        elif isinstance(node, ast.ExceptHandler) and calls and node.name in callable_names:
            _unknown('UNKNOWN_DYNAMIC_METADATA', 'exception target shadows setup authority')
        elif isinstance(node, (ast.MatchAs, ast.MatchStar)) and calls and node.name in callable_names:
            _unknown('UNKNOWN_DYNAMIC_METADATA', 'pattern target shadows setup authority')
        elif isinstance(node, ast.MatchMapping) and calls and node.rest in callable_names:
            _unknown('UNKNOWN_DYNAMIC_METADATA', 'pattern mapping shadows setup authority')
    if calls and any(imported_names.count(name) > 1 for name in callable_names):
        _unknown('UNKNOWN_DYNAMIC_METADATA', 'reimported setup authority binding')
    records = []
    for call in calls:
        if call.args:
            _unknown('UNKNOWN_DYNAMIC_METADATA', 'positional setup arguments')
        result = {}
        for kw in call.keywords:
            if kw.arg is None:
                values = _literal(kw.value, symbols)
                if not isinstance(values, dict):
                    _unknown('UNKNOWN_DYNAMIC_METADATA', 'setup expansion is not literal mapping')
                values = {k: v for k, v in values.items() if k in _SETUP_KEYS}
            elif kw.arg in _SETUP_KEYS:
                values = {kw.arg: _literal(kw.value, symbols)}
            else:
                continue
            if result.keys() & values.keys():
                _unknown('UNKNOWN_DYNAMIC_METADATA', 'duplicate setup metadata')
            result.update(values)
        records.append(result)
    if records and any(record != records[0] for record in records[1:]):
        _unknown('UNKNOWN_CONFLICTING_METADATA', 'distinct setup metadata calls')
    def references(node):
        if node is None:
            return set()
        if isinstance(node, ast.Name):
            return {node.id}
        if isinstance(node, ast.Call):
            # A constructor name is not an alias of the container it creates.
            children = [*node.args, *(kw.value for kw in node.keywords)]
            if isinstance(node.func, ast.Attribute):
                children.append(node.func.value)
        else:
            children = list(ast.iter_child_nodes(node))
        return set().union(*(references(child) for child in children)) if children else set()

    # Only environment-bearing keyword values seed container-reference tracking.
    relevant_symbols = set().union(*(references(kw.value) for call in calls for kw in call.keywords
                                    if kw.arg is None or kw.arg in _SETUP_KEYS)) if calls else set()
    changed = True
    while changed:
        before = set(relevant_symbols)
        for name in before:
            for value in symbols.get(name, []):
                relevant_symbols.update(references(value))
        for name, values in symbols.items():
            # Subscript/slice/container/copy expressions may retain references to
            # a literal metadata container. Propagate uncertainty through them.
            if any(references(value) & before for value in values):
                relevant_symbols.add(name)
        changed = before != relevant_symbols
    for node in ast.walk(tree):
        # A bounded literal parser cannot follow aliases introduced by arbitrary
        # binding/control constructs. Refuse them whenever metadata may escape.
        unsupported = []
        if isinstance(node, ast.Assign) and any(not isinstance(target, ast.Name) for target in node.targets):
            unsupported.append(node.value)
        elif isinstance(node, ast.AnnAssign) and not isinstance(node.target, ast.Name):
            unsupported.append(node.value)
        elif isinstance(node, ast.AugAssign):
            unsupported.append(node.value)
        elif isinstance(node, ast.NamedExpr):
            unsupported.append(node.value)
        elif isinstance(node, (ast.For, ast.AsyncFor, ast.comprehension)):
            unsupported.append(node.iter)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            unsupported.extend(item.context_expr for item in node.items if item.optional_vars is not None)
        elif isinstance(node, ast.arguments):
            unsupported.extend([*node.defaults, *node.kw_defaults])
        elif isinstance(node, (ast.Return, ast.Yield, ast.YieldFrom)):
            unsupported.append(node.value)
        if any(references(value) & relevant_symbols for value in unsupported):
            _unknown('UNKNOWN_DYNAMIC_METADATA', 'unsupported binding of referenced setup metadata')
        if isinstance(node, ast.Call) and not setup_call(node.func):
            if not (isinstance(node.func, ast.Name) and node.func.id == 'dict'):
                args = [*node.args, *(kw.value for kw in node.keywords)]
                if any(isinstance(x, ast.Name) and x.id in relevant_symbols
                       for arg in args for x in ast.walk(arg)):
                    _unknown('UNKNOWN_DYNAMIC_METADATA', 'unknown call receives setup metadata')
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if references(node.func.value) & relevant_symbols:
                _unknown('UNKNOWN_DYNAMIC_METADATA', 'method call through referenced setup metadata')
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.Delete)):
            targets = node.targets if isinstance(node, (ast.Assign, ast.Delete)) else [node.target]
            for target in targets:
                if any(setup_call(part) for part in ast.walk(target)):
                    _unknown('UNKNOWN_DYNAMIC_METADATA', 'mutated setup callable')
                if isinstance(target, ast.Name) and target.id in relevant_symbols:
                    if isinstance(node, ast.AugAssign):
                        _unknown('UNKNOWN_DYNAMIC_METADATA', 'augmented setup metadata assignment')
                    ancestor = parents.get(node)
                    while ancestor is not None:
                        if isinstance(ancestor, (ast.If, ast.Try, ast.For, ast.While, ast.With, ast.Match)):
                            _unknown('UNKNOWN_DYNAMIC_METADATA', 'conditional setup metadata binding')
                        ancestor = parents.get(ancestor)
                root = target
                while isinstance(root, (ast.Subscript, ast.Attribute)):
                    root = root.value
                if isinstance(node, ast.Delete) and isinstance(root, ast.Name) and root.id in relevant_symbols:
                    _unknown('UNKNOWN_DYNAMIC_METADATA', 'deleted setup metadata')
                if isinstance(target, ast.Subscript) and isinstance(root, ast.Name) and root.id in relevant_symbols:
                    if target.value is not root:
                        _unknown('UNKNOWN_DYNAMIC_METADATA', 'nested setup metadata mutation')
                    try:
                        key = ast.literal_eval(target.slice)
                    except (ValueError, TypeError):
                        _unknown('UNKNOWN_DYNAMIC_METADATA', 'dynamic setup metadata mutation')
                    container = _literal(ast.Name(id=root.id, ctx=ast.Load()), symbols)
                    if not isinstance(container, dict) or not isinstance(key, str) or key in _SETUP_KEYS:
                        _unknown('UNKNOWN_DYNAMIC_METADATA', 'mutated setup metadata field')
    return records[0] if records else {}


def _expand_tox(value):
    if not isinstance(value, str):
        _unknown('UNKNOWN_METADATA_GRAMMAR', 'tox envlist must be text')
    if '{}' in value:
        _unknown('UNKNOWN_METADATA_GRAMMAR', 'empty tox factor')
    # Split commas only outside braces, then expand finite nonnested products.
    tokens = re.findall(r'[^\s,{}]+(?:\{[^{}]*\}[^\s,{}]*)*|\{[^{}]*\}[^\s,{}]*', value)
    compact = re.sub(r'[\s,]', '', value)
    if ''.join(tokens).replace(',', '') != compact:
        _unknown('UNKNOWN_METADATA_GRAMMAR', 'unsupported tox envlist grammar')
    result = []
    for token in tokens:
        expanded = [token]
        while any('{' in x for x in expanded):
            rows = []
            for item in expanded:
                match = re.search(r'\{([^{}]+)\}', item)
                if not match:
                    rows.append(item); continue
                values = []
                for choice in match[1].split(','):
                    interval = re.fullmatch(r'([0-9]+)-([0-9]+)', choice)
                    if interval:
                        lo, hi = map(int, interval.groups())
                        if not 0 <= lo <= hi <= 99:
                            _unknown('UNKNOWN_METADATA_GRAMMAR', 'unbounded tox expansion')
                        values.extend(str(x) for x in range(lo, hi + 1))
                    elif re.fullmatch(r'[A-Za-z0-9_]+', choice):
                        values.append(choice)
                    else:
                        _unknown('UNKNOWN_METADATA_GRAMMAR', 'unsupported tox factor')
                rows.extend(item[:match.start()] + v + item[match.end():] for v in values)
            expanded = rows
            if len(expanded) + len(result) > 512:
                _unknown('UNKNOWN_METADATA_GRAMMAR', 'tox expansion exceeds finite grammar')
        result.extend(expanded)
    return result


def derive_constraints(files):
    """Read conservative literal source metadata and API bounds; never execute it."""
    result = {'schema': CONSTRAINT_SCHEMA, 'status': 'UNKNOWN', 'metadata_sha256': {},
              'source_sha256': None, 'python_specifiers': [], 'declared_python': [],
              'python_implementations': [], 'requirements': [], 'plugin_requirements': [],
              'evidence': [], 'reasons': []}
    matrices, implementations = [], []
    try:
        if not isinstance(files, dict) or any(not isinstance(v, bytes) for v in files.values()):
            _unknown('UNKNOWN_SOURCE_INPUT', 'tracked source byte map required')
        for name in files:
            _path(name)
        result['source_sha256'] = _hash(_canonical({name: _hash(raw) for name, raw in sorted(files.items())}).encode())

        def evidence(path, field, value):
            result['metadata_sha256'][path] = _hash(files[path])
            result['evidence'].append({'path': path, 'field': field, 'value': value})

        def add_requirement(value, path, field, extra='', python_versions=None):
            req = _requirement(value)
            row = {'requirement': str(req), 'path': path, 'field': field, 'extra': extra}
            if python_versions is not None:
                row['python_versions'] = sorted(python_versions, key=Version)
            if row not in result['requirements']:
                result['requirements'].append(row)

        def classifiers(values, path, field):
            values = _strings(values, 'classifiers must be literal strings')
            minors, impls = set(), set()
            for value in values:
                match = re.fullmatch(r'Programming Language :: Python :: ([0-9]+\.[0-9]+)', value)
                if match:
                    minors.add(match[1])
                match = re.fullmatch(r'Programming Language :: Python :: Implementation :: (CPython|PyPy)', value)
                if match:
                    impls.add(match[1])
            if minors:
                matrices.append(minors)
            if impls:
                implementations.append(impls)
            evidence(path, field, values)

        if 'pyproject.toml' in files:
            path = 'pyproject.toml'; data = tomllib.loads(files[path].decode('utf-8'))
            project = data.get('project', {}); build = data.get('build-system', {})
            if not isinstance(project, dict) or not isinstance(build, dict):
                _unknown('UNKNOWN_METADATA_GRAMMAR', 'project/build-system tables required')
            dynamic = project.get('dynamic', [])
            if not isinstance(dynamic, list) or any(x in dynamic for x in ('requires-python', 'dependencies', 'optional-dependencies', 'classifiers')):
                _unknown('UNKNOWN_DYNAMIC_METADATA', 'dynamic environment metadata')
            if 'requires-python' in project:
                value = _specifier(project['requires-python']); result['python_specifiers'].append(value)
                evidence(path, 'project.requires-python', value)
            if 'classifiers' in project:
                classifiers(project['classifiers'], path, 'project.classifiers')
            for field, values in [('build-system.requires', build.get('requires', [])),
                                  ('project.dependencies', project.get('dependencies', []))]:
                for value in _strings(values, field):
                    add_requirement(value, path, field)
                if values:
                    evidence(path, field, values)
            extras = project.get('optional-dependencies', {})
            if not isinstance(extras, dict):
                _unknown('UNKNOWN_METADATA_GRAMMAR', 'optional-dependencies table required')
            for key, values in sorted(extras.items()):
                if canonicalize_name(key) in _TEST_GROUPS:
                    for value in _strings(values, key):
                        add_requirement(value, path, 'project.optional-dependencies.' + key, key)
                    evidence(path, 'project.optional-dependencies.' + key, values)
            groups = data.get('dependency-groups', {})
            if not isinstance(groups, dict):
                _unknown('UNKNOWN_DEPENDENCY_GROUP', 'dependency-groups table required')

            def group(name, stack=()):
                if name not in groups or name in stack or not isinstance(groups[name], list):
                    _unknown('UNKNOWN_DEPENDENCY_GROUP', 'unresolved or cyclic group: ' + str(name))
                for value in groups[name]:
                    if isinstance(value, str):
                        add_requirement(value, path, 'dependency-groups.' + name)
                    elif isinstance(value, dict) and set(value) == {'include-group'} and isinstance(value['include-group'], str):
                        group(value['include-group'], (*stack, name))
                    else:
                        _unknown('UNKNOWN_DEPENDENCY_GROUP', 'unsupported group member')
            for name in sorted(groups):
                if canonicalize_name(name) in _TEST_GROUPS:
                    group(name); evidence(path, 'dependency-groups.' + name, groups[name])

        trees = {}
        for name, raw in sorted(files.items()):
            if name.endswith('.py'):
                try:
                    trees[name] = ast.parse(raw, filename=name)
                except (SyntaxError, ValueError, UnicodeError) as error:
                    _unknown('UNKNOWN_SOURCE_PARSER', name + ': ' + str(error))
        if 'setup.py' in trees:
            data = _setup_metadata(trees['setup.py']); path = 'setup.py'
            if 'python_requires' in data:
                value = _specifier(data['python_requires']); result['python_specifiers'].append(value)
                evidence(path, 'setup.python_requires', value)
            if 'classifiers' in data:
                classifiers(data['classifiers'], path, 'setup.classifiers')
            for key in ('install_requires', 'tests_require'):
                for value in _strings(data.get(key, []), key):
                    add_requirement(value, path, 'setup.' + key)
                if key in data:
                    evidence(path, 'setup.' + key, data[key])
            extras = data.get('extras_require', {})
            if not isinstance(extras, dict):
                _unknown('UNKNOWN_METADATA_GRAMMAR', 'literal extras_require mapping required')
            for key, values in sorted(extras.items()):
                if canonicalize_name(key) in _TEST_GROUPS:
                    for value in _strings(values, key):
                        add_requirement(value, path, 'setup.extras_require.' + key, key)
                    evidence(path, 'setup.extras_require.' + key, values)

        if 'setup.cfg' in files:
            path = 'setup.cfg'; parser = configparser.ConfigParser(interpolation=None)
            parser.read_string(files[path].decode('utf-8'))
            if parser.has_option('options', 'python_requires'):
                value = _specifier(parser.get('options', 'python_requires'))
                result['python_specifiers'].append(value); evidence(path, 'options.python_requires', value)
            if parser.has_option('metadata', 'classifiers'):
                values = [x.strip() for x in parser.get('metadata', 'classifiers').splitlines() if x.strip()]
                classifiers(values, path, 'metadata.classifiers')
            for key in ('install_requires', 'tests_require', 'setup_requires'):
                if parser.has_option('options', key):
                    value = parser.get('options', key)
                    for line in value.splitlines():
                        if line.strip() and not line.strip().startswith('#'):
                            add_requirement(line.strip(), path, 'options.' + key)
                    evidence(path, 'options.' + key, value)
            if parser.has_section('options.extras_require'):
                for extra, value in parser.items('options.extras_require'):
                    if canonicalize_name(extra) in _TEST_GROUPS:
                        for line in value.splitlines():
                            if line.strip() and not line.strip().startswith('#'):
                                add_requirement(line.strip(), path, 'options.extras_require.' + extra, extra)
                        evidence(path, 'options.extras_require.' + extra, value)

        if 'tox.ini' in files:
            path = 'tox.ini'; parser = configparser.ConfigParser(interpolation=None)
            parser.read_string(files[path].decode('utf-8'))
            for key in ('envlist', 'env_list'):
                if parser.has_option('tox', key):
                    value = parser.get('tox', key); minors = set()
                    for env in _expand_tox(value):
                        match = re.match(r'py([23])([0-9]+)(?:-|$)', env)
                        if match:
                            minors.add(match[1] + '.' + str(int(match[2])))
                        elif re.match(r'py(?:[0-9]|-|$)', env):
                            _unknown('UNKNOWN_METADATA_GRAMMAR', 'unversioned or unsupported tox Python environment')
                    if minors:
                        matrices.append(minors)
                    evidence(path, 'tox.' + key, value)
            if parser.has_option('testenv', 'deps'):
                values = parser.get('testenv', 'deps')
                for value in values.splitlines():
                    value = value.strip()
                    if not value or value.startswith('#'):
                        continue
                    # Optional source coverage environment does not license packages.
                    if re.fullmatch(r'\{env:[A-Z_]+:\}', value):
                        continue
                    add_requirement(value, path, 'testenv.deps')
                evidence(path, 'testenv.deps', values)
            for section in parser.sections():
                if not section.startswith('testenv:') or not parser.has_option(section, 'deps'):
                    continue
                minors = set()
                for env in _expand_tox(section[len('testenv:'):]):
                    match = re.match(r'py([23])([0-9]+)(?:-|$)', env)
                    if match:
                        minors.add(match[1] + '.' + str(int(match[2])))
                    elif env.startswith(('py', 'pypy')):
                        _unknown('UNKNOWN_METADATA_GRAMMAR', 'unresolved Python-specific tox dependencies')
                if minors:
                    values = parser.get(section, 'deps')
                    for line in values.splitlines():
                        if line.strip() and not line.strip().startswith('#'):
                            add_requirement(line.strip(), path, section + '.deps', python_versions=minors)
                    evidence(path, section + '.deps', values)

        requirement_roots = {'requirements-test.txt', 'requirements-tests.txt', 'test-requirements.txt',
                             'tests-requirements.txt', 'requirements/test.txt', 'requirements/tests.txt',
                             'requirements/testing.txt', 'tests/requirements.txt'}

        def requirements_file(path, stack=()):
            if path not in files or path in stack:
                _unknown('UNKNOWN_REQUIREMENT_GRAMMAR', 'missing or cyclic requirements include')
            evidence(path, 'test-requirements', _hash(files[path]))
            for line in files[path].decode('utf-8').splitlines():
                line = re.split(r'\s+#', line, 1)[0].strip()
                if not line or line.startswith('#'):
                    continue
                if line.startswith(('-r ', '--requirement ')):
                    included = line.split(None, 1)[1]
                    try:
                        _path(included)
                        target = str(PurePosixPath(path).parent / included); _path(target)
                    except _Unknown:
                        _unknown('UNKNOWN_REQUIREMENT_GRAMMAR', 'noncanonical requirements include')
                    requirements_file(target, (*stack, path))
                elif line.startswith('-'):
                    _unknown('UNKNOWN_REQUIREMENT_GRAMMAR', 'unsupported requirements directive')
                else:
                    add_requirement(line, path, 'test-requirements')
        for name in sorted(requirement_roots & files.keys()):
            requirements_file(name)

        for path, tree in trees.items():
            aliases = {'pytest': 'pytest', 'inspect': 'inspect'}
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    aliases.update({x.asname or x.name: x.name for x in node.names})
                elif isinstance(node, ast.ImportFrom) and node.module:
                    aliases.update({x.asname or x.name: node.module + '.' + x.name for x in node.names})
                    imported.update(node.module + '.' + x.name for x in node.names)
            def qualified(node):
                if isinstance(node, ast.Name):
                    return aliases.get(node.id, node.id)
                if isinstance(node, ast.Attribute):
                    return qualified(node.value) + '.' + node.attr
                return ''
            values = imported | {qualified(node) for node in ast.walk(tree) if isinstance(node, (ast.Attribute, ast.Name))}
            if any(value == 'pytest.collect' or value.startswith('pytest.collect.') for value in values):
                add_requirement('pytest<6', path, 'source-api.pytest.collect')
                evidence(path, 'source-api.pytest.collect', 'pytest<6')
            if values & {'inspect.getargspec', 'inspect.formatargspec'}:
                result['python_specifiers'].append('<3.11')
                evidence(path, 'source-api.inspect', '<3.11')

        if not matrices and not result['python_specifiers']:
            _unknown('UNKNOWN_UNDECLARED_PYTHON_COMPATIBILITY', 'no original Python compatibility declaration')
        witnesses = _python_witnesses(result['python_specifiers'], set().union(*matrices) if matrices else ())
        witnesses = [v for v in witnesses if all(v in SpecifierSet(spec) for spec in result['python_specifiers'])]
        if result['python_specifiers'] and not witnesses:
            _unknown('UNKNOWN_CONFLICTING_METADATA', 'Python release constraints have empty intersection')
        if matrices:
            declared = set.intersection(*matrices)
            if result['python_specifiers']:
                declared = {minor for minor in declared if any(
                    '.'.join(map(str, version.release[:2])) == minor for version in witnesses)}
            if not declared:
                _unknown('UNKNOWN_CONFLICTING_METADATA', 'declared Python matrices/constraints have empty intersection')
            result['declared_python'] = sorted(declared, key=Version)
        if implementations:
            declared = set.intersection(*implementations)
            if not declared:
                _unknown('UNKNOWN_CONFLICTING_METADATA', 'implementation declarations conflict')
            result['python_implementations'] = sorted(declared)
        result['python_specifiers'] = sorted(set(result['python_specifiers']))
        result['requirements'].sort(key=_canonical); result['evidence'].sort(key=_canonical)
        result['status'] = 'DERIVED_SOURCE_CONSTRAINTS'
    except _Unknown as error:
        result['reasons'].append({'reason': error.reason, 'detail': error.detail})
    except (UnicodeError, ValueError, TypeError, AttributeError, configparser.Error) as error:
        result['reasons'].append({'reason': 'UNKNOWN_METADATA_GRAMMAR', 'detail': str(error)})
    return result


def _catalog(catalog):
    if (not isinstance(catalog, dict) or catalog.get('schema') != CATALOG_SCHEMA
            or not isinstance(catalog.get('profiles'), list) or not catalog['profiles']):
        _unknown('UNKNOWN_CATALOG_AUTHORITY', 'nonempty versioned external catalog required')
    ids = set()
    for p in catalog['profiles']:
        required = {'id', 'python_version', 'python_implementation', 'pytest_version', 'packages', 'plugins'}
        if not isinstance(p, dict) or not required <= p.keys():
            _unknown('UNKNOWN_CATALOG_AUTHORITY', 'incomplete external profile')
        if not isinstance(p['id'], str) or not re.fullmatch(r'[A-Za-z0-9_.-]+', p['id']) or p['id'] in ids:
            _unknown('UNKNOWN_CATALOG_AUTHORITY', 'invalid or duplicate profile id')
        ids.add(p['id'])
        if p['python_implementation'] not in ('CPython', 'PyPy'):
            _unknown('UNKNOWN_CATALOG_AUTHORITY', 'unsupported Python implementation')
        if not isinstance(p['python_version'], str) or not re.fullmatch(r'[23]\.[0-9]+\.[0-9]+', p['python_version']):
            _unknown('UNKNOWN_CATALOG_AUTHORITY', 'exact ordinary interpreter version required')
        pins = {}
        for pin in _strings(p['packages'], 'complete exact package closure required'):
            req = _requirement(pin); specs = list(req.specifier)
            if req.url or req.marker or req.extras or len(specs) != 1 or specs[0].operator != '==' or '*' in specs[0].version:
                _unknown('UNKNOWN_CATALOG_AUTHORITY', 'exact unconditional package pin required')
            version = Version(specs[0].version); name = canonicalize_name(req.name)
            if name in pins:
                _unknown('UNKNOWN_CATALOG_AUTHORITY', 'duplicate normalized distribution: ' + name)
            pins[name] = version
        if pins.get('pytest') != Version(p['pytest_version']):
            _unknown('UNKNOWN_CATALOG_AUTHORITY', 'pytest pin differs from external policy')
        if not isinstance(p['plugins'], list):
            _unknown('UNKNOWN_CATALOG_AUTHORITY', 'explicit plugin list required')
        modules = set()
        for row in p['plugins']:
            if (not isinstance(row, dict) or set(row) != {'module', 'distribution', 'version'}
                    or any(not isinstance(v, str) for v in row.values())
                    or not re.fullmatch(r'[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*', row['module'])
                    or row['module'] in modules
                    or pins.get(canonicalize_name(row['distribution'])) != Version(row['version'])):
                _unknown('UNKNOWN_CATALOG_AUTHORITY', 'plugin lacks independent exact package pin')
            modules.add(row['module'])
        if not isinstance(p.get('marker_environment', {}), dict) or any(
                not isinstance(k, str) or not isinstance(v, str) for k, v in p.get('marker_environment', {}).items()):
            _unknown('UNKNOWN_CATALOG_AUTHORITY', 'explicit marker environment must be strings')
        if not isinstance(p.get('package_requirements', {}), dict):
            _unknown('UNKNOWN_CATALOG_AUTHORITY', 'package requirements mapping required')
        metadata_names = set()
        for name, values in p.get('package_requirements', {}).items():
            if not isinstance(name, str):
                _unknown('UNKNOWN_CATALOG_AUTHORITY', 'package metadata name must be text')
            normalized = canonicalize_name(name)
            if normalized in metadata_names:
                _unknown('UNKNOWN_CATALOG_AUTHORITY', 'duplicate normalized package metadata key: ' + normalized)
            metadata_names.add(normalized)
            if normalized not in pins:
                _unknown('UNKNOWN_CATALOG_AUTHORITY', 'metadata for an unpinned distribution')
            for value in _strings(values, 'package requirements must be strings'):
                _requirement(value)
    return catalog['profiles']


def _marker_variables(marker):
    if isinstance(marker, Variable):
        return {marker.value}
    if isinstance(marker, (tuple, list)):
        return set().union(*(_marker_variables(x) for x in marker)) if marker else set()
    return set()


def _evaluate(profile, constraints):
    reasons = []; version = Version(profile['python_version'])
    minor = '.'.join(str(x) for x in version.release[:2])
    if constraints['declared_python'] and minor not in constraints['declared_python']:
        reasons.append({'reason': 'INCOMPATIBLE_DECLARED_PYTHON', 'detail': minor})
    if any(version not in SpecifierSet(spec) for spec in constraints['python_specifiers']):
        reasons.append({'reason': 'INCOMPATIBLE_PYTHON_RANGE', 'detail': str(version)})
    if constraints['python_implementations'] and profile['python_implementation'] not in constraints['python_implementations']:
        reasons.append({'reason': 'INCOMPATIBLE_PYTHON_IMPLEMENTATION', 'detail': profile['python_implementation']})
    pins = {canonicalize_name(Requirement(pin).name): Version(next(iter(Requirement(pin).specifier)).version)
            for pin in profile['packages']}
    env = dict(profile.get('marker_environment', {}))
    derived = {'python_version': minor, 'python_full_version': str(version),
               'implementation_name': profile['python_implementation'].lower(),
               'platform_python_implementation': profile['python_implementation']}
    if any(key in env and env[key] != value for key, value in derived.items()):
        reasons.append({'reason': 'UNKNOWN_MARKER_ENVIRONMENT', 'detail': 'profile marker identity conflicts'})
    env.update(derived)
    metadata = {canonicalize_name(name): values for name, values in profile.get('package_requirements', {}).items()}
    requirements = list(constraints['requirements']); activated = set()

    def activate(name, extra):
        key = (name, extra)
        if key not in activated:
            activated.add(key)
            requirements.extend({'requirement': value, 'extra': extra, 'path': '@catalog/' + name,
                                 'field': 'Requires-Dist'} for value in metadata[name])

    for name in sorted(metadata):
        activate(name, '')
    for row in requirements:
        if row.get('python_versions') is not None and minor not in row['python_versions']:
            continue
        req = _requirement(row['requirement']); current = {**env, 'extra': row['extra']}
        if req.marker:
            missing = _marker_variables(req.marker._markers) - current.keys()
            if missing:
                reasons.append({'reason': 'UNKNOWN_MARKER_ENVIRONMENT', 'detail': ','.join(sorted(missing)),
                                'requirement': str(req)})
                continue
            if not req.marker.evaluate(environment=current):
                continue
        name = canonicalize_name(req.name)
        if name not in pins or pins[name] not in req.specifier:
            reasons.append({'reason': 'UNKNOWN_DEPENDENCY_UNSATISFIED', 'detail': str(req),
                            'installed_pin': str(pins[name]) if name in pins else None})
        if req.extras:
            if name not in metadata:
                reasons.append({'reason': 'UNKNOWN_EXTRA_DEPENDENCY_METADATA', 'detail': str(req)})
            else:
                for extra in sorted(req.extras):
                    activate(name, canonicalize_name(extra))
    unknown = [row for row in reasons if row['reason'].startswith('UNKNOWN_')]
    rejected = [row for row in reasons if row['reason'].startswith('INCOMPATIBLE_')]
    status = 'REJECTED' if rejected else ('UNKNOWN' if unknown else 'COMPATIBLE')
    return {'id': profile['id'], 'status': status, 'reason': (rejected or unknown or reasons)[0]['reason'] if reasons else None,
            'reasons': reasons, 'python_version': profile['python_version'], 'pytest_version': profile['pytest_version']}


def select_profile(files, catalog):
    """Select the highest compatible frozen Python/pytest pair, or retain UNKNOWN."""
    constraints = derive_constraints(files)
    result = {'schema': SELECTION_SCHEMA, 'status': 'UNKNOWN', 'constraints': constraints,
              'catalog_sha256': None, 'selector_sha256': _hash(Path(__file__).read_bytes()),
              'packaging_version': packaging.__version__, 'candidates': [], 'selected_profile': None,
              'reason': None}
    try:
        result['catalog_sha256'] = _hash(_canonical(catalog).encode())
        profiles = _catalog(catalog)
        if constraints['status'] != 'DERIVED_SOURCE_CONSTRAINTS':
            result['reason'] = constraints['reasons'][0]['reason']
            result['candidates'] = [{'id': p['id'], 'status': 'UNKNOWN', 'reason': result['reason'],
                                     'reasons': constraints['reasons']} for p in profiles]
            return result
        result['candidates'] = [_evaluate(p, constraints) for p in profiles]
        good = [p for p, row in zip(profiles, result['candidates']) if row['status'] == 'COMPATIBLE']
        if not good:
            result['reason'] = 'UNKNOWN_NO_COMPATIBLE_PROFILE'
            return result
        rank = lambda p: (Version(p['python_version']), Version(p['pytest_version']))
        best_rank = max(map(rank, good)); best = [p for p in good if rank(p) == best_rank]
        # A higher unresolved profile prevents a claim that this is the best choice.
        if any(row['status'] == 'UNKNOWN' and rank(p) >= best_rank
               for p, row in zip(profiles, result['candidates'])):
            result['reason'] = 'UNKNOWN_UNRESOLVED_HIGHER_PROFILE'
        elif len(best) != 1:
            result['reason'] = 'UNKNOWN_AMBIGUOUS_PROFILE'
        else:
            result['status'] = 'CANDIDATE_SOURCE_ENVIRONMENT'
            result['selected_profile'] = json.loads(_canonical(best[0]))
    except (_Unknown, InvalidVersion, InvalidRequirement, ValueError, TypeError, KeyError) as error:
        result['reason'] = 'UNKNOWN_CATALOG_AUTHORITY'
        result['detail'] = str(error)
        if isinstance(catalog, dict) and isinstance(catalog.get('profiles'), list):
            result['candidates'] = [
                {'id': p.get('id', '@' + str(index)) if isinstance(p, dict) else '@' + str(index),
                 'status': 'UNKNOWN', 'reason': result['reason'],
                 'reasons': [{'reason': result['reason'], 'detail': str(error)}]}
                for index, p in enumerate(catalog['profiles'])]
    return result


def validate_selection(files, catalog, selection):
    """Independently reconstruct all source/catalog/candidate decisions."""
    expected = select_profile(files, catalog)
    if not isinstance(selection, dict) or _canonical(selection) != _canonical(expected):
        raise ValueError('UNKNOWN_SELECTION_IDENTITY: selection differs from source/catalog reconstruction')
    return expected
