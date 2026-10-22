"""V44 metadata-only transport; no declared universe or query on import.

The original scanner, order, exclusions and first-receipt guard stay. A separate
bootstrap qualification is mandatory alongside the preserved older gates.
"""
import importlib.util
import inspect
from pathlib import Path
from types import FunctionType

from research.unified_consequence_runtime import qualify_native_frontier_v44 as q

_path = q.HERE/'archaeology/native-authority-v42/curate_frontier.py'
_expected = '0ebd3bd5f51f40f7db547aafd986e99a255bc017bb71a5e4923fc5c97d6c659e'
if q.digest(_path.read_bytes()) != _expected:
    raise ValueError('frozen V42 metadata curator source differs')
_spec = importlib.util.spec_from_file_location('_udm_v44_frozen_curator', _path)
_carrier = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_carrier)
for _name, _value in vars(_carrier).items():
    if not _name.startswith('__'):
        globals().setdefault(_name, _value)
for _name, _value in tuple(vars(_carrier).items()):
    if isinstance(_value, FunctionType) and _value.__module__ == _carrier.__name__:
        _bound = FunctionType(_value.__code__, globals(), _name, _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        globals()[_name] = _bound

UNIVERSE = ()
RECORDS = q.RECORDS
SCHEMA = 'UDM_NATIVE_AUTHORITY_V44_METADATA_PREQUERY_V1'
EXTRA_HISTORY = (*_carrier.EXTRA_HISTORY, *(('archaeology/native-authority-v42/'+name)
    for name in ('DECLARED_UNIVERSE.json', 'PREQUERY.json', 'PREQUERY_EXECUTION.json',
                 'METADATA_CURATION.json', 'FROZEN_POOL.json', 'SCREENING_AUTHORITY.json',
                 'SCREENING_ENVELOPES.json', 'SCREENING_METER.json', 'SCREENING_SHORTFALL.json')),
    *(('archaeology/experiment-interface-v43/prospective/'+name) for name in ('DECLARED_UNIVERSE.json','PREQUERY_V2.json','PREQUERY_EXECUTION.json','METADATA_CURATION.json','FROZEN_POOL.json','SCREENING_AUTHORITY.json')),
    'archaeology/experiment-interface-v43/prospective-result/PROSPECTIVE_EXPOSURE_ADDENDUM.json',
    'archaeology/native-bootstrap-v44/prospective/PRIOR_EXPOSURE.json')
_EXPOSURE_SHA256 = 'f8716f3720a63f65ec2551bc8230712b75c42915010ccc59847e3bf29ce3e818'
_LOADED_SHA256 = q.digest(Path(__file__).read_bytes())
_qualification_binding = None


def _source_binding(function, substitutions):
    text = inspect.getsource(function)
    for old, new in substitutions:
        if text.count(old) != 1:
            raise ValueError('frozen V44 curator binding site differs: '+old)
        text = text.replace(old, new)
    namespace = dict(globals())
    exec(compile(text, __file__+':bound-'+function.__name__, 'exec'), namespace)
    compiled = namespace[function.__code__.co_name]
    return FunctionType(compiled.__code__, globals(), compiled.__name__, compiled.__defaults__, compiled.__closure__)


_base_query = _source_binding(_carrier._base_query, (
    ("{'environment_gate', 'catalog'}", "{'environment_gate', 'catalog', 'interface_gate', 'interface_archive_audit', 'bootstrap_gate', 'bootstrap_archive_audit'}"),
    ('from research.unified_consequence_runtime.qualify_native_frontier_v3 import require_environment_gate',
     'from research.unified_consequence_runtime.qualify_native_frontier_v44 import require_environment_gate'),
    ("'UDM_COMMITTED_METADATA_PREQUERY_EXECUTION_V3'", "'UDM_COMMITTED_METADATA_PREQUERY_EXECUTION_V44'"),
    ("'UDM_NATIVE_FRONTIER_METADATA_CURATION_V3'", "'UDM_NATIVE_FRONTIER_METADATA_CURATION_V44'"),
    ("'UDM_ORDERED_NATIVE_ADMISSION_SCREENING_POOL_V3'", "'UDM_ORDERED_NATIVE_ADMISSION_SCREENING_POOL_V44'"),
    ("'environment_gate': verified_gate,", "'environment_gate': gate['environment_gate'],\n        'interface_gate': gate['interface_gate'],\n        'interface_archive_audit': gate['interface_archive_audit'],\n        'bootstrap_gate': gate['bootstrap_gate'],\n        'bootstrap_archive_audit': gate['bootstrap_archive_audit'],\n        'qualified_gate_chain': verified_gate,"),
))


# The original first-query/history guard remains the same executable algorithm;
# only its canonical plan filename changes for this source-versioned revision.
if query.__code__.co_consts.count('PREQUERY.json') != 1:
    raise ValueError('original canonical prequery guard binding site differs')
_original_query_guard = query
query = FunctionType(q._literal_code(query.__code__, {'PREQUERY.json': 'PREQUERY.json'}),
    globals(), query.__name__, query.__defaults__, query.__closure__)
query.__kwdefaults__ = _original_query_guard.__kwdefaults__


def _exposure_record():
    path = RECORDS/'PRIOR_EXPOSURE.json'
    if path.is_symlink() or q.digest(path.read_bytes()) != _EXPOSURE_SHA256:
        raise ValueError('exact prior exposure union required')
    record = json.loads(path.read_text())
    for name, expected in record['input_files_sha256'].items():
        source = q.HERE/name
        if source.is_symlink() or not source.is_file() or q.digest(source.read_bytes()) != expected:
            raise ValueError('prior exposure input differs: '+name)
    return record


def configure_universe(universe_path, gate_path, artifact_path, interface_artifact_path, bootstrap_artifact_path):
    """Validate both archived gates and audit before reading a target name."""
    global UNIVERSE, _qualification_binding
    wrapper = json.loads(Path(gate_path).resolve().read_text())
    q.require_environment_gate(wrapper)
    if set(wrapper) != {'environment_gate', 'catalog', 'interface_gate', 'interface_archive_audit', 'bootstrap_gate', 'bootstrap_archive_audit'}:
        raise ValueError('exact dual-qualified V44 gate wrapper required')
    for path, key in ((artifact_path, 'environment_gate'), (interface_artifact_path, 'interface_gate'), (bootstrap_artifact_path, 'bootstrap_gate')):
        if q.digest(Path(path).resolve().read_bytes()) != wrapper[key]['artifact_sha256']:
            raise ValueError('archived qualification artifact digest differs: '+key)
    exposed = _exposure_record()
    supplied = Path(universe_path).absolute()
    universe_path = supplied.resolve()
    if (universe_path != (RECORDS/'DECLARED_UNIVERSE.json').resolve()
            or supplied != universe_path or supplied.is_symlink()):
        raise ValueError('canonical declared universe record required')
    universe = json.loads(universe_path.read_text())
    keys = {'schema', 'repositories', 'environment_gate', 'interface_gate', 'interface_archive_audit', 'bootstrap_gate', 'bootstrap_archive_audit'}
    if (not isinstance(universe, dict) or set(universe) != keys
            or universe['schema'] != 'UDM_NATIVE_AUTHORITY_V44_DECLARED_UNIVERSE_V1'
            or any(universe[key] != wrapper[key] for key in keys-{'schema', 'repositories'})):
        raise ValueError('new universe must bind exact independently qualified V44 gate chain')
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
                'qualified_gate_wrapper': wrapper, 'prior_exposure_sha256': _EXPOSURE_SHA256}
    if _qualification_binding is not None and (UNIVERSE != tuple(names) or _qualification_binding != proposed):
        raise ValueError('preserve first declared universe; use a new version')
    UNIVERSE, _qualification_binding = tuple(names), proposed
    return proposed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write-prequery', type=Path)
    mode.add_argument('--query-after-committed-prequery', type=Path)
    parser.add_argument('--universe', type=Path, required=True)
    parser.add_argument('--environment-gate', type=Path, required=True)
    parser.add_argument('--qualification-artifact', type=Path, required=True)
    parser.add_argument('--interface-qualification-artifact', type=Path, required=True)
    parser.add_argument('--bootstrap-qualification-artifact', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    configure_universe(args.universe, args.environment_gate, args.qualification_artifact,
                       args.interface_qualification_artifact, args.bootstrap_qualification_artifact)
    if args.write_prequery:
        if args.write_prequery.resolve() != (RECORDS/'PREQUERY.json').resolve():
            raise ValueError('canonical prequery record required')
        write_once(args.write_prequery, plan(q.HERE))
        result = {'path': str(args.write_prequery), 'sha256': q.digest(args.write_prequery.read_bytes()),
                  'state': 'PREQUERY_PREPARED_NO_QUERIES', 'network_queries': 0}
    else:
        if not args.out:
            parser.error('--out required for committed query')
        result = query(q.HERE, args.query_after_committed_prequery.resolve(), args.environment_gate.resolve(),
                       args.qualification_artifact.resolve(), args.out.resolve())
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
