"""Versioned, source-derived static authority for native pytest admission.

This module adds a conservative Python/configuration grammar without changing
the published v1 verifier. It grants no execution, plugin or time authority.
An independent collector must bind the complete exact parameterized node set;
these static prefixes alone cannot certify assertion strength or containment.
"""
from __future__ import annotations

import ast
import configparser
import fnmatch
from pathlib import Path, PurePosixPath
import re
import shlex
import tomllib

from .decisive_native_verify import (
    NATIVE_CONFIG_FILES, _path, _snapshot, canonical, fingerprint, sha256,
)

SCHEMA = 'UDM_NATIVE_SUITE_AUTHORITY_V2'
CONFIG_SCHEMA = 'UDM_NATIVE_PYTEST_CONFIGURATION_V2'
_LOADED_SOURCE_SHA256 = sha256(Path(__file__).read_bytes())


def assert_source_identity():
    if sha256(Path(__file__).read_bytes()) != _LOADED_SOURCE_SHA256:
        raise ValueError('UNKNOWN_ADMISSION_SOURCE_MUTATION: loaded static authority differs from source')


def _words(value, key):
    result = shlex.split(value) if isinstance(value, str) else value
    if not isinstance(result, list) or any(not isinstance(x, str) or not x for x in result):
        raise ValueError('invalid ' + key)
    return result


def _options(value):
    """A closed option grammar; plugin requirements demand external licenses."""
    args = _words(value, 'addopts'); plugins = set(); index = 0
    simple = {'--strict-config', '--strict-markers', '--strict', '--disable-warnings',
              '--showlocals', '-l', '--full-trace', '--no-header', '--no-summary'}
    while index < len(args):
        arg = args[index]
        if arg in ('-k', '-m'):
            index += 1
            if index >= len(args) or not args[index] or args[index].startswith('-'):
                raise ValueError('missing native selection expression')
        elif arg in simple or re.fullmatch(r'-(?:q+|v+|r[A-Za-z]+)', arg):
            pass
        elif re.fullmatch(r'--(?:tb=(?:auto|long|short|line|native|no)|color=(?:yes|no|auto)|'
                          r'durations=[0-9]+|durations-min=(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))', arg):
            pass
        elif arg == '--import-mode=importlib':
            pass
        elif re.fullmatch(r'--benchmark-(?:sort=(?:min|max|mean|stddev|median|iqr|ops|rounds|iterations|name|fullname)|'
                          r'group-by=(?:group|name|fullname|func|fullfunc|param:[A-Za-z_][A-Za-z0-9_]*|param)|'
                          r'warmup=(?:true|false|auto)|warmup-iterations=[1-9][0-9]*|'
                          r'min-rounds=[1-9][0-9]*|(?:min-time|max-time)=(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))', arg):
            plugins.add('pytest_benchmark.plugin')
        else:
            raise ValueError('unsupported addopts collection/authority option: ' + arg)
        index += 1
    return args, sorted(plugins)


def _read_config(name, raw):
    text = raw.decode('utf-8')
    if name == 'pyproject.toml':
        options = tomllib.loads(text).get('tool', {}).get('pytest', {}).get('ini_options')
        return options
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string(text)
    section = 'tool:pytest' if name == 'setup.cfg' else 'pytest'
    if parser.has_section(section):
        return dict(parser.items(section))
    return {} if name in ('pytest.ini', '.pytest.ini') else None


