"""Local-only V4.1 record assembly over preserved V4 helper bytecode."""
import importlib.util
from pathlib import Path
from types import FunctionType

from research.unified_consequence_runtime import qualify_native_frontier_v41 as q

_path = q.HERE/'archaeology/native-authority-v4/prepare_records.py'
_expected = 'f9f1ad136596354256ac1f0d5e6ff6006551856daa73d9d0508da9b3bd4916b8'
if q.digest(_path.read_bytes()) != _expected:
    raise ValueError('frozen V4 local-only record assembler source differs')
_spec = importlib.util.spec_from_file_location('_udm_v41_frozen_record_assembler', _path)
_carrier = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_carrier)

for _name, _value in vars(_carrier).items():
    if not _name.startswith('__'):
        globals().setdefault(_name, _value)
for _name, _value in tuple(vars(_carrier).items()):
    if isinstance(_value, FunctionType) and _value.__module__ == _carrier.__name__:
        _bound = FunctionType(_value.__code__, globals(), _name,
                              _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        globals()[_name] = _bound

if __name__ == '__main__':
    main()
