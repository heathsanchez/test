"""Independent, source/data-only reconstruction of the bounded V45 authority.

API::

    expected = derive(files, baseline, modes, base_modes, authority)
    comparison = validate(expected, authority)

``files`` and ``baseline`` are independently authenticated original path->bytes
maps.  Their mode maps bind the same complete path sets.  This helper handles
regular Git blobs only (100644/100755); links/gitlinks are explicit obstructions
because this API cannot carry both raw link bytes and resolved projections.
The caller authenticates repository/commits/protocol and source inventory/tree
identities separately.  ``derive`` reconstructs all assertion/configuration/
namespace fields without taking selections or witnesses from ``authority``.
Its authority argument is shape-checked only; it never supplies requirements.

This module never imports repository verifiers or fixture source, executes or
compiles fixture code, calls Git, collects/runs tests, or makes a qualification
claim.  AST parsing and literal evaluation inspect source as data.  The one
sibling import below loads our own independent audit grammar by its exact path.
Run under the original controller's Python 3.12 AST grammar; a different minor
version is an explicit obstruction because declaration AST hashes can differ.
Only current-controller stdlib (including tomllib when needed) is required.
Unsupported source/configuration is Obstruction, not an inferred requirement.
"""

import ast
import configparser
import fnmatch
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import shlex
import sys


# Load only the newly authored audit helper, never a similarly named repo file.
_grammar_spec = importlib.util.spec_from_file_location(
    "independent_v45_test_source_grammar", Path(__file__).with_name("test_source_grammar.py"))
_grammar = importlib.util.module_from_spec(_grammar_spec)
_grammar_spec.loader.exec_module(_grammar)
Obstruction = _grammar.Obstruction

CONFIG_FILES = ("pytest.ini", ".pytest.ini", "tox.ini", "setup.cfg", "pyproject.toml")
REGULAR = {"100644", "100755"}
FUNCTIONS = (ast.FunctionDef, ast.AsyncFunctionDef)
DEFINITIONS = FUNCTIONS + (ast.ClassDef,)
PRIMITIVES = {"globals", "locals", "vars", "setattr", "delattr", "exec", "eval"}
DERIVED_KEYS = {"schema", "derivation", "configuration", "test_source_sha256",
                "required_test_nodes", "namespace_certificate"}
IDENTITY_KEYS = {"repository", "baseline_commit", "source_commit", "protocol_binding",
                 "baseline_source", "source"}


