"""Literal-only V45 transport of the original actual Codex/native watcher.

No arm is published and no model process starts on import. The original raw
JSON telemetry, real native meter requirements and all budgets are unchanged.
"""
import hashlib
import importlib.util
from pathlib import Path
from types import CodeType, FunctionType

_path = Path(__file__).resolve().parents[2]/'native-bootstrap-v44/prospective/watch_actual_agent.py'
_pin = '608386225e0b129e781bf8f645a7968a69701c273d3e8db4703864731b06d99a'
if _path.is_symlink() or hashlib.sha256(_path.read_bytes()).hexdigest() != _pin:
    raise ValueError('original actual-agent watcher source differs')
_spec = importlib.util.spec_from_file_location('_udm_v45_original_actual_agent', _path)
_original = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_original)


def _transport(code):
    constants = tuple(_transport(value) if isinstance(value, CodeType) else
        value.replace('_V44', '_V45').replace('qualify_native_frontier_v44', 'qualify_native_frontier_v45')
        if isinstance(value, str) else value for value in code.co_consts)
    return code if constants == code.co_consts else code.replace(co_consts=constants)


for _name, _value in vars(_original).items():
    if not _name.startswith('__'):
        globals().setdefault(_name, _value)
for _name, _value in tuple(vars(_original).items()):
    if isinstance(_value, FunctionType) and _value.__module__ == _original.__name__:
        _bound = FunctionType(_transport(_value.__code__), globals(), _name, _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        globals()[_name] = _bound


if __name__ == '__main__':
    main()
