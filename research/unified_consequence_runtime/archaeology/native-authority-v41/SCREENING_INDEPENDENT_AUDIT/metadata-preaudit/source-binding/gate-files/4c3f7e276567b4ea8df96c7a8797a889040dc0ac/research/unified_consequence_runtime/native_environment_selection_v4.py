"""Versioned metadata inference; byte inventory is not executable authority.

The exact V3 derivation and selection bytecode is reused in private globals.
Only setup.py is parsed as Python metadata. All other tracked bytes remain in
the source inventory; actual executable compatibility belongs to independent
native collection/import/execution, never this candidate environment choice.
Unsupported metadata and catalog limitations retain V3's precise UNKNOWNs.
"""
import ast
from pathlib import Path
from types import FunctionType, SimpleNamespace

from . import native_environment_selection_v3 as previous

PREVIOUS_SHA256 = '5a8cbc4a8f3dfa7969516f4bf0a39d3f7720789b764d83764112234834f3af3b'
CONSTRAINT_SCHEMA = 'UDM_NATIVE_ENVIRONMENT_CONSTRAINTS_V4'
SELECTION_SCHEMA = 'UDM_NATIVE_ENVIRONMENT_SELECTION_V4'
CATALOG_SCHEMA = previous.CATALOG_SCHEMA
_LOADED_SHA256 = previous._hash(Path(__file__).read_bytes())


def _guard():
    if (previous._hash(Path(previous.__file__).read_bytes()) != PREVIOUS_SHA256
            or previous._hash(Path(__file__).read_bytes()) != _LOADED_SHA256):
        raise ValueError('UNKNOWN_METADATA_OPERATION_SOURCE_CHANGED')


def _metadata_parse(raw, filename='<unknown>', *args, **kwargs):
    _guard()
    if filename == 'setup.py':
        return ast.parse(raw, filename=filename, *args, **kwargs)
    # This is only the inference parser. No runtime import, compile, collection
    # or original source is intercepted or changed by this scoped AST policy.
    return ast.Module(body=[], type_ignores=[])


_guard()
_namespace = dict(vars(previous), __name__=__name__, __file__=__file__,
                  CONSTRAINT_SCHEMA=CONSTRAINT_SCHEMA, SELECTION_SCHEMA=SELECTION_SCHEMA,
                  ast=SimpleNamespace(**dict(vars(ast), parse=_metadata_parse)))
for _name, _value in vars(previous).items():
    if isinstance(_value, FunctionType) and _value.__module__ == previous.__name__:
        _bound = FunctionType(_value.__code__, _namespace, _name,
                              _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        _namespace[_name] = _bound
        globals()[_name] = _bound

# Existing provisioning consumes the same requirement/catalog types. The
# external catalog schema, pin authority and package semantics are unchanged.
canonicalize_name = previous.canonicalize_name
Requirement = previous.Requirement
del _name, _value, _bound
