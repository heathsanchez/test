"""Narrow materialization checker binding of the original FLASH projection.

The original projection functions retain their code objects and private globals.
Generic native pytest publication retains its original, unlicensed boundary.
"""
from pathlib import Path
from types import FunctionType

from . import cross_frontier as original

MATERIALIZATION_VERIFICATION = 'native_materialization_verification_v43'
_ORIGINAL_SHA256 = 'bc51d0b1e4c1cb27325baf1e8e67a0f3a4fe769bc5f8916731ded451767e583c'
_LOADED_SHA256 = original.digest(Path(__file__).read_bytes())


def _guard():
    if (original.digest(Path(original.__file__).read_bytes()) != _ORIGINAL_SHA256
            or original.digest(Path(__file__).read_bytes()) != _LOADED_SHA256):
        raise ValueError('UNKNOWN_V43_FRONTIER_BINDING_SOURCE_CHANGED')


def _validator_source(verification_kind):
    _guard()
    if verification_kind == MATERIALIZATION_VERIFICATION:
        return Path(__file__).with_name('native_materialization_v43.py')
    return original._validator_source(verification_kind)


_namespace = dict(vars(original), __file__=__file__,
                  VERIFICATION_KINDS=original.VERIFICATION_KINDS | {MATERIALIZATION_VERIFICATION},
                  _validator_source=_validator_source)
for _name, _value in vars(original).items():
    if not _name.startswith('__') and not isinstance(_value, FunctionType):
        globals()[_name] = _namespace[_name]
for _name, _value in vars(original).items():
    if (isinstance(_value, FunctionType) and _value.__module__ == original.__name__
            and _name != '_validator_source'):
        _bound = FunctionType(_value.__code__, _namespace, _name,
                              _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        globals()[_name] = _namespace[_name] = _bound
_guard()