def obstruct(message):
    raise Obstruction("INDEPENDENT_SOURCE_OBSTRUCTION: " + message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def blob(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def path_of(name):
    if not isinstance(name, str) or not name or "\\" in name or "\0" in name:
        obstruct("unsafe logical source path")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or str(path) != name:
        obstruct("unsafe logical source path")
    return path


def matches(name, patterns):
    return any(fnmatch.fnmatchcase(name, pattern) if set(pattern) & set("*?[")
               else name.startswith(pattern) for pattern in patterns)


def module_path(name, config):
    return (name.endswith(".py") and any(fnmatch.fnmatchcase(PurePosixPath(name).name, pattern)
                                        for pattern in config["test_patterns"]))


def test_scope(name, config):
    path = path_of(name)
    return path.suffix == ".py" and (module_path(name, config) or path.name == "conftest.py" or
                                    bool(set(path.parts) & {"test", "tests", "testing"}))


def words(value, key):
    result = shlex.split(value) if isinstance(value, str) else value
    if not isinstance(result, list) or any(not isinstance(item, str) or not item for item in result):
        obstruct("invalid configuration word list: " + key)
    return result


def options(value):
    args = words(value, "addopts")
    plugins = set()
    simple = {"--strict-config", "--strict-markers", "--strict", "--disable-warnings", "--showlocals",
              "-l", "--full-trace", "--no-header", "--no-summary", "--import-mode=importlib"}
    general = (r"--(?:tb=(?:auto|long|short|line|native|no)|color=(?:yes|no|auto)|durations=[0-9]+|"
               r"durations-min=(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))")
    benchmark = (r"--benchmark-(?:sort=(?:min|max|mean|stddev|median|iqr|ops|rounds|iterations|name|fullname)|"
                 r"group-by=(?:group|name|fullname|func|fullfunc|param:[A-Za-z_][A-Za-z0-9_]*|param)|"
                 r"warmup=(?:true|false|auto)|warmup-iterations=[1-9][0-9]*|min-rounds=[1-9][0-9]*|"
                 r"(?:min-time|max-time)=(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))")
    position = 0
    while position < len(args):
        item = args[position]
        if item in {"-k", "-m"}:
            position += 1
            if position == len(args) or args[position].startswith("-"):
                obstruct("missing configuration selection expression")
        elif item in simple or re.fullmatch(r"-(?:q+|v+|r[A-Za-z]+)", item) or re.fullmatch(general, item):
            pass
        elif re.fullmatch(benchmark, item):
            plugins.add("pytest_benchmark.plugin")
        else:
            obstruct("unsupported addopts: " + item)
        position += 1
    return args, sorted(plugins)


def read_config(name, raw):
    text = raw.decode("utf-8")
    if name == "pyproject.toml":
        try:
            import tomllib
        except ImportError:
            obstruct("stdlib TOML parser unavailable")
        return tomllib.loads(text).get("tool", {}).get("pytest", {}).get("ini_options")
    parser = configparser.ConfigParser(interpolation=None)
    parser.read_string(text)
    section = "tool:pytest" if name == "setup.cfg" else "pytest"
    if parser.has_section(section):
        return dict(parser.items(section))
    return {} if name in {"pytest.ini", ".pytest.ini"} else None


def configuration(files):
    active, values = None, {}
    try:
        for name in ("pytest.ini", ".pytest.ini", "pyproject.toml", "tox.ini", "setup.cfg"):
            if name in files:
                candidate = read_config(name, files[name])
                if candidate is not None:
                    active, values = name, candidate
                    break
        if active is None and "pyproject.toml" in files:
            active = "pyproject.toml"
        if not isinstance(values, dict):
            obstruct("pytest configuration is not a table")
        allowed = {"addopts", "python_files", "python_classes", "python_functions", "testpaths", "norecursedirs",
                   "markers", "filterwarnings", "xfail_strict", "usefixtures", "empty_parameter_set_mark", "minversion",
                   "junit_suite_name", "junit_logging", "junit_log_passing_tests", "junit_duration_report", "junit_family",
                   "console_output_style", "log_cli", "log_cli_level", "log_level", "log_format", "log_date_format",
                   "log_cli_format", "log_cli_date_format", "log_auto_indent", "log_file_level", "log_file_format",
                   "log_file_date_format"}
        if set(values) - allowed:
            obstruct("unsupported configuration settings: " + ",".join(sorted(set(values) - allowed)))
        word_keys = {"python_files", "python_classes", "python_functions", "testpaths", "norecursedirs", "usefixtures"}
        bool_keys = {"xfail_strict", "junit_log_passing_tests", "log_cli"}
        typed = {}
        for key, value in values.items():
            if key == "addopts":
                continue
            if key in word_keys:
                typed[key] = words(value, key)
            elif key in {"markers", "filterwarnings"}:
                lines = value.splitlines() if isinstance(value, str) else value
                if not isinstance(lines, list) or any(not isinstance(item, str) for item in lines):
                    obstruct("invalid configuration lines: " + key)
                typed[key] = [item.strip() for item in lines if item.strip()]
            elif key in bool_keys:
                if type(value) is bool:
                    typed[key] = value
                elif isinstance(value, str) and value.lower() in {"true", "false", "1", "0", "yes", "no"}:
                    typed[key] = value.lower() in {"true", "1", "yes"}
                else:
                    obstruct("invalid configuration boolean: " + key)
            elif isinstance(value, str):
                typed[key] = value
            else:
                obstruct("invalid configuration value: " + key)
        for key in ("python_files", "python_functions", "python_classes"):
            if any(pattern in {".", ".."} or any(c in pattern for c in ("/", "\\", "\0"))
                   for pattern in typed.get(key, [])):
                obstruct("unsafe configuration pattern: " + key)
        for name in typed.get("testpaths", []):
            path_of(name.rstrip("/"))
        args, plugins = options(values.get("addopts", []))
        return {"schema": "UDM_NATIVE_PYTEST_CONFIGURATION_V2", "active_config": active,
                "config_sha256": {name: sha(files[name]) for name in CONFIG_FILES if name in files},
                "ini_options": typed, "pytest_options": args, "plugin_requirements": plugins,
                "test_patterns": typed.get("python_files", ["test_*.py", "*_test.py"]),
                "function_patterns": typed.get("python_functions", ["test"]),
                "class_patterns": typed.get("python_classes", ["Test"])}
    except (UnicodeError, AttributeError, TypeError, configparser.Error, ValueError) as error:
        if isinstance(error, Obstruction):
            raise
        obstruct("unsupported configuration: " + str(error))


def protected(name, config):
    return (matches(name, config["function_patterns"] + config["class_patterns"] + ["test", "Test"]) or
            name.startswith("pytest_") or name in PRIMITIVES)


def literal(node):
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError, SyntaxError):
        obstruct("nonliteral production binding/default/annotation")


def parse_python(raw, filename):
    try:
        return ast.parse(raw, filename=filename)
    except (SyntaxError, UnicodeError, ValueError) as error:
        obstruct("unsupported original Python AST in " + filename + ": " + str(error))


def plain_function(node):
    if node.decorator_list:
        obstruct("decorated production declaration")
    parameters = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
    if node.args.vararg:
        parameters += [node.args.vararg]
    if node.args.kwarg:
        parameters += [node.args.kwarg]
    expressions = node.args.defaults + node.args.kw_defaults + [arg.annotation for arg in parameters] + [node.returns]
    for expression in expressions:
        if expression is not None:
            literal(expression)


def closed_exports(raw, filename, config):
    tree = parse_python(raw, filename)
    bound = set()
    declared_all = None
    classes = {"object"}

    def bind(name, is_all=False):
        if name in bound:
            obstruct("duplicate production namespace binding")
        if (protected(name, config) or name == "__all__" and not is_all or
                name.startswith("__") and name.endswith("__") and name not in {"__all__", "__doc__"}):
            obstruct("protected/dynamic production export")
        bound.add(name)

    def assignment(node, at_module):
        nonlocal declared_all
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if any(not isinstance(target, ast.Name) for target in targets):
            obstruct("non-name production namespace write")
        if isinstance(node, ast.AnnAssign) and node.annotation is not None:
            literal(node.annotation)
        value = literal(node.value)
        for target in targets:
            if at_module:
                bind(target.id, target.id == "__all__")
            if target.id == "__all__":
                if not at_module or len(targets) != 1:
                    obstruct("unsupported __all__ protocol")
                if (not isinstance(value, (list, tuple)) or any(not isinstance(name, str) or not name.isidentifier()
                        for name in value) or len(set(value)) != len(value)):
                    obstruct("nonliteral/duplicate __all__ protocol")
                declared_all = list(value)

    for statement in tree.body:
        if isinstance(statement, ast.Pass) or (isinstance(statement, ast.Expr) and
                isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str)):
            continue
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            assignment(statement, True)
        elif isinstance(statement, FUNCTIONS):
            bind(statement.name)
            plain_function(statement)
        elif isinstance(statement, ast.ClassDef):
            bind(statement.name)
            if statement.decorator_list or statement.keywords or any(
                    not isinstance(base, ast.Name) or base.id not in classes for base in statement.bases):
                obstruct("opaque production class initialization")
            for member in statement.body:
                if isinstance(member, ast.Pass) or (isinstance(member, ast.Expr) and
                        isinstance(member.value, ast.Constant) and isinstance(member.value.value, str)):
                    continue
                if isinstance(member, FUNCTIONS):
                    if member.name in {"__init_subclass__", "__class_getitem__"}:
                        obstruct("production class initialization hook")
                    plain_function(member)
                elif isinstance(member, (ast.Assign, ast.AnnAssign)):
                    assignment(member, False)
                else:
                    obstruct("effectful production class body")
            classes.add(statement.name)
        else:
            obstruct("production import/reexport/initializer effect")
    exports = sorted(name for name in bound if not name.startswith("_")) if declared_all is None else sorted(declared_all)
    if any(name not in bound or protected(name, config) for name in exports):
        obstruct("unresolved/protected production export protocol")
    return exports


