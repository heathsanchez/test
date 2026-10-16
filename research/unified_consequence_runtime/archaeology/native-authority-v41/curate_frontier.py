"""V4.1 metadata-only curation: new gate, empty universe, all prior exclusions."""
import importlib.util
from pathlib import Path
from types import FunctionType

from research.unified_consequence_runtime import qualify_native_frontier_v41 as q

_path = q.HERE/'archaeology/native-authority-v4/curate_frontier.py'
_expected = 'bfd0f38de30b12021090eb9592aebc79c60317c1bccdbcac3487da15f0e1b413'
if q.digest(_path.read_bytes()) != _expected:
    raise ValueError('frozen V4 metadata curator source differs')
_spec = importlib.util.spec_from_file_location('_udm_v41_frozen_curator', _path)
_carrier = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_carrier)

for _name, _value in vars(_carrier).items():
    if not _name.startswith('__'):
        globals().setdefault(_name, _value)

UNIVERSE = ()
RECORDS = q.RECORDS
SCHEMA = 'UDM_NATIVE_AUTHORITY_V41_METADATA_PREQUERY_V1'
EXTRA_HISTORY = (*_carrier.EXTRA_HISTORY, *(('archaeology/native-authority-v4/'+name)
    for name in ('DECLARED_UNIVERSE.json', 'PREQUERY.json', 'PREQUERY_EXECUTION.json',
                 'METADATA_CURATION.json', 'FROZEN_POOL.json', 'SCREENING_AUTHORITY.json',
                 'SCREENING_ENVELOPES.json', 'SCREENING_METER.json')))
_LOADED_SHA256 = q.digest(Path(__file__).read_bytes())
_qualification_binding = None

for _name, _value in tuple(vars(_carrier).items()):
    if isinstance(_value, FunctionType) and _value.__module__ == _carrier.__name__:
        _code = _value.__code__
        if _name == '_base_query':
            _old_import = 'research.unified_consequence_runtime.qualify_native_frontier_v4'
            if _code.co_names.count(_old_import) != 1:
                raise ValueError('frozen V4 metadata gate import binding site differs')
            _code = _code.replace(co_names=tuple(q.MODULE if name == _old_import else name
                                                 for name in _code.co_names))
            _code = q._literal_code(_code, {
                'UDM_COMMITTED_METADATA_PREQUERY_EXECUTION_V4': 'UDM_COMMITTED_METADATA_PREQUERY_EXECUTION_V41',
                'UDM_NATIVE_FRONTIER_METADATA_CURATION_V4': 'UDM_NATIVE_FRONTIER_METADATA_CURATION_V41',
                'UDM_ORDERED_NATIVE_ADMISSION_SCREENING_POOL_V4': 'UDM_ORDERED_NATIVE_ADMISSION_SCREENING_POOL_V41'})
        elif _name == 'configure_universe':
            _code = q._literal_code(_code, {
                'UDM_NATIVE_AUTHORITY_V4_DECLARED_UNIVERSE_V1': 'UDM_NATIVE_AUTHORITY_V41_DECLARED_UNIVERSE_V1'})
        _bound = FunctionType(_code, globals(), _name, _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        globals()[_name] = _bound

if __name__ == '__main__':
    main()
