"""Gate-bound v4 wrapper for the unchanged metadata-only frontier curator.

No new repository universe is embedded. A later operator supplies its declared
universe only after the final v4 qualification artifact is independently ready.
Importing this file performs no metadata request or source/native operation.
"""
import importlib.util
from pathlib import Path
from types import FunctionType, SimpleNamespace

from research.unified_consequence_runtime import qualify_native_frontier_v4 as q

_path = q.HERE/'archaeology/native-environment-v3/curate_frontier.py'
_expected = '44455d61c8144261e2db2ce2a6de8b6b2671d9ca504353e03bb9dcd487fa3c14'
if q.digest(_path.read_bytes()) != _expected:
    raise ValueError('original metadata-only curator source differs')
_spec = importlib.util.spec_from_file_location('_udm_v4_original_frontier_curator', _path)
_original = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_original)

for _name, _value in vars(_original).items():
    if not _name.startswith('__'):
        globals().setdefault(_name, _value)

UNIVERSE = ()
RECORDS = q.RECORDS
SCHEMA = 'UDM_NATIVE_AUTHORITY_V4_METADATA_PREQUERY_V1'
EXTRA_HISTORY = (*_original.EXTRA_HISTORY, *(('archaeology/native-environment-v3/'+name)
    for name in ('PREQUERY.json', 'PREQUERY_EXECUTION.json', 'METADATA_CURATION.json',
                 'FROZEN_POOL.json', 'SCREENING_ENVELOPES.json', 'SCREENING_AUTHORITY.json',
                 'SCREENING_METER.json', 'SCREENING_SHORTFALL.json')))
_LOADED_SHA256 = q.digest(Path(__file__).read_bytes())
_qualification_binding = None