def import_route(module, files, modes, config):
    if not isinstance(module, str) or not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*", module):
        obstruct("nonabsolute production wildcard module")
    parts = module.split(".")
    candidates = [(root, root + "/".join(parts) + suffix) for root in ("", "src/")
                  for suffix in (".py", "/__init__.py") if root + "/".join(parts) + suffix in files]
    if len(candidates) != 1:
        obstruct("unresolved/ambiguous root/src production module")
    root, target = candidates[0]
    other = "src/" if root == "" else ""
    for size in range(1, len(parts) + 1):
        stem = other + "/".join(parts[:size])
        if stem + ".py" in files or stem + "/__init__.py" in files:
            obstruct("ambiguous alternate production import route")
    route_paths = []
    for size in range(1, len(parts)):
        stem = root + "/".join(parts[:size])
        initializer = stem + "/__init__.py"
        if initializer not in files or stem + ".py" in files:
            obstruct("missing/ambiguous production package initializer")
        route_paths.append(initializer)
    route_paths.append(target)
    route = []
    for name in route_paths:
        if (modes.get(name) not in REGULAR or test_scope(name, config) or any(
                name == item.rstrip("/") or name.startswith(item.rstrip("/") + "/")
                for item in config["ini_options"].get("testpaths", []) if item != ".")):
            obstruct("wildcard route has test source or unsupported source kind")
        closed_exports(files[name], name, config)
        route.append({"path": name, "source_sha256": sha(files[name]), "mode": modes[name], "git_blob": blob(files[name])})
    return target, route