def configuration(files):
    """Describe immutable effective root config; never activate its plugins.

    Precedence follows pytest 8 discovery. Every root config blob is bound,
    including inactive files; augmented source cannot add or change any config.
    Values have explicit JSON types and unknown active settings fail closed.
    """
    try:
        if not isinstance(files, dict) or any(not isinstance(k, str) or not isinstance(v, bytes)
                                              for k, v in files.items()):
            raise ValueError('tracked configuration byte map required')
        active = None; values = {}
        for name in ('pytest.ini', '.pytest.ini', 'pyproject.toml', 'tox.ini', 'setup.cfg'):
            if name not in files:
                continue
            current = _read_config(name, files[name])
            if current is not None and active is None:
                if not isinstance(current, dict):
                    raise ValueError('pytest ini options must be a table')
                active, values = name, current
                break
        if active is None and 'pyproject.toml' in files:
            active = 'pyproject.toml'  # pytest >= 8.1 uses the first pyproject as fallback root config.
        allowed = {'addopts', 'python_files', 'python_classes', 'python_functions', 'testpaths',
                   'norecursedirs', 'markers', 'filterwarnings', 'xfail_strict', 'usefixtures',
                   'empty_parameter_set_mark', 'minversion', 'junit_suite_name', 'junit_logging',
                   'junit_log_passing_tests', 'junit_duration_report', 'junit_family',
                   'console_output_style', 'log_cli', 'log_cli_level', 'log_level', 'log_format',
                   'log_date_format', 'log_cli_format', 'log_cli_date_format', 'log_auto_indent',
                   'log_file_level', 'log_file_format', 'log_file_date_format'}
        if set(values) - allowed:
            raise ValueError('unsupported pytest configuration: ' + ','.join(sorted(set(values) - allowed)))
        typed = {}
        line_keys = {'markers', 'filterwarnings'}
        word_keys = {'python_files', 'python_classes', 'python_functions', 'testpaths', 'norecursedirs', 'usefixtures'}
        bool_keys = {'xfail_strict', 'junit_log_passing_tests', 'log_cli'}
        for key, value in values.items():
            if key == 'addopts':
                continue
            if key in word_keys:
                typed[key] = _words(value, key)
            elif key in line_keys:
                lines = value.splitlines() if isinstance(value, str) else value
                if not isinstance(lines, list) or any(not isinstance(x, str) for x in lines):
                    raise ValueError('invalid ' + key)
                typed[key] = [x.strip() for x in lines if x.strip()]
            elif key in bool_keys:
                if type(value) is bool:
                    typed[key] = value
                elif isinstance(value, str) and value.lower() in ('true', 'false', '1', '0', 'yes', 'no'):
                    typed[key] = value.lower() in ('true', '1', 'yes')
                else:
                    raise ValueError('invalid ' + key)
            elif isinstance(value, str):
                typed[key] = value
            else:
                raise ValueError('invalid ' + key)
        for key in ('python_files', 'python_classes', 'python_functions'):
            for pattern in typed.get(key, []):
                if any(c in pattern for c in ('/', '\\', '\x00')) or pattern in ('.', '..'):
                    raise ValueError('unsafe ' + key)
        for path in typed.get('testpaths', []):
            _path(path.rstrip('/'))
        args, plugins = _options(values.get('addopts', []))
        return {'schema': CONFIG_SCHEMA, 'active_config': active,
                'config_sha256': {name: sha256(files[name]) for name in NATIVE_CONFIG_FILES if name in files},
                'ini_options': typed, 'pytest_options': args, 'plugin_requirements': plugins,
                'test_patterns': typed.get('python_files', ['test_*.py', '*_test.py']),
                'function_patterns': typed.get('python_functions', ['test']),
                'class_patterns': typed.get('python_classes', ['Test'])}
    except (ValueError, AttributeError, TypeError, UnicodeError, configparser.Error) as error:
        raise ValueError('UNKNOWN_INTERFACE: unsupported native test configuration: ' + str(error)) from error


def _matches(name, patterns):
    return any(fnmatch.fnmatchcase(name, pattern) if any(c in pattern for c in '*?[')
               else name.startswith(pattern) for pattern in patterns)


def _test_module(name, config):
    return name.endswith('.py') and any(fnmatch.fnmatchcase(PurePosixPath(name).name, pattern)
                                       for pattern in config['test_patterns'])


def _test_scope(name, config):
    path = _path(name)
    return path.suffix == '.py' and (_test_module(name, config)
        or any(part in ('test', 'tests', 'testing') for part in path.parts)
        or path.name == 'conftest.py')


