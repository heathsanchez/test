"""Expose the original request operation without changing native V45 semantics.

Every existing V45 function retains its original object and private bindings.
The single added operation is the already implemented V43 request recorder;
recording an obligation supplies no native warrant or external permission.
"""
from __future__ import annotations

from pathlib import Path

from . import native_environment_v45 as _qualified_environment
from . import native_environment_v43 as _request_source

for _name, _value in vars(_qualified_environment).items():
    if not _name.startswith('__'):
        globals().setdefault(_name, _value)

ACTIVATION_VERSION = 'UDM_NATIVE_REQUEST_ACTIVATION_V1'
record_admission_request = _request_source.record_admission_request
_QUALIFIED_ENVIRONMENT_SHA256 = 'bc33a9924be9bff9a56f59bfbad1b866372e0b5a962fc3d939c669e0e697ec8c'
_REQUEST_SOURCE_SHA256 = 'f419eef3079c70ec10f5fcb1f7f7308156d9ea1f4683780643728920afe83a49'
_LOADED_SHA256 = sha256(Path(__file__).read_bytes())


def _guard():
    if (sha256(Path(__file__).read_bytes()) != _LOADED_SHA256
            or sha256(Path(_qualified_environment.__file__).read_bytes()) != _QUALIFIED_ENVIRONMENT_SHA256
            or sha256(Path(_request_source.__file__).read_bytes()) != _REQUEST_SOURCE_SHA256):
        raise ValueError('UNKNOWN_NATIVE_REQUEST_ACTIVATION_V1_SOURCE_CHANGED')
    _qualified_environment._guard()


_guard()
del _name, _value