def module_bindings(tree):
    names = set()

    def class_globals(node):
        if isinstance(node, FUNCTIONS + (ast.Lambda,)):
            return
        if isinstance(node, ast.Global):
            names.update(node.names)
        for child in ast.iter_child_nodes(node):
            class_globals(child)

    def scan(node):
        if isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            names.add(node.id)
        if isinstance(node, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)) and node.name:
            names.add(node.name)
        if isinstance(node, ast.MatchMapping) and node.rest:
            names.add(node.rest)
        if isinstance(node, FUNCTIONS):
            names.add(node.name)
            args = node.args
            parameters = args.posonlyargs + args.args + args.kwonlyargs
            if args.vararg:
                parameters += [args.vararg]
            if args.kwarg:
                parameters += [args.kwarg]
            expressions = node.decorator_list + args.defaults + args.kw_defaults + [node.returns]
            expressions += [parameter.annotation for parameter in parameters]
            for expression in expressions:
                if expression is not None:
                    scan(expression)
            return
        if isinstance(node, ast.ClassDef):
            names.add(node.name)
            for member in node.body:
                class_globals(member)
            for expression in node.decorator_list + node.bases + [keyword.value for keyword in node.keywords]:
                scan(expression)
            return
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names.update(alias.asname or alias.name.split(".")[0] for alias in node.names if alias.name != "*")
            return
        for child in ast.iter_child_nodes(node):
            scan(child)
    for statement in tree.body:
        scan(statement)
    return names


