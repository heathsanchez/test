"""Local-only v4 record assembly through unchanged original helper bytecode."""
import importlib.util
from pathlib import Path
from types import FunctionType

from research.unified_consequence_runtime import qualify_native_frontier_v4 as q

_path = q.HERE/'archaeology/native-environment-v3/prepare_records.py'
_expected = '7ab47d2339641a09d5ab2c6e417ed148298477e83bf19f8580b56a9655c6ce5a'
if q.digest(_path.read_bytes()) != _expected:
    raise ValueError('original local-only record assembler source differs')
_spec = importlib.util.spec_from_file_location('_udm_v4_original_record_assembler', _path)
_original = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_original)

for _name, _value in vars(_original).items():
    if not _name.startswith('__'):
        globals().setdefault(_name, _value)
for _name, _value in vars(_original).items():
    if isinstance(_value, FunctionType) and _value.__module__ == _original.__name__:
        _bound = FunctionType(_value.__code__, globals(), _name,
                              _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        globals()[_name] = _bound

if __name__ == '__main__':
    main()
