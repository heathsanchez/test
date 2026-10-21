"""Original Machine with versioned frontier imports and one source operation.

Metatron, CAS, support projection, FLASH, withdrawal and the existing selection
branches remain the original implementations. No original globals are changed.
"""
import inspect
from pathlib import Path
import textwrap
import time

from . import developmental_machine as original
from . import cross_frontier_v43 as frontier

Capability = original.Capability
canonical, digest, check_source = original.canonical, original.digest, original.check_source
PINS, EVIDENCE, TRANSITIONS = original.PINS, original.EVIDENCE, original.TRANSITIONS
_ORIGINAL_SHA256 = digest(Path(original.__file__).read_bytes())
_LOADED_SHA256 = digest(Path(__file__).read_bytes())


def _guard():
    frontier._guard()
    if (digest(Path(original.__file__).read_bytes()) != _ORIGINAL_SHA256
            or digest(Path(__file__).read_bytes()) != _LOADED_SHA256):
        raise ValueError('UNKNOWN_V43_MACHINE_BINDING_SOURCE_CHANGED')


def _replace(source, before, after):
    if source.count(before) != 1:
        raise ValueError('UNKNOWN_V43_MACHINE_BINDING_SITE')
    return source.replace(before, after)


_namespace = dict(vars(original), __file__=__file__)
_reclose_source = _replace(textwrap.dedent(inspect.getsource(original.Machine.reclose)),
    'from .cross_frontier import reclose_frontiers',
    'from .cross_frontier_v43 import reclose_frontiers')
exec(compile(_reclose_source, __file__ + ':original-reclosure-binding', 'exec'), _namespace)
_reclose = _namespace['reclose']
_select_source = _replace(textwrap.dedent(inspect.getsource(original.Machine.select_and_execute_frontier)),
    'from .cross_frontier import require_frontier_route',
    'from .cross_frontier_v43 import require_frontier_route')
_select_source = _replace(_select_source,
    "    elif cap.operation == 'native.pytest_suite':\n",
    "    elif cap.operation == 'source.materialize_declared_backend':\n"
    "        result, consequence = runtime.execute(capability_id, request)\n"
    "        return {**route, 'materialization': result, 'consequence': consequence,\n"
    "                'transition': 'ACTIVATION', 'new_constructor_invocations': 0}\n"
    "    elif cap.operation == 'native.pytest_suite':\n")
exec(compile(_select_source, __file__ + ':original-selection-binding', 'exec'), _namespace)
_select = _namespace['select_and_execute_frontier']


class Machine(original.Machine):
    def __init__(self, *args, **kwargs):
        _guard()
        super().__init__(*args, **kwargs)
        # Both original FLASH router/closure factories require real events.
        # The existing user research ceiling is an actual external input, also
        # retained by both original native adapters; it grants no native result.
        if not hasattr(self, 'flash'):
            if self.log or self.prior_flash:
                raise ValueError('missing original FLASH view for a nonempty state')
            started = time.perf_counter()
            from .native_runtime_v2 import AUTHORITY
            ceiling = original.json.loads(canonical(AUTHORITY))
            authority_record = self.append('execution_authority_ceiling', ceiling)
            self.flush()
            agrees = set(self.mt.live_ids(self.log)) == self.flash_live_ids()
            if not agrees:
                raise AssertionError('original initial FLASH disagrees with Metatron')
            self.costs.append({'phase': 'original_research_authority_initialization',
                'seconds': time.perf_counter() - started,
                'authority_record': authority_record, 'closure_agrees': agrees})

    def reclose(self):
        _guard()
        return _reclose(self)

    def select_and_execute_frontier(self, frontier_id, runtime):
        _guard()
        return _select(self, frontier_id, runtime)


_guard()