def local_members(node):
    members = {}
    for statement in node.body:
        if isinstance(statement, DEFINITIONS):
            members[statement.name] = statement
        elif isinstance(statement, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
            for target in targets:
                if isinstance(target, ast.Name):
                    members[target.id] = None
    return members


def class_nodes(filename, tree, config):
    """Independent C3 merge, preserving original declaration and shadow origins."""
    classes, bindings = {}, {"object": "@object"}
    definitions, declarations, routed = {}, {}, set()

    def qualified(node):
        if isinstance(node, ast.Name):
            return bindings.get(node.id)
        if isinstance(node, ast.Attribute):
            parent = qualified(node.value)
            return parent + "." + node.attr if isinstance(parent, str) else None
        return None

    for statement in tree.body:
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                bindings[alias.asname or alias.name.split(".")[0]] = alias.name if alias.asname else alias.name.split(".")[0]
        elif isinstance(statement, ast.ImportFrom):
            for alias in statement.names:
                bindings[alias.asname or alias.name] = (statement.module or "") + "." + alias.name
        elif isinstance(statement, ast.ClassDef):
            if statement.name in classes:
                obstruct("duplicate top-level class mapping")
            bases = [qualified(base) for base in statement.bases]
            bases = ["@TestCase" if base in {"unittest.TestCase", "unittest.case.TestCase"} else base for base in bases]
            classes[statement.name] = (statement, bases or ["@object"])
            bindings[statement.name] = statement.name
        elif isinstance(statement, (ast.Assign, ast.AnnAssign)):
            targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
            value = qualified(statement.value)
            for target in targets:
                if isinstance(target, ast.Name):
                    bindings[target.id] = value
        elif isinstance(statement, FUNCTIONS):
            bindings[statement.name] = None

    cache = {"@object": ["@object"], "@TestCase": ["@TestCase", "@object"]}
    active = set()

    def mro(name):
        if name in cache:
            return cache[name]
        if name not in classes or name in active:
            obstruct("unresolved/cyclic test class ancestry")
        active.add(name)
        try:
            bases = classes[name][1]
            pending = [list(mro(base)) for base in bases] + [list(bases)]
            result = [name]
            while True:
                pending = [sequence for sequence in pending if sequence]
                if not pending:
                    break
                admissible = [sequence[0] for sequence in pending
                              if all(sequence[0] not in other[1:] for other in pending)]
                if not admissible:
                    obstruct("inconsistent C3 test class ancestry")
                selected = admissible[0]
                result.append(selected)
                for sequence in pending:
                    if sequence[0] == selected:
                        del sequence[0]
            cache[name] = result
            return result
        finally:
            active.remove(name)

    for statement in tree.body:
        if isinstance(statement, FUNCTIONS):
            definitions[statement.name] = ast.dump(statement, include_attributes=False)
            if matches(statement.name, config["function_patterns"]):
                declarations[filename + "::" + statement.name] = (statement.name, statement)
                routed.add(statement.name)
    for name, (node, _) in classes.items():
        members = local_members(node)
        for method, declaration in members.items():
            if isinstance(declaration, FUNCTIONS):
                definitions[name + "::" + method] = ast.dump(declaration, include_attributes=False)
        has_tests = any(matches(method, config["function_patterns"] + ["test"]) for method in members)
        try:
            order = mro(name)
        except Obstruction:
            if has_tests or matches(name, config["class_patterns"]):
                raise
            continue
        unittest = "@TestCase" in order
        if not unittest and not matches(name, config["class_patterns"]):
            continue
        selected = {}
        for ancestor in order:
            if ancestor in classes:
                for method, declaration in local_members(classes[ancestor][0]).items():
                    selected.setdefault(method, (ancestor, declaration))
        patterns = ["test"] if unittest else config["function_patterns"]
        for method, (ancestor, declaration) in selected.items():
            if isinstance(declaration, FUNCTIONS) and matches(method, patterns):
                origin = ancestor + "::" + method
                declarations[filename + "::" + name + "::" + method] = (origin, declaration)
                routed.add(origin)
    return declarations, routed, definitions


def collection_declarations(tree):
    declarations = []
    for node in ast.walk(tree):
        names = []
        if isinstance(node, DEFINITIONS):
            names = [node.name]
        elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            names = [child.id for target in targets for child in ast.walk(target) if isinstance(child, ast.Name)]
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.asname or alias.name.split(".")[0] for alias in node.names]
        if any(name.startswith("pytest_") for name in names):
            declarations.append(ast.dump(node, include_attributes=False))
    return sorted(declarations)


class Reconstruction:
    def __init__(self, files, baseline, modes, base_modes, config):
        self.files, self.baseline = files, baseline
        self.modes, self.base_modes = modes, base_modes
        self.config = config
        self.visited = set()
        self.witnesses = {}

    def parse(self, name, raw):
        self.visited.add(name)
        tree = parse_python(raw, name)
        occupied, imported = module_bindings(tree), set()
        for node in tree.body:
            if not isinstance(node, ast.ImportFrom) or not any(alias.name == "*" for alias in node.names):
                continue
            if node.level or len(node.names) != 1:
                obstruct("relative/mixed production wildcard import")
            target, route = import_route(node.module, self.files, self.modes, self.config)
            old_target, old_route = import_route(node.module, self.baseline, self.base_modes, self.config)
            if target != old_target or route != old_route:
                obstruct("production namespace changed across author test overlay")
            exports = closed_exports(self.files[target], target, self.config)
            if set(exports) & (occupied | imported):
                obstruct("production wildcard collides with original module binding")
            imported.update(exports)
            self.witnesses[(name, node.lineno, node.module)] = {
                "test_path": name, "line": node.lineno, "module": node.module, "path": target,
                "source_sha256": sha(self.files[target]), "exports": exports, "route": route}
            node.names = [ast.alias(name=export) for export in exports]
        _grammar.validate_tree(tree, name, self.config["function_patterns"])
        declarations, routed, definitions = class_nodes(name, tree, self.config)
        return tree, declarations, routed, definitions


def check_snapshot(files, modes, label):
    if not isinstance(files, dict) or not isinstance(modes, dict) or set(files) != set(modes):
        obstruct(label + " byte/mode maps must have identical path sets")
    for name, raw in files.items():
        path_of(name)
        if not isinstance(raw, bytes):
            obstruct(label + " needs original byte values")
        if modes[name] not in REGULAR:
            obstruct(label + " contains nonregular source kind needing manual typed audit: " + name)


