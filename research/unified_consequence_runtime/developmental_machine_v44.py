"""Existing Machine plus a source-native metadata observation opcode.

The original Metatron/FLASH algorithms and existing E/D/V54/native branches are
unchanged. Source-native metadata supplies experiment evidence, never permission
or a protected native-outcome verdict.
"""
import inspect
from pathlib import Path
import textwrap

from . import developmental_machine as original
from . import developmental_machine_v43 as previous
from . import cross_frontier_v44 as frontier

Capability, canonical, digest = original.Capability, original.canonical, original.digest
check_source, PINS, EVIDENCE, TRANSITIONS = original.check_source, original.PINS, original.EVIDENCE, original.TRANSITIONS
_ORIGINAL_SHA256 = '4609e5b881abcfb6472d4caa2d542dc9eb1d852cf1c42f00a577aba539ccc241'
_PREVIOUS_SHA256 = '3f1be3ff0f45f3c78edbe89f60eaa2b821e85402c1dc4844e4d7f314ce9d9c8a'
_LOADED_SHA256 = digest(Path(__file__).read_bytes())


def _guard():
    previous._guard()
    frontier._guard()
    if (digest(Path(original.__file__).read_bytes()) != _ORIGINAL_SHA256
            or digest(Path(previous.__file__).read_bytes()) != _PREVIOUS_SHA256
            or digest(Path(__file__).read_bytes()) != _LOADED_SHA256):
        raise ValueError('UNKNOWN_V44_MACHINE_BINDING_SOURCE_CHANGED')


def _replace(source, before, after):
    if source.count(before) != 1:
        raise ValueError('UNKNOWN_V44_MACHINE_BINDING_SITE')
    return source.replace(before, after)


_namespace = dict(vars(original), __file__=__file__)
_reclose_source = _replace(textwrap.dedent(inspect.getsource(original.Machine.reclose)),
    'from .cross_frontier import reclose_frontiers',
    'from .cross_frontier_v44 import reclose_frontiers')
exec(compile(_reclose_source, __file__+':original-reclosure-binding', 'exec'), _namespace)
_reclose = _namespace['reclose']
_select_source = _replace(textwrap.dedent(inspect.getsource(original.Machine.select_and_execute_frontier)),
    'from .cross_frontier import require_frontier_route',
    'from .cross_frontier_v44 import require_frontier_route')
_select_source = _replace(_select_source,
    "    elif cap.operation == 'native.pytest_suite':\n",
    "    elif cap.operation == 'source.materialize_declared_backend':\n"
    "        result, consequence = runtime.execute(capability_id, request)\n"
    "        return {**route, 'materialization': result, 'consequence': consequence,\n"
    "                'transition': 'ACTIVATION', 'new_constructor_invocations': 0}\n"
    "    elif cap.operation == 'source.observe_native_metadata':\n"
    "        result, consequence = runtime.execute(capability_id, request)\n"
    "        return {**route, 'metadata_observation': result, 'consequence': consequence,\n"
    "                'transition': 'ACTIVATION', 'new_constructor_invocations': 0}\n"
    "    elif cap.operation == 'native.pytest_suite':\n")
exec(compile(_select_source, __file__+':original-selection-binding', 'exec'), _namespace)
_select = _namespace['select_and_execute_frontier']


class Machine(previous.Machine):
    def __init__(self, *args, **kwargs):
        _guard()
        super().__init__(*args, **kwargs)

    def reclose(self):
        _guard()
        return _reclose(self)

    def select_and_execute_frontier(self, frontier_id, runtime):
        _guard()
        return _select(self, frontier_id, runtime)


_guard()