for _name, _value in vars(_original).items():
    if isinstance(_value, FunctionType) and _value.__module__ == _original.__name__:
        _code = _value.__code__
        if _name == 'query':
            _old_import = 'research.unified_consequence_runtime.qualify_native_frontier_v3'
            if _code.co_names.count(_old_import) != 1:
                raise ValueError('original metadata gate import binding site differs')
            _code = _code.replace(co_names=tuple(q.MODULE if name == _old_import else name
                                                 for name in _code.co_names))
            _code = q._literal_code(_code, {
                'UDM_COMMITTED_METADATA_PREQUERY_EXECUTION_V3': 'UDM_COMMITTED_METADATA_PREQUERY_EXECUTION_V4',
                'UDM_NATIVE_FRONTIER_METADATA_CURATION_V3': 'UDM_NATIVE_FRONTIER_METADATA_CURATION_V4',
                'UDM_ORDERED_NATIVE_ADMISSION_SCREENING_POOL_V3': 'UDM_ORDERED_NATIVE_ADMISSION_SCREENING_POOL_V4'})
        _bound = FunctionType(_code, globals(), _name, _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        globals()[_name] = _bound

_base_plan = plan
_base_query = query
_base_exclusions = exclusions
_OLD_REPOSITORIES = 'archaeology/programme-closure/REPOSITORIES.json'
_VERSIONED_REPOSITORIES = 'archaeology/native-authority-v4/HISTORICAL_REPOSITORIES.json'
_HISTORICAL_REPOSITORIES_SHA256 = '0d48c74467e8c493c1579104588d3745a4126cc4eff36464b84ce15a29bb3fb6'


def exclusions(research, old):
    """Retain one historical input from exact tracked bytes absent in old CI."""
    frozen = json.loads((research/'archaeology/native-environment-v3/PREQUERY.json').read_text())
    authority = [row for row in frozen['historical_metadata_inputs'] if row['path'] == _OLD_REPOSITORIES]
    if len(authority) != 1 or authority[0].get('sha256') != _HISTORICAL_REPOSITORIES_SHA256:
        raise ValueError('frozen historical repositories authority hash differs')
    target = research/_VERSIONED_REPOSITORIES
    if (target.is_symlink() or not target.is_file()
            or sha256(target.read_bytes()) != authority[0]['sha256']):
        raise ValueError('versioned historical repositories authority bytes differ')
    if old.HISTORICAL_METADATA.count(_OLD_REPOSITORIES) != 1:
        raise ValueError('original historical repositories authority binding site differs')
    paths = tuple(_VERSIONED_REPOSITORIES if name == _OLD_REPOSITORIES else name
                  for name in old.HISTORICAL_METADATA)
    private = SimpleNamespace(**dict(vars(old), HISTORICAL_METADATA=paths))
    return _base_exclusions(research, private)


def configure_universe(universe_path, gate_path, artifact_path):
    """Validate qualified authority before reading a later declared universe."""
    global UNIVERSE, _qualification_binding
    gate_path, artifact_path = Path(gate_path).resolve(), Path(artifact_path).resolve()
    wrapper = json.loads(gate_path.read_text())
    q.require_environment_gate(wrapper)
    if set(wrapper) != {'environment_gate', 'catalog'}:
        raise ValueError('qualified gate wrapper must have exactly environment_gate and catalog')
    if sha256(artifact_path.read_bytes()) != wrapper['environment_gate']['artifact_sha256']:
        raise ValueError('qualified v4 artifact bytes differ')
    supplied = Path(universe_path).absolute()
    universe_path = supplied.resolve()
    if (universe_path != (RECORDS/'DECLARED_UNIVERSE.json').resolve()
            or supplied != universe_path or supplied.is_symlink()):
        raise ValueError('canonical declared universe record required')
    universe = json.loads(universe_path.read_text())
    if (not isinstance(universe, dict) or set(universe) != {'schema', 'repositories', 'environment_gate'}
            or universe['schema'] != 'UDM_NATIVE_AUTHORITY_V4_DECLARED_UNIVERSE_V1'
            or universe['environment_gate'] != wrapper['environment_gate']):
        raise ValueError('new universe must bind exact independently qualified v4 gate')
    names = universe['repositories']
    if (not isinstance(names, list) or not 1 <= len(names) <= SCREENING_BUDGET['maximum_cases']
            or any(not isinstance(name, str) or not re.fullmatch(r'[a-z0-9_.-]+/[a-z0-9_.-]+', name)
                   for name in names)
            or names != sorted(set(names))):
        raise ValueError('new universe must contain at most nine sorted unique lowercase repositories')
    touched, _ = exclusions(q.HERE, original(q.HERE))
    if any(name in touched for name in names):
        raise ValueError('declared universe contains a historically exposed repository')
    root = q.HERE.parents[1]
    if not universe_path.is_relative_to(root) or universe_path.is_symlink():
        raise ValueError('declared universe must be an ordinary repository record')
    proposed = {'universe': {'path': universe_path.relative_to(root).as_posix(),
                            'sha256': sha256(universe_path.read_bytes())},
                'environment_gate': wrapper['environment_gate']}
    if _qualification_binding is not None and (UNIVERSE != tuple(names) or _qualification_binding != proposed):
        raise ValueError('preserve the first declared universe; new source version required')
    UNIVERSE, _qualification_binding = tuple(names), proposed
    return proposed


def plan(research):
    if not UNIVERSE or _qualification_binding is None:
        raise ValueError('qualified v4 gate and later declared universe required before prequery')
    return dict(_base_plan(research), qualification_and_universe=_qualification_binding)


def query(research, plan_path, gate_path, artifact_path, out):
    """One canonical query receipt survives process restarts and later commits."""
    records = RECORDS.resolve()
    if (Path(plan_path).resolve() != records/'PREQUERY.json'
            or Path(out).resolve() != records):
        raise ValueError('canonical prequery and query output records required')
    receipt = records/'PREQUERY_EXECUTION.json'
    if receipt.exists():
        raise ValueError('prior query receipt retained; preserve the first frontier')
    root = Path(research).resolve().parents[1]
    history = subprocess.check_output(['git', '-C', str(root), 'log', '--format=%H', '-n', '1',
                                       'HEAD', '--', receipt.relative_to(root).as_posix()])
    if history.strip():
        raise ValueError('prior query receipt exists in committed history; no replacement frontier')
    return _base_query(research, plan_path, gate_path, artifact_path, out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write-prequery', type=Path)
    mode.add_argument('--query-after-committed-prequery', type=Path)
    parser.add_argument('--universe', type=Path, required=True)
    parser.add_argument('--environment-gate', type=Path, required=True)
    parser.add_argument('--qualification-artifact', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    configure_universe(args.universe, args.environment_gate, args.qualification_artifact)
    if args.write_prequery:
        if args.write_prequery.resolve() != (RECORDS/'PREQUERY.json').resolve():
            raise ValueError('canonical prequery record required')
        write_once(args.write_prequery, plan(q.HERE))
        result = {'path': str(args.write_prequery), 'sha256': sha256(args.write_prequery.read_bytes()),
                  'state': 'PREQUERY_PREPARED_NO_QUERIES', 'network_queries': 0}
    else:
        if not args.out:
            parser.error('--out is required for the committed query')
        result = query(q.HERE, args.query_after_committed_prequery.resolve(),
                       args.environment_gate.resolve(), args.qualification_artifact.resolve(), args.out.resolve())
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
