"""Exact V45 training projection, loaded from controller-rooted original source.

The original V45 input headers, V3 output and training-only observation boundary
are unchanged. Import and projection never execute native tests or a model.
"""
import importlib.util
from types import FunctionType

from research.unified_consequence_runtime import qualify_native_frontier_request_v1 as q

ORIGINAL_HELPER_SOURCE = q.HERE/'archaeology/native-namespace-v45/prospective/training_history_projection_v45.py'
ORIGINAL_HELPER_SHA256 = '4be377306c5c4c6b4f51a279b6f7cde8fc2b0fb0e79480ccbe2970880384995c'
if ORIGINAL_HELPER_SOURCE.is_symlink() or q.digest(ORIGINAL_HELPER_SOURCE.read_bytes()) != ORIGINAL_HELPER_SHA256:
    raise ValueError('qualified training-history projection source differs')
_spec = importlib.util.spec_from_file_location('_request_qualified_v45_training_projection', ORIGINAL_HELPER_SOURCE)
QUALIFIED_HELPER = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(QUALIFIED_HELPER)
for _name, _value in vars(QUALIFIED_HELPER).items():
    if not _name.startswith('__') and _name != 'q':
        globals().setdefault(_name, _value)
for _name, _value in tuple(vars(QUALIFIED_HELPER).items()):
    if isinstance(_value, FunctionType) and _value.__globals__ is vars(QUALIFIED_HELPER):
        _bound = FunctionType(_value.__code__, globals(), _name, _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        globals()[_name] = _bound


if __name__ == '__main__':
    main()
