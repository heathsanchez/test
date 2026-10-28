"""Independent source-only validation of bounded pytest collection statements.

``validate_tree(tree, path, function_patterns)`` accepts an already parsed AST
and returns None, or raises Obstruction.  The caller must first replace approved
top-level wildcard imports with their independently proven explicit names.
This module never imports source modules or executes/compiles fixture code.
It validates collection-scope declarations only; C3 mapping is the caller's job.

The rules were read as data from native_admission_v2._test_nodes.  They are
re-expressed here with an independent stateful traversal.  In particular,
ordinary test bodies retain Python semantics, while collection statements and
ordinary initializer helper bodies cannot register tests through the bounded
set of visible namespace primitives accepted by the original authority.
"""

import ast
import fnmatch


class Obstruction(ValueError):
    """Source lies outside the bounded original collection grammar."""


_FUNCS = (ast.FunctionDef, ast.AsyncFunctionDef)
_DEFS = _FUNCS + (ast.ClassDef,)
_WRITES = (ast.Assign, ast.AnnAssign, ast.AugAssign)
_NAMESPACE = frozenset(("globals", "locals", "vars", "setattr", "delattr", "exec", "eval"))


def _stop(detail):
    raise Obstruction("INDEPENDENT_SOURCE_OBSTRUCTION: " + detail)


