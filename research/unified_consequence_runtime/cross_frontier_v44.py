"""One typed metadata verifier over the original FLASH frontier projection."""
from pathlib import Path
from types import FunctionType

from . import cross_frontier_v43 as previous
from . import cross_frontier as original

METADATA_VERIFICATION = 'native_metadata_verification_v44'
_ORIGINAL_SHA256 = 'bc51d0b1e4c1cb27325baf1e8e67a0f3a4fe769bc5f8916731ded451767e583c'
_PREVIOUS_SHA256 = '4e36f427ea2e5d3dfe128647d7fe7e0280d89ea91ab7196483898c906e9665e5'
_LOADED_SHA256 = original.digest(Path(__file__).read_bytes())


def _guard():
    previous._guard()
    if (original.digest(Path(original.__file__).read_bytes()) != _ORIGINAL_SHA256
            or original.digest(Path(previous.__file__).read_bytes()) != _PREVIOUS_SHA256
            or original.digest(Path(__file__).read_bytes()) != _LOADED_SHA256):
        raise ValueError('UNKNOWN_V44_FRONTIER_BINDING_SOURCE_CHANGED')


def _validator_source(verification_kind):
    _guard()
    if verification_kind == METADATA_VERIFICATION:
        return Path(__file__).with_name('native_bootstrap_runtime_v44.py')
    return previous._validator_source(verification_kind)


_namespace = dict(vars(original), __file__=__file__,
                  VERIFICATION_KINDS=previous.VERIFICATION_KINDS | {METADATA_VERIFICATION},
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
