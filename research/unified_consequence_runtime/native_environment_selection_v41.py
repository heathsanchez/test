"""Tracked tox dependency includes over the source-pinned V4 metadata operation.

The original derivation, requirement validator and recursive file walker remain
their original code objects. A field-sensitive forwarding closure activates the
walker for literal tox includes. No source bytes or catalog authority change.
"""
from pathlib import Path, PurePosixPath
from types import CodeType, FunctionType, SimpleNamespace
import re as _re

from . import native_environment_selection_v4 as previous

PREVIOUS_SHA256 = 'bfb3c57d61bb8bcbb44e8a10c95dbe3162bc3adef58174c9c75eb27e728f0efb'
CONSTRAINT_SCHEMA = 'UDM_NATIVE_ENVIRONMENT_CONSTRAINTS_V41'
SELECTION_SCHEMA = 'UDM_NATIVE_ENVIRONMENT_SELECTION_V41'
CATALOG_SCHEMA = previous.CATALOG_SCHEMA
_Unknown = previous._namespace['_Unknown']
canonicalize_name = previous.canonicalize_name
Requirement = previous.Requirement
_LOADED_SHA256 = previous._hash(Path(__file__).read_bytes())


def _guard():
    previous._guard()
    if (previous._hash(Path(previous.__file__).read_bytes()) != PREVIOUS_SHA256
            or previous._hash(Path(__file__).read_bytes()) != _LOADED_SHA256):
        raise ValueError('UNKNOWN_METADATA_OPERATION_SOURCE_CHANGED')


_namespace = dict(previous._namespace, __name__=__name__, __file__=__file__,
                  CONSTRAINT_SCHEMA=CONSTRAINT_SCHEMA, SELECTION_SCHEMA=SELECTION_SCHEMA)
for _name, _value in previous._namespace.items():
    if isinstance(_value, FunctionType) and _value.__globals__ is previous._namespace:
        _bound = FunctionType(_value.__code__, _namespace, _name,
                              _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        _namespace[_name] = _bound
        globals()[_name] = _bound
_DERIVE = _namespace['derive_constraints']
_nested = {code.co_name: code for code in _DERIVE.__code__.co_consts if isinstance(code, CodeType)}
_ADD, _EVIDENCE, _WALK = (_nested[name] for name in ('add_requirement', 'evidence', 'requirements_file'))
if (_ADD.co_freevars != ('result',) or _EVIDENCE.co_freevars != ('files', 'result')
        or _WALK.co_freevars != ('add_requirement', 'evidence', 'files', 'requirements_file')):
    raise ValueError('UNKNOWN_PINNED_REQUIREMENTS_BINDING')


def _cell(value):
    return (lambda: value).__closure__[0]


def _bind(code, namespace, **values):
    return FunctionType(code, namespace, code.co_name,
                        closure=tuple(_cell(values[name]) for name in code.co_freevars))


def _forward_template():
    result = None
    def add_requirement(value, path, field, extra='', python_versions=None):
        return _dispatch_requirement(result, value, path, field, extra, python_versions)
    return add_requirement.__code__


_FORWARD = _forward_template()
if (_FORWARD.co_freevars != _ADD.co_freevars or _FORWARD.co_argcount != _ADD.co_argcount
        or sum(code is _ADD for code in _DERIVE.__code__.co_consts) != 1):
    raise ValueError('UNKNOWN_PINNED_REQUIREMENTS_DISPATCH_SITE')
_DERIVE_CODE = _DERIVE.__code__.replace(co_consts=tuple(
    _FORWARD if code is _ADD else code for code in _DERIVE.__code__.co_consts))


def _include_target(line):
    if line.startswith('-r') and len(line) > 2 and not line[2].isspace():
        line = '-r ' + line[2:]
    if not line.startswith(('-r ', '--requirement ')):
        return None
    target = line.split(None, 1)[1]
    try:
        if (not target or target.startswith('-') or any(c.isspace() for c in target)
                or any(c in target for c in '{}$')):
            _unknown('UNKNOWN_REQUIREMENT_GRAMMAR', 'nonliteral requirements include')
        _path(target)
    except _Unknown:
        _unknown('UNKNOWN_REQUIREMENT_GRAMMAR', 'noncanonical requirements include')
    return target


def _split(pattern, value, *args, **kwargs):
    parts = _re.split(pattern, value, *args, **kwargs)
    if pattern == r'\s+#' and parts:
        line = parts[0].strip()
        target = _include_target(line)
        if target is not None:
            parts[0] = '-r ' + target
    return parts


_walker_namespace = dict(_namespace, re=SimpleNamespace(**dict(vars(_re), split=_split)))


def derive_constraints(files):
    _guard()
    pending = []
    def dispatch(result, value, path, field, extra, python_versions):
        if path == 'tox.ini' and (field == 'testenv.deps'
                                  or field.startswith('testenv:') and field.endswith('.deps')):
            line = _split(r'\s+#', value)[0].strip()
            target = _include_target(line)
            if target is not None:
                pending.append((target, extra, python_versions))
                return
        return _bind(_ADD, _namespace, result=result)(value, path, field, extra, python_versions)
    context = dict(_walker_namespace, _dispatch_requirement=dispatch)
    result = FunctionType(_DERIVE_CODE, context, 'derive_constraints')(files)
    if result['status'] != 'DERIVED_SOURCE_CONSTRAINTS':
        return result
    try:
        for target, extra, python_versions in pending:
            original_add = _bind(_ADD, _namespace, result=result)
            def add(value, path, field):
                return original_add(value, path, field, extra, python_versions)
            evidence = _bind(_EVIDENCE, _namespace, files=files, result=result)
            cells = {'add_requirement': _cell(add), 'evidence': _cell(evidence),
                     'files': _cell(files), 'requirements_file': _cell(None)}
            walk = FunctionType(_WALK, _walker_namespace, 'requirements_file',
                                ((),), tuple(cells[name] for name in _WALK.co_freevars))
            cells['requirements_file'].cell_contents = walk
            walk(str(PurePosixPath('tox.ini').parent / target))
        result['requirements'].sort(key=_canonical)
        result['evidence'].sort(key=_canonical)
    except _Unknown as error:
        result['status'] = 'UNKNOWN'
        result['reasons'].append({'reason': error.reason, 'detail': error.detail})
    except (UnicodeError, ValueError, TypeError, AttributeError) as error:
        result['status'] = 'UNKNOWN'
        result['reasons'].append({'reason': 'UNKNOWN_METADATA_GRAMMAR', 'detail': str(error)})
    return result


_namespace['derive_constraints'] = derive_constraints
del _name, _value, _bound
