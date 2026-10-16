"""V4.1 metadata binding; original source/native provisioning stays unchanged."""
from pathlib import Path
from types import FunctionType
from . import native_environment_v3 as previous
from . import native_environment_selection_v41 as selection

PREVIOUS_SHA256 = '7d18bc80ab96fdfc2128e5f8211aef5a2d88750a85bad4d5c96bb4b9bbad4501'
if previous.sha256(Path(previous.__file__).read_bytes()) != PREVIOUS_SHA256:
    raise ValueError('UNKNOWN_FROZEN_ENVIRONMENT_SOURCE_CHANGED')
_namespace = dict(vars(previous), selection=selection)
for _name, _value in vars(previous).items():
    if isinstance(_value, FunctionType) and _value.__module__ == previous.__name__:
        _bound = FunctionType(_value.__code__, _namespace, _name,
                              _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        _namespace[_name] = _bound
        globals()[_name] = _bound
execution = previous.execution
del _name, _value, _bound