def validate_candidate(candidate, files):
    """Validate production-only replacements under the v2 immutable grammar."""
    assert_source_identity()
    if (not isinstance(candidate, dict) or set(candidate) != {'replacements'}
            or not isinstance(candidate['replacements'], list)):
        raise ValueError('invalid candidate schema')
    config = configuration(files); seen = set()
    for row in candidate['replacements']:
        if not isinstance(row, dict) or set(row) != {'path', 'original_sha256', 'replacement'}:
            raise ValueError('invalid replacement schema')
        path = _path(row['path']); name = path.as_posix()
        if name in seen:
            raise ValueError('duplicate candidate path')
        seen.add(name)
        testpaths = config['ini_options'].get('testpaths', [])
        if (name not in files or path.suffix != '.py'
                or path.name in ('conftest.py', 'setup.py', 'pytest.py')
                or _test_scope(name, config)
                or any(part.startswith('.') or part in ('test', 'tests', 'testing') or part.startswith('test_')
                       for part in path.parts)
                or any(root == '.' or name == root.rstrip('/') or name.startswith(root.rstrip('/') + '/')
                       for root in testpaths)):
            raise ValueError('candidate must replace a tracked production Python file')
        if row['original_sha256'] != sha256(files[name]):
            raise ValueError('candidate original blob mismatch')
        if not isinstance(row['replacement'], str):
            raise ValueError('candidate source must be text')
        if row['replacement'].encode('utf-8') == files[name]:
            raise ValueError('unchanged candidate replacement is not development')
        compile(row['replacement'], name, 'exec')


def _class_test_nodes(path, tree, function_patterns, class_patterns):
    """Map statically closed Python inheritance to pytest/unittest node prefixes.

    The independent native collector remains authoritative for actual collection.
    Unknown bases affecting tests are an obstruction, never guessed ancestry.
    """
    classes = {}; bindings = {'object': '@object'}; routes = set(); nodes = []
    definitions = {}

    def qualified(node):
        if isinstance(node, ast.Name):
            return bindings.get(node.id)
        if isinstance(node, ast.Attribute):
            root = qualified(node.value)
            return root + '.' + node.attr if isinstance(root, str) else None
        return None

    for statement in tree.body:
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                bindings[alias.asname or alias.name.split('.')[0]] = alias.name if alias.asname else alias.name.split('.')[0]
        elif isinstance(statement, ast.ImportFrom):
            for alias in statement.names:
                bindings[alias.asname or alias.name] = ((statement.module or '') + '.' + alias.name)
        elif isinstance(statement, ast.ClassDef):
            key = statement.name
            if key in classes:
                raise ValueError('UNKNOWN_SUITE_CONTRACT: duplicate class mapping unsupported')
            bases = []
            for base in statement.bases:
                value = qualified(base)
                if value in ('unittest.TestCase', 'unittest.case.TestCase'):
                    value = '@TestCase'
                bases.append(value)
            classes[key] = {'node': statement, 'bases': bases or ['@object']}
            bindings[key] = key
        elif isinstance(statement, (ast.Assign, ast.AnnAssign)):
            targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
            value = qualified(statement.value)
            for target in targets:
                if isinstance(target, ast.Name):
                    bindings[target.id] = value
        elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            bindings[statement.name] = None

    mros = {'@object': ['@object'], '@TestCase': ['@TestCase', '@object']}
    visiting = set()

    def linearize(name):
        if name in mros:
            return mros[name]
        if name not in classes or name in visiting:
            raise ValueError('UNKNOWN_SUITE_CONTRACT: unresolved native test base mapping')
        visiting.add(name)
        bases = classes[name]['bases']
        sequences = [list(linearize(base)) for base in bases] + [list(bases)]
        result = [name]
        while any(sequences):
            sequences = [sequence for sequence in sequences if sequence]
            head = next((sequence[0] for sequence in sequences
                if not any(sequence[0] in other[1:] for other in sequences)), None)
            if head is None:
                raise ValueError('UNKNOWN_SUITE_CONTRACT: inconsistent native test base mapping')
            result.append(head)
            sequences = [sequence[1:] if sequence[0] == head else sequence for sequence in sequences]
        visiting.remove(name); mros[name] = result
        return result

    def body_bindings(node):
        result = {}
        for statement in node.body:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                result[statement.name] = statement
            elif isinstance(statement, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
                for target in targets:
                    if isinstance(target, ast.Name):
                        result[target.id] = None
        return result

    # Every top-level function uses pytest's configured function grammar.
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            definitions[statement.name] = ast.dump(statement, include_attributes=False)
            if _matches(statement.name, function_patterns):
                nodes.append(path + '::' + statement.name); routes.add(statement.name)
    for name, entry in classes.items():
        local = body_bindings(entry['node'])
        for method, statement in local.items():
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                definitions[name + '::' + method] = ast.dump(statement, include_attributes=False)
        has_tests = any(_matches(method, function_patterns + ['test']) for method in local)
        try:
            order = linearize(name)
        except ValueError:
            if has_tests or _matches(name, class_patterns):
                raise
            continue  # An unrelated ordinary data/helper class grants no test route.
        unittest = '@TestCase' in order
        if not unittest and not _matches(name, class_patterns):
            continue
        selected = {}
        for ancestor in order:
            if ancestor in classes:
                for method, statement in body_bindings(classes[ancestor]['node']).items():
                    selected.setdefault(method, (ancestor, statement))
        patterns = ['test'] if unittest else function_patterns
        for method, (ancestor, statement) in selected.items():
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)) and _matches(method, patterns):
                nodes.append(path + '::' + name + '::' + method)
                routes.add(ancestor + '::' + method)
    return nodes, routes, definitions


