"""V45 input-schema binding of the unchanged original training projection."""
import hashlib
import importlib.util
from pathlib import Path
from types import CodeType, FunctionType

_path = Path(__file__).resolve().parents[2]/'native-bootstrap-v44/prospective/training_history_projection_v44.py'
_pin = '6d7bb4e634a1ac01dc86ed4ca8367223368c249033efcd368abc8f22ec7385d9'
if _path.is_symlink() or hashlib.sha256(_path.read_bytes()).hexdigest() != _pin:
    raise ValueError('original training-history carrier source differs')
_spec = importlib.util.spec_from_file_location('_udm_v45_original_training_projection', _path)
_carrier = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_carrier)


def _transport(code):
    constants = tuple(_transport(value) if isinstance(value, CodeType) else
        value.replace('_V44', '_V45') if isinstance(value, str) and value.startswith('UDM_')
        else value for value in code.co_consts)
    return code if constants == code.co_consts else code.replace(co_consts=constants)


for _name, _value in vars(_carrier).items():
    if not _name.startswith('__'):
        globals().setdefault(_name, _value)
for _name, _value in tuple(vars(_carrier).items()):
    if isinstance(_value, FunctionType) and _value.__module__ == _carrier.__name__:
        _bound = FunctionType(_transport(_value.__code__), globals(), _name, _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        globals()[_name] = _bound


if __name__ == '__main__':
    main()
