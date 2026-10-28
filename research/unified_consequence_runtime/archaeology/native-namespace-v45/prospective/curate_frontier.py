"""V45 metadata-only carrier; no declared universe or query on import.

The original scanner/order/no-resampling rule remains. All four actual archived
qualifications and the latest complete prior-exposure union precede any query.
"""
import importlib.util
from pathlib import Path
from types import FunctionType

from research.unified_consequence_runtime import qualify_native_frontier_v45 as q

_path = q.HERE/'archaeology/native-bootstrap-v44/prospective/curate_frontier.py'
_pin = '3d79e607f8f07a08861ff0363c92bfd811e2924c8699bd8126209f2fd3dd4d04'
if _path.is_symlink() or q.digest(_path.read_bytes()) != _pin:
    raise ValueError('original V44 metadata curator differs')
_spec = importlib.util.spec_from_file_location('_udm_v45_original_curator', _path)
_carrier = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_carrier)
for _name, _value in vars(_carrier).items():
    if not _name.startswith('__'):
        globals().setdefault(_name, _value)
for _name, _value in tuple(vars(_carrier).items()):
    if (isinstance(_value, FunctionType) and _value.__module__ == _carrier.__name__
            and _name not in ('configure_universe', '_exposure_record', 'main')):
        _bound = FunctionType(_value.__code__, globals(), _name, _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        globals()[_name] = _bound

UNIVERSE = ()
RECORDS = q.RECORDS
SCHEMA = 'UDM_NATIVE_AUTHORITY_V45_METADATA_PREQUERY_V1'
_LATEST_HISTORY = 'archaeology/native-bootstrap-v44/prospective-result/PROSPECTIVE_EXPOSURE_ADDENDUM.json'
_LATEST_SHA256 = 'dd412ec8015543990f80afc26ca3867eadd0ce94725960e73368abdf9b68898a'
EXTRA_HISTORY = (*_carrier.EXTRA_HISTORY, _LATEST_HISTORY,
    *(('archaeology/native-bootstrap-v44/prospective/'+name) for name in (
        'DECLARED_UNIVERSE.json', 'PREQUERY.json', 'PREQUERY_EXECUTION.json', 'METADATA_CURATION.json',
        'FROZEN_POOL.json', 'SCREENING_AUTHORITY.json')))
_LOADED_SHA256 = q.digest(Path(__file__).read_bytes())
_qualification_binding = None


def _exposure_record():
    previous = _carrier._exposure_record()
    path = q.HERE/_LATEST_HISTORY
    if path.is_symlink() or not path.is_file() or q.digest(path.read_bytes()) != _LATEST_SHA256:
        raise ValueError('latest complete prior exposure addendum differs')
    addendum = json.loads(path.read_text())
    if (addendum.get('schema') != 'UDM_V44_PROSPECTIVE_EXPOSURE_ADDENDUM'
            or any(addendum.get('verdicts', {}).get('G'+str(i)) != 'UNKNOWN' for i in range(2, 7))):
        raise ValueError('latest prior exposure lineage differs')
    repositories = sorted(set(previous['repositories']) | set(addendum['conservative_prior_union']))
    return {'schema': 'UDM_NATIVE_NAMESPACE_V45_PRIOR_EXPOSURE_V1',
            'repositories': repositories, 'repository_count': len(repositories),
            'input_files_sha256': {**previous['input_files_sha256'],
                'archaeology/native-bootstrap-v44/prospective/PRIOR_EXPOSURE.json': _carrier._EXPOSURE_SHA256,
                _LATEST_HISTORY: _LATEST_SHA256},
            'boundary': previous['boundary']}


def configure_universe(universe_path, gate_path, artifact_path, interface_artifact_path,
                       bootstrap_artifact_path, namespace_artifact_path):
    """Authenticate gates/artifact bytes and exposure before reading names."""
    global UNIVERSE, _qualification_binding
    wrapper = json.loads(Path(gate_path).resolve().read_text())
    q.require_environment_gate(wrapper)
    keys = {'catalog', *q.GATE_KEYS}
    if set(wrapper) != keys:
        raise ValueError('exact four-qualified V45 gate wrapper required')
    for path, key in ((artifact_path, 'environment_gate'), (interface_artifact_path, 'interface_gate'),
                      (bootstrap_artifact_path, 'bootstrap_gate'), (namespace_artifact_path, 'namespace_gate')):
        supplied = Path(path).absolute()
        if (supplied.is_symlink() or supplied.resolve() != supplied or not supplied.is_file()
                or q.digest(supplied.read_bytes()) != wrapper[key]['artifact_sha256']):
            raise ValueError('archived qualification artifact digest differs: '+key)
    exposed = _exposure_record()
    supplied = Path(universe_path).absolute()
    universe_path = supplied.resolve()
    if (universe_path != (RECORDS/'DECLARED_UNIVERSE.json').resolve()
            or supplied != universe_path or supplied.is_symlink()):
        raise ValueError('canonical declared universe record required')
    universe = json.loads(universe_path.read_text())
    if (not isinstance(universe, dict) or set(universe) != {'schema', 'repositories', *q.GATE_KEYS}
            or universe.get('schema') != 'UDM_NATIVE_AUTHORITY_V45_DECLARED_UNIVERSE_V1'
            or any(universe.get(key) != wrapper[key] for key in q.GATE_KEYS)):
        raise ValueError('new universe must bind exact independently qualified V45 gate chain')
    names = universe['repositories']
    if (not isinstance(names, list) or not 1 <= len(names) <= SCREENING_BUDGET['maximum_cases']
            or any(not isinstance(name, str) or not re.fullmatch(r'[a-z0-9_.-]+/[a-z0-9_.-]+', name) for name in names)
            or names != sorted(set(names))):
        raise ValueError('one to nine sorted unique lowercase repositories required')
    touched, _ = exclusions(q.HERE, original(q.HERE))
    if not set(exposed['repositories']) <= set(touched) or any(name in touched for name in names):
        raise ValueError('prior exposure union incomplete or declared repository already exposed')
    root = q.HERE.parents[1]
    if not universe_path.is_relative_to(root):
        raise ValueError('declared universe must be an ordinary repository record')
    proposed = {'universe': {'path': universe_path.relative_to(root).as_posix(),
                            'sha256': q.digest(universe_path.read_bytes())},
                'qualified_gate_wrapper': wrapper,
                'prior_exposure_sha256': q.worker.fingerprint(exposed)}
    if _qualification_binding is not None and (UNIVERSE != tuple(names) or _qualification_binding != proposed):
        raise ValueError('preserve first declared universe; use a new version')
    UNIVERSE, _qualification_binding = tuple(names), proposed
    return proposed


_base_query = _source_binding(_carrier._carrier._base_query, (
    ("{'environment_gate', 'catalog'}", repr({'catalog', *q.GATE_KEYS})),
    ('from research.unified_consequence_runtime.qualify_native_frontier_v3 import require_environment_gate',
     'from research.unified_consequence_runtime.qualify_native_frontier_v45 import require_environment_gate'),
    ("'UDM_COMMITTED_METADATA_PREQUERY_EXECUTION_V3'", "'UDM_COMMITTED_METADATA_PREQUERY_EXECUTION_V45'"),
    ("'UDM_NATIVE_FRONTIER_METADATA_CURATION_V3'", "'UDM_NATIVE_FRONTIER_METADATA_CURATION_V45'"),
    ("'UDM_ORDERED_NATIVE_ADMISSION_SCREENING_POOL_V3'", "'UDM_ORDERED_NATIVE_ADMISSION_SCREENING_POOL_V45'"),
    ("'environment_gate': verified_gate,", "'environment_gate': gate['environment_gate'],\n"
     "        'interface_gate': gate['interface_gate'], 'interface_archive_audit': gate['interface_archive_audit'],\n"
     "        'bootstrap_gate': gate['bootstrap_gate'], 'bootstrap_archive_audit': gate['bootstrap_archive_audit'],\n"
     "        'namespace_gate': gate['namespace_gate'], 'namespace_archive_audit': gate['namespace_archive_audit'],\n"
     "        'qualified_gate_chain': verified_gate,"),
))
main = _source_binding(_carrier.main, (
    ("parser.add_argument('--bootstrap-qualification-artifact', type=Path, required=True)",
     "parser.add_argument('--bootstrap-qualification-artifact', type=Path, required=True)\n"
     "    parser.add_argument('--namespace-qualification-artifact', type=Path, required=True)"),
    ('args.interface_qualification_artifact, args.bootstrap_qualification_artifact)',
     'args.interface_qualification_artifact, args.bootstrap_qualification_artifact, args.namespace_qualification_artifact)'),
))


if __name__ == '__main__':
    main()
