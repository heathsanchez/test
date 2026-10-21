"""Local-only V42 assembly over the unchanged original record procedures."""
import importlib.util
from pathlib import Path
from types import FunctionType

from research.unified_consequence_runtime import qualify_native_frontier_v42 as q

_path = q.HERE/'archaeology/native-authority-v41/prepare_records.py'
_expected = 'd8894e568041dcd0dec7aedc766bf18a6312ee444ac615a8c5e860b08cd9b7b5'
if q.digest(_path.read_bytes()) != _expected:
    raise ValueError('frozen V41 local-only record assembler source differs')
_spec = importlib.util.spec_from_file_location('_udm_v42_frozen_record_assembler', _path)
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