def derive(files, baseline, modes, base_modes, authority):
    """Return independent derived authority fields; never read claimed selections."""
    if sys.version_info[:2] != (3, 12):
        obstruct("requires original controller Python 3.12 AST grammar")
    if not isinstance(authority, dict):
        raise TypeError("authority must be an object (identity authenticated by caller)")
    check_snapshot(files, modes, "source")
    check_snapshot(baseline, base_modes, "baseline")
    config = configuration(files)
    if any(files.get(name) != baseline.get(name) for name in CONFIG_FILES):
        obstruct("immutable root configuration changed")
    for name in set(modes) | set(base_modes):
        if (modes.get(name), files.get(name)) != (base_modes.get(name), baseline.get(name)):
            if name not in files or not test_scope(name, config):
                obstruct("typed author overlay changes a non-test entry or deletes source")
    changed_paths = sorted(name for name in set(files) | set(baseline) if files.get(name) != baseline.get(name))
    state = Reconstruction(files, baseline, modes, base_modes, config)
    changed, required = {}, set()
    helper_changed = False
    for name in changed_paths:
        if PurePosixPath(name).name == "conftest.py" and name not in baseline:
            obstruct("new conftest requires external authority")
        tree, declarations, routed, definitions = state.parse(name, files[name])
        before_tree = ast.Module(body=[], type_ignores=[])
        prior_definitions = {}
        if name in baseline:
            before_tree, _, _, prior_definitions = state.parse(name, baseline[name])
            if ast.dump(tree, include_attributes=False) == ast.dump(before_tree, include_attributes=False):
                continue
        for origin, declaration in definitions.items():
            if (matches(origin.split("::")[-1], config["function_patterns"] + ["test"]) and
                    prior_definitions.get(origin) != declaration and origin not in routed):
                obstruct("changed assertion has no collected original class mapping: " + origin)
        if collection_declarations(tree) != collection_declarations(before_tree):
            obstruct("changed pytest plugin/collection declarations need external license")
        changed[name] = sha(files[name])
        if module_path(name, config):
            if not declarations:
                obstruct("changed test module has no static collected declarations")
            required.update(declarations)
        else:
            helper_changed = True
    if helper_changed:
        for name, raw in sorted(files.items()):
            if module_path(name, config):
                _, declarations, _, _ = state.parse(name, raw)
                required.update(declarations)
    if not required:
        obstruct("author overlay has no changed native test assertions")

    # Original semantics rebuild current-source witnesses over every visited
    # original module, even byte-only/comment changes skipped by AST delta.
    visited = sorted(state.visited)
    state.witnesses.clear()
    current_declarations = {}
    for name in visited:
        _, declarations, _, _ = state.parse(name, files[name])
        for prefix, (origin, declaration) in declarations.items():
            current_declarations[prefix] = {"path": name, "origin": origin,
                                            "source_sha256": sha(files[name]),
                                            "ast_sha256": sha(ast.dump(declaration, include_attributes=False).encode())}
    if required - current_declarations.keys():
        obstruct("required declaration has no exact current-source C3 origin")
    return {"schema": "UDM_NATIVE_SUITE_AUTHORITY_V45", "derivation": "STATIC_NATIVE_TEST_AST_DELTA_V2",
            "configuration": config, "test_source_sha256": changed, "required_test_nodes": sorted(required),
            "namespace_certificate": {"schema": "UDM_NATIVE_TEST_NAMESPACE_CERTIFICATE_V45",
                "wildcard_imports": [state.witnesses[key] for key in sorted(state.witnesses)],
                "required_declarations": {prefix: current_declarations[prefix] for prefix in sorted(required)}}}


def validate(expected, authority):
    """Compare every derived field exactly; source/commit identity is caller-bound."""
    if not isinstance(expected, dict) or set(expected) != DERIVED_KEYS or not isinstance(authority, dict):
        raise TypeError("independently derived fields and authority objects required")
    if set(authority) != DERIVED_KEYS | IDENTITY_KEYS:
        return {"ok": False, "mismatches": ["authority top-level field set"],
                "derived_sha256": sha(canonical(expected).encode())}
    mismatches = [key for key in sorted(DERIVED_KEYS) if authority.get(key) != expected[key]]
    return {"ok": not mismatches, "mismatches": mismatches,
            "derived_sha256": sha(canonical(expected).encode()),
            "identity_fields_authenticated_by_caller": sorted(IDENTITY_KEYS)}