class _Grammar:
    def __init__(self, tree, path, patterns):
        self.tree = tree
        self.path = path
        self.patterns = tuple(dict.fromkeys(list(patterns) + ["test"]))
        self.seen_prefixes = set()
        self.direct_tests = set()
        # The original traversal updates the module fallback only after its
        # complete first pass, so nested classes see this initial empty map.
        self.module_fallback = {}

    def test_name(self, name):
        for pattern in self.patterns:
            if any(char in pattern for char in "*?["):
                if fnmatch.fnmatchcase(name, pattern):
                    return True
            elif name.startswith(pattern):
                return True
        return False

    def noncallable(self, expression, known):
        """Only the value's callable kind matters, including container values."""
        if isinstance(expression, (ast.Constant, ast.List, ast.Tuple, ast.Set, ast.Dict)):
            return True
        if isinstance(expression, ast.Name):
            return known.get(expression.id, False)
        if isinstance(expression, ast.UnaryOp) and isinstance(
                expression.op, (ast.UAdd, ast.USub, ast.Invert, ast.Not)):
            return self.noncallable(expression.operand, known)
        return False

    def inert_expression(self, expression, known):
        """Whether evaluating this syntax preserves previously known values."""
        if expression is None or isinstance(expression, (ast.Name, ast.Constant)):
            return True
        if isinstance(expression, (ast.List, ast.Tuple)):
            return all(not isinstance(part, ast.Starred) and
                       self.inert_expression(part, known) for part in expression.elts)
        if isinstance(expression, (ast.Set, ast.Dict)):
            try:
                ast.literal_eval(expression)
            except (ValueError, TypeError, SyntaxError):
                return False
            return True
        if isinstance(expression, ast.UnaryOp):
            return self.noncallable(expression.operand, known)
        return False

    def preserves_values(self, statement, known):
        if isinstance(statement, _FUNCS):
            args = statement.args
            parameters = list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs)
            if args.vararg is not None:
                parameters.append(args.vararg)
            if args.kwarg is not None:
                parameters.append(args.kwarg)
            evaluated = list(args.defaults) + list(args.kw_defaults)
            evaluated += [parameter.annotation for parameter in parameters]
            evaluated.append(statement.returns)
            return (not statement.decorator_list and
                    all(self.inert_expression(item, known) for item in evaluated))
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            return (self.inert_expression(statement.value, known) and
                    self.inert_expression(getattr(statement, "annotation", None), known))
        if isinstance(statement, ast.Expr):
            return self.inert_expression(statement.value, known)
        return isinstance(statement, (ast.Pass, ast.Global, ast.Nonlocal))

    def target_names(self, target):
        if isinstance(target, ast.Name):
            return [target.id]
        if isinstance(target, (ast.Tuple, ast.List)):
            names = []
            for element in target.elts:
                names.extend(self.target_names(element))
            return names
        if isinstance(target, ast.Starred):
            return self.target_names(target.value)
        if isinstance(target, (ast.Subscript, ast.Attribute)):
            _stop("dynamic namespace write unsupported")
        return []

    def primitive(self, node):
        return ((isinstance(node, ast.Name) and node.id in _NAMESPACE) or
                (isinstance(node, ast.Attribute) and node.attr in _NAMESPACE))

    def check_evaluation(self, node):
        """Inspect only immediately evaluated pieces of definitions."""
        if isinstance(node, _DEFS):
            expressions = list(node.decorator_list)
            if isinstance(node, ast.ClassDef):
                expressions.extend(node.bases)
                expressions.extend(keyword.value for keyword in node.keywords)
            else:
                expressions.extend(node.args.defaults)
                expressions.extend(item for item in node.args.kw_defaults if item is not None)
                if not self.test_name(node.name):
                    for inner in ast.walk(node):
                        if self.primitive(inner):
                            _stop("initializer helper test registration unsupported")
                        if isinstance(inner, (ast.Global, ast.Nonlocal)) and any(
                                self.test_name(name) for name in inner.names):
                            _stop("initializer helper test registration unsupported")
            for expression in expressions:
                self.check_evaluation(expression)
            return
        for evaluated in ast.walk(node):
            if self.primitive(evaluated):
                _stop("dynamic test registration primitive unsupported")
            if isinstance(evaluated, ast.Call) and isinstance(evaluated.func, ast.Name):
                if self.test_name(evaluated.func.id):
                    _stop("collection-time test callable execution unsupported")
            if isinstance(evaluated, ast.NamedExpr) and any(
                    self.test_name(name) for name in self.target_names(evaluated.target)):
                _stop("conditional test binding unsupported")

    def ambiguous_statement(self, statement, known):
        """Invalidate possible conditional writes and reject test writes."""
        for descendant in ast.walk(statement):
            if isinstance(descendant, _FUNCS) and self.test_name(descendant.name):
                _stop("conditional or nested test definition unsupported")
            names = []
            if isinstance(descendant, ast.Name) and isinstance(descendant.ctx, (ast.Store, ast.Del)):
                names.append(descendant.id)
            elif isinstance(descendant, (ast.ExceptHandler, ast.MatchAs, ast.MatchStar)):
                if descendant.name:
                    names.append(descendant.name)
            for name in names:
                if self.test_name(name):
                    _stop("conditional test binding unsupported")
                known[name] = False

    def scope(self, body, prefix, inherited):
        known = dict(inherited)
        for statement in body:
            self.check_evaluation(statement)
            if not self.preserves_values(statement, known):
                known = dict.fromkeys(known, False)
            if isinstance(statement, _FUNCS):
                if self.test_name(statement.name):
                    key = prefix + "::" + statement.name
                    if key in self.seen_prefixes:
                        _stop("duplicate test definition unsupported")
                    self.seen_prefixes.add(key)
                    self.direct_tests.add(id(statement))
                known[statement.name] = False
                continue
            if isinstance(statement, ast.ClassDef):
                if self.test_name(statement.name):
                    _stop("test callable class alias unsupported")
                fallback = known if prefix == self.path else self.module_fallback
                self.scope(statement.body, prefix + "::" + statement.name, fallback)
                known[statement.name] = False
                continue
            if isinstance(statement, _WRITES):
                targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
                names = [name for target in targets for name in self.target_names(target)]
                direct_names = all(isinstance(target, ast.Name) for target in targets)
                data = (not isinstance(statement, ast.AugAssign) and direct_names and
                        self.noncallable(statement.value, known))
                if not data and any(self.test_name(name) for name in names):
                    _stop("dynamic test alias unsupported")
                for name in names:
                    known[name] = data and direct_names
                continue
            if isinstance(statement, (ast.Import, ast.ImportFrom)):
                for alias in statement.names:
                    if alias.name == "*":
                        _stop("unresolved wildcard imported tests unsupported")
                    name = alias.asname or alias.name.split(".")[0]
                    if self.test_name(name) or alias.name.split(".")[-1] in _NAMESPACE:
                        _stop("imported test callable or registration primitive unsupported")
                    known[name] = False
                continue
            if isinstance(statement, ast.Delete):
                for target in statement.targets:
                    for name in self.target_names(target):
                        if self.test_name(name):
                            _stop("test deletion unsupported")
                        known[name] = False
                continue
            self.ambiguous_statement(statement, known)
        return known

    def validate(self):
        self.module_fallback.update(self.scope(self.tree.body, self.path, self.module_fallback))
        for node in ast.walk(self.tree):
            if isinstance(node, _FUNCS) and self.test_name(node.name):
                if id(node) not in self.direct_tests:
                    _stop("conditional or nested test definition unsupported")
        for top in self.tree.body:
            if isinstance(top, ast.ClassDef):
                for member in top.body:
                    if isinstance(member, ast.ClassDef) and any(
                            isinstance(node, _FUNCS) and self.test_name(node.name)
                            for node in ast.walk(member)):
                        _stop("nested class test mapping unsupported")


def validate_tree(tree, path, function_patterns):
    """Validate an already parsed tree without imports, compilation or execution."""
    if not isinstance(tree, ast.Module) or not isinstance(path, str):
        raise TypeError("a module AST and its logical path are required")
    if not isinstance(function_patterns, (list, tuple)) or any(
            not isinstance(pattern, str) for pattern in function_patterns):
        raise TypeError("function_patterns must be a sequence of strings")
    _Grammar(tree, path, function_patterns).validate()
    return None