def _test_nodes(path, source, *, function_patterns=None, class_patterns=None):
    """Static declarations only; proven noncallable data is never a test alias.

    Python initializers are not a sandbox. Visible collection-scope namespace
    operations are refused; ordinary test bodies retain Python semantics and
    exact independent collection remains a separate required authority.
    """
    function_patterns = ['test'] if function_patterns is None else function_patterns
    class_patterns = ['Test'] if class_patterns is None else class_patterns
    patterns = list(dict.fromkeys(function_patterns + ['test']))
    try:
        tree = ast.parse(source, filename=path)
    except (SyntaxError, UnicodeError) as error:
        raise ValueError('UNKNOWN_NATIVE_SUITE_AST') from error
    result = []; declared = set(); definitions = set()
    primitives = {'globals', 'locals', 'vars', 'setattr', 'delattr', 'exec', 'eval'}

    def refuse(reason):
        raise ValueError('UNKNOWN_SUITE_CONTRACT: ' + reason)

    def safe(value, env):
        if isinstance(value, ast.Constant):
            return True
        if isinstance(value, (ast.List, ast.Tuple, ast.Set, ast.Dict)):
            return True  # The container itself is noncallable, regardless of its contents.
        if isinstance(value, ast.Name):
            return env.get(value.id, False)
        if isinstance(value, ast.UnaryOp) and isinstance(value.op, (ast.UAdd, ast.USub, ast.Invert, ast.Not)):
            return safe(value.operand, env)
        return False

    def inert(value, env):
        """Expressions whose evaluation cannot mutate earlier data bindings."""
        if value is None or isinstance(value, (ast.Constant, ast.Name)):
            return True
        if isinstance(value, (ast.List, ast.Tuple)):
            return all(inert(child, env) and not isinstance(child, ast.Starred) for child in value.elts)
        if isinstance(value, (ast.Set, ast.Dict)):
            try:
                ast.literal_eval(value)
                return True
            except (ValueError, TypeError, SyntaxError):
                return False
        if isinstance(value, ast.UnaryOp):
            return safe(value.operand, env)
        return False

    def inert_statement(node, env):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            annotations = [arg.annotation for arg in node.args.posonlyargs + node.args.args
                           + node.args.kwonlyargs]
            annotations += [node.returns]
            if node.args.vararg:
                annotations.append(node.args.vararg.annotation)
            if node.args.kwarg:
                annotations.append(node.args.kwarg.annotation)
            expressions = node.args.defaults + node.args.kw_defaults + annotations
            return not node.decorator_list and all(inert(value, env) for value in expressions)
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            return inert(node.value, env) and inert(getattr(node, 'annotation', None), env)
        if isinstance(node, ast.Expr):
            return inert(node.value, env)
        return isinstance(node, (ast.Pass, ast.Global, ast.Nonlocal))

    def targets(target):
        if isinstance(target, ast.Name):
            return [target.id]
        if isinstance(target, (ast.Tuple, ast.List)):
            return [name for child in target.elts for name in targets(child)]
        if isinstance(target, ast.Starred):
            return targets(target.value)
        if isinstance(target, (ast.Attribute, ast.Subscript)):
            refuse('dynamic namespace write unsupported')
        return []

    def inspect(node):
        # Definitions have their own scope; their bodies are not collection statements.
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            expressions = list(node.decorator_list)
            if isinstance(node, ast.ClassDef):
                expressions += node.bases + [kw.value for kw in node.keywords]
            else:
                expressions += node.args.defaults + [x for x in node.args.kw_defaults if x is not None]
                if not _matches(node.name, patterns):
                    for child in ast.walk(node):
                        if ((isinstance(child, ast.Name) and child.id in primitives)
                                or (isinstance(child, ast.Attribute) and child.attr in primitives)
                                or (isinstance(child, (ast.Global, ast.Nonlocal))
                                    and any(_matches(name, patterns) for name in child.names))):
                            refuse('initializer helper test registration unsupported')
            for expression in expressions:
                inspect(expression)
            return
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and child.id in primitives:
                refuse('dynamic test registration primitive unsupported')
            if isinstance(child, ast.Attribute) and child.attr in primitives:
                refuse('dynamic test registration primitive unsupported')
            if (isinstance(child, ast.Call) and isinstance(child.func, ast.Name)
                    and _matches(child.func.id, patterns)):
                refuse('collection-time test callable execution unsupported')
            if isinstance(child, ast.NamedExpr):
                if any(_matches(name, patterns) for name in targets(child.target)):
                    refuse('conditional test binding unsupported')

    def visit(nodes, prefix, inherited):
        env = dict(inherited)
        for node in nodes:
            inspect(node)
            if not inert_statement(node, env):
                # Calls, imports, decorators, class initialization and opaque
                # operations can rebind module globals through arbitrary Python.
                env = {name: False for name in env}
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                key = prefix + '::' + node.name
                if _matches(node.name, patterns):
                    if key in definitions:
                        refuse('duplicate test definition unsupported')
                    definitions.add(key); result.append(key); declared.add(id(node))
                env[node.name] = False
            elif isinstance(node, ast.ClassDef):
                if _matches(node.name, patterns):
                    refuse('test callable class alias unsupported')
                # Class bodies fall back to module globals, not surrounding class locals.
                visit(node.body, prefix + '::' + node.name, module_env if prefix != path else env)
                env[node.name] = False
            elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                raw_targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                names = [name for target in raw_targets for name in targets(target)]
                value = getattr(node, 'value', None)
                proven = (not isinstance(node, ast.AugAssign)
                          and all(isinstance(target, ast.Name) for target in raw_targets)
                          and safe(value, env))
                if any(_matches(name, patterns) for name in names) and not proven:
                    refuse('dynamic test alias unsupported')
                for name in names:
                    env[name] = proven and all(isinstance(target, ast.Name) for target in raw_targets)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                for alias in node.names:
                    if alias.name == '*':
                        refuse('wildcard imported tests unsupported')
                    name = alias.asname or alias.name.split('.')[0]
                    if _matches(name, patterns) or alias.name.split('.')[-1] in primitives:
                        refuse('imported test callable or registration primitive unsupported')
                    env[name] = False
            elif isinstance(node, ast.Delete):
                for target in node.targets:
                    for name in targets(target):
                        if _matches(name, patterns):
                            refuse('test deletion unsupported')
                        env[name] = False
            else:
                for child in ast.walk(node):
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and _matches(child.name, patterns):
                        refuse('conditional or nested test definition unsupported')
                    if isinstance(child, ast.Name) and isinstance(child.ctx, (ast.Store, ast.Del)):
                        if _matches(child.id, patterns):
                            refuse('conditional test binding unsupported')
                        env[child.id] = False
                    if isinstance(child, ast.ExceptHandler) and child.name:
                        if _matches(child.name, patterns):
                            refuse('conditional test binding unsupported')
                        env[child.name] = False
                    if isinstance(child, (ast.MatchAs, ast.MatchStar)) and child.name:
                        if _matches(child.name, patterns):
                            refuse('conditional test binding unsupported')
                        env[child.name] = False
        return env

    module_env = {}
    module_env.update(visit(tree.body, path, module_env))
    if any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and _matches(node.name, patterns)
           and id(node) not in declared for node in ast.walk(tree)):
        refuse('conditional or nested test definition unsupported')
    for outer in (node for node in tree.body if isinstance(node, ast.ClassDef)):
        for nested in (node for node in outer.body if isinstance(node, ast.ClassDef)):
            if any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                   and _matches(node.name, patterns) for node in ast.walk(nested)):
                refuse('nested class test mapping unsupported')
    nodes, _, _ = _class_test_nodes(path, tree, function_patterns, class_patterns)
    return tree, nodes


