"""Original V45 live-agent watcher with the versioned controller path only.

Model execution, native-meter evidence, source release and all budgets retain
their original algorithms. Importing this helper starts no process or model.
"""
import hashlib
import importlib.util
from types import CodeType, FunctionType

from research.unified_consequence_runtime import qualify_native_frontier_request_v1 as q

ORIGINAL_HELPER_SOURCE = q.HERE/'archaeology/native-namespace-v45/prospective/watch_actual_agent.py'
ORIGINAL_HELPER_SHA256 = '456a003ae0de2c86536515a13a27dee8c8eb19435cb3e6e5a9fd9599dc6fe778'
if ORIGINAL_HELPER_SOURCE.is_symlink() or q.digest(ORIGINAL_HELPER_SOURCE.read_bytes()) != ORIGINAL_HELPER_SHA256:
    raise ValueError('qualified actual-agent watcher source differs')
_spec = importlib.util.spec_from_file_location('_request_qualified_v45_watcher', ORIGINAL_HELPER_SOURCE)
QUALIFIED_HELPER = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(QUALIFIED_HELPER)
for _name, _value in vars(QUALIFIED_HELPER).items():
    if not _name.startswith('__') and _name != 'q':
        globals().setdefault(_name, _value)


def _request_code(code):
    paths = {'research/unified_consequence_runtime/qualify_native_frontier_v45.py':
                'research/unified_consequence_runtime/qualify_native_frontier_request_v1.py',
             'research.unified_consequence_runtime.qualify_native_frontier_v45':
                'research.unified_consequence_runtime.qualify_native_frontier_request_v1'}
    constants = tuple(_request_code(value) if isinstance(value, CodeType)
                      else paths.get(value, value) if isinstance(value, str) else value for value in code.co_consts)
    return code if constants == code.co_consts else code.replace(co_consts=constants)


for _name, _value in tuple(vars(QUALIFIED_HELPER).items()):
    if isinstance(_value, FunctionType) and _value.__globals__ is vars(QUALIFIED_HELPER):
        _bound = FunctionType(_request_code(_value.__code__), globals(), _name, _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        globals()[_name] = _bound


if __name__ == '__main__':
    main()
