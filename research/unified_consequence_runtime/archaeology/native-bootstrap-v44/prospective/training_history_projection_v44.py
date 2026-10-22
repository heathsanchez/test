"""Literal-only V44 input-schema binding of the archived training projection.

The original projection algorithm and V3 output format are preserved. This
input transport grants no native verification or execution authority.
"""
import hashlib
import importlib.util
from pathlib import Path
from types import CodeType, FunctionType

ORIGINAL_SOURCE = Path(__file__).resolve().with_name('training-history-original')/'training_history_projection.py'
ORIGINAL_SOURCE_SHA256 = '3172f8a5d175d593b938db62a48db76437abbbe59c8432a91ea53488ef5f7b21'
SCHEMA_BINDINGS = {
    'UDM_NATIVE_CLI_AUTHORITY_V3': 'UDM_NATIVE_CLI_AUTHORITY_V44',
    'UDM_NATIVE_AGENT_PARENT_RECEIPT_V3': 'UDM_NATIVE_AGENT_PARENT_RECEIPT_V44',
    'UDM_CODING_AGENT_NATIVE_ARM_V3': 'UDM_CODING_AGENT_NATIVE_ARM_V44',
}
if (ORIGINAL_SOURCE.is_symlink() or ORIGINAL_SOURCE.resolve() != ORIGINAL_SOURCE
        or hashlib.sha256(ORIGINAL_SOURCE.read_bytes()).hexdigest() != ORIGINAL_SOURCE_SHA256):
    raise ValueError('archived original training projection source differs')
_spec = importlib.util.spec_from_file_location('_udm_original_training_history_projection', ORIGINAL_SOURCE)
_original = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_original)


def _literals(code):
    for value in code.co_consts:
        if isinstance(value, CodeType):
            yield from _literals(value)
        elif isinstance(value, str):
            yield value


def _literal_code(code):
    constants = tuple(_literal_code(value) if isinstance(value, CodeType)
                      else SCHEMA_BINDINGS.get(value, value) if isinstance(value, str)
                      else value for value in code.co_consts)
    return code if constants == code.co_consts else code.replace(co_consts=constants)


for _old in SCHEMA_BINDINGS:
    if list(_literals(_original.project.__code__)).count(_old) != 1:
        raise ValueError('original projection schema binding site differs: '+_old)
for _name, _value in vars(_original).items():
    if not _name.startswith('__'):
        globals().setdefault(_name, _value)
for _name, _value in tuple(vars(_original).items()):
    if isinstance(_value, FunctionType) and _value.__module__ == _original.__name__:
        _code = _literal_code(_value.__code__)
        _bound = FunctionType(_code, globals(), _name, _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        globals()[_name] = _bound


if __name__ == '__main__':
    main()