def derive_suite_contract(repo, base_commit, augmented_commit, protocol_binding, *, repository):
    """Bind immutable configuration and author test changes from independent Git."""
    assert_source_identity()
    if (not isinstance(repository, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository)
            or not isinstance(protocol_binding, str) or not re.fullmatch('[0-9a-f]{64}', protocol_binding)):
        raise ValueError('wrong native suite repository or protocol')
    base_source, old, _ = _snapshot(repo, base_commit)
    source, files, _ = _snapshot(repo, augmented_commit)
    config = configuration(files)
    if any(old.get(name) != files.get(name) for name in NATIVE_CONFIG_FILES):
        raise ValueError('immutable native configuration changed')
    changed_paths = {name for name in old.keys() | files.keys() if old.get(name) != files.get(name)}
    if any(name not in files or not _test_scope(name, config) for name in changed_paths):
        raise ValueError('source overlay may change canonical author Python tests only')
    changed = {}; required = []; helper_changed = False
    for name in sorted(changed_paths):
        if PurePosixPath(name).name == 'conftest.py' and name not in old:
            raise ValueError('new native configuration path requires external authority')
        tree, nodes = _test_nodes(name, files[name], function_patterns=config['function_patterns'],
            class_patterns=config['class_patterns'])
        previous = ast.Module(body=[], type_ignores=[])
        if name in old:
            previous, _ = _test_nodes(name, old[name], function_patterns=config['function_patterns'],
                class_patterns=config['class_patterns'])
            if ast.dump(tree, include_attributes=False) == ast.dump(previous, include_attributes=False):
                continue
        _, routed, definitions = _class_test_nodes(name, tree, config['function_patterns'], config['class_patterns'])
        _, _, prior_definitions = _class_test_nodes(name, previous, config['function_patterns'], config['class_patterns'])
        for origin, declaration in definitions.items():
            method = origin.split('::')[-1]
            if (_matches(method, config['function_patterns'] + ['test'])
                    and prior_definitions.get(origin) != declaration and origin not in routed):
                raise ValueError('UNKNOWN_SUITE_CONTRACT: changed test assertion has no collected class mapping')
        if _collection_declarations(tree) != _collection_declarations(previous):
            raise ValueError('new or changed pytest plugin/collection authority requires external license')
        changed[name] = sha256(files[name])
        if _test_module(name, config):
            if not nodes:
                raise ValueError('UNKNOWN_NATIVE_SUITE_DELTA: changed test module has no static test nodes')
            required.extend(nodes)
        else:
            helper_changed = True
    if helper_changed:
        for name, raw in sorted(files.items()):
            if _test_module(name, config):
                _, nodes = _test_nodes(name, raw, function_patterns=config['function_patterns'],
                    class_patterns=config['class_patterns'])
                required.extend(nodes)
    if not required:
        raise ValueError('UNKNOWN_NATIVE_SUITE_DELTA: no changed native test assertions')
    return {'schema': SCHEMA, 'derivation': 'STATIC_NATIVE_TEST_AST_DELTA_V2',
            'repository': repository, 'baseline_commit': base_commit, 'source_commit': augmented_commit,
            'protocol_binding': protocol_binding, 'baseline_source': base_source, 'source': source,
            'configuration': config, 'test_source_sha256': changed,
            'required_test_nodes': sorted(set(required))}


def _collection_declarations(tree):
    declarations = []
    for node in ast.walk(tree):
        names = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(node.name)
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names.extend(child.id for target in targets for child in ast.walk(target) if isinstance(child, ast.Name))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            names.extend(alias.asname or alias.name.split('.')[0] for alias in node.names)
        if any(name.startswith('pytest_') for name in names):
            declarations.append(ast.dump(node, include_attributes=False))
    return sorted(declarations)


def validate_suite_contract(contract, authority):
    if not isinstance(authority, dict) or authority.get('schema') != SCHEMA:
        raise ValueError('wrong native suite authority schema')
    try:
        expected = derive_suite_contract(contract['repo_path'], authority.get('baseline_commit'),
            contract['commit'], contract['protocol_binding'], repository=contract['repository'])
    except (KeyError, TypeError) as error:
        raise ValueError('invalid native suite contract source') from error
    if authority != expected:
        raise ValueError('native suite authority source, config, assertions or protocol mismatch')
    return fingerprint(expected)
