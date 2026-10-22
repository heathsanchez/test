"""V44 record assembly; no query or source/native execution.

The independently archived old gates and new bootstrap gate are mandatory.
"""
import importlib.util
import inspect
from pathlib import Path
import textwrap
from types import FunctionType

from research.unified_consequence_runtime import qualify_native_frontier_v44 as q

SOURCE_PINS = {
    'archaeology/native-authority-v42/prepare_records.py':
        '00fbd357882c3aea5a319601b3302c6208a0eef7bd0b0a560d60cee1c0533458',
    'archaeology/native-environment-v3/prepare_records.py':
        '7ab47d2339641a09d5ab2c6e417ed148298477e83bf19f8580b56a9655c6ce5a',
    'qualify_native_frontier_v44.py':
        '5006932fedc8b321d6f36002d1c3086790dd49ad18ca8327feb6148bb0948f02',
}
for _relative, _expected in SOURCE_PINS.items():
    _source = q.HERE/_relative
    if _source.is_symlink() or q.digest(_source.read_bytes()) != _expected:
        raise ValueError('V44 local record assembly source differs: '+_relative)


def _load(relative, name):
    spec = importlib.util.spec_from_file_location(name, q.HERE/relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_carrier = _load('archaeology/native-authority-v42/prepare_records.py', '_udm_v44_pinned_v42_records')
_original = _load('archaeology/native-environment-v3/prepare_records.py', '_udm_v44_original_records')
for _name, _value in vars(_carrier).items():
    if not _name.startswith('__'):
        globals().setdefault(_name, _value)
for _name, _value in tuple(vars(_carrier).items()):
    if isinstance(_value, FunctionType) and _value.__module__ == _carrier.__name__:
        _bound = FunctionType(_value.__code__, globals(), _name, _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        globals()[_name] = _bound


def _bind(function, substitutions):
    source = textwrap.dedent(inspect.getsource(function))
    for old, new in substitutions:
        if source.count(old) != 1:
            raise ValueError('V44 record assembly binding site differs: '+function.__name__+':'+old)
        source = source.replace(old, new)
    namespace = dict(globals())
    exec(compile(source, __file__+':bound-'+function.__name__, 'exec'), namespace)
    changed = namespace[function.__name__]
    bound = FunctionType(changed.__code__, globals(), changed.__name__, changed.__defaults__, changed.__closure__)
    bound.__kwdefaults__ = changed.__kwdefaults__
    return bound


def _aggregate_build_costs(reports):
    for row in reports:
        q._validate_screening_build_costs(row['build_costs'])
    return {
        'build_calls': sum(row['build_costs']['build_calls'] for row in reports),
        'build_seconds': sum(row['build_costs']['build_seconds'] for row in reports),
        'verification_attempts': sum(row['build_costs']['verification_attempts'] for row in reports),
        'sum_case_inclusive_parent_wall_seconds': sum(
            row['build_costs']['inclusive_parent_wall_seconds'] for row in reports),
        'all_pool_members_retained': len(reports),
        'coverage': q._BUILD_COST_COVERAGE,
        'aggregation': 'Sum of exact sealed envelope build deltas; build seconds are included in parent wall time. '
                       'Original native costs and native-call ceilings remain separate and unchanged.',
    }


def _aggregate_bootstrap_costs(reports):
    for row in reports:
        q._validate_screening_bootstrap_costs(row['bootstrap_costs'])
    return {
        'backend_calls': sum(row['bootstrap_costs']['backend_calls'] for row in reports),
        'backend_seconds': sum(row['bootstrap_costs']['backend_seconds'] for row in reports),
        'sum_case_inclusive_parent_wall_seconds': sum(row['bootstrap_costs']['inclusive_parent_wall_seconds'] for row in reports),
        'all_pool_members_retained': len(reports),
        'coverage': q._BOOTSTRAP_COST_COVERAGE,
        'aggregation': 'Exact sealed metadata-backend deltas; nested build/native/parent wall intervals are not additive.',
    }


prepare = _bind(_original.prepare, (
    ("value.update(environment_gate=wrapper['environment_gate'], catalog=wrapper['catalog'],",
     "value.update(environment_gate=wrapper['environment_gate'], catalog=wrapper['catalog'],\n"
     "                 interface_gate=wrapper['interface_gate'], interface_archive_audit=wrapper['interface_archive_audit'],\n"
     "                 bootstrap_gate=wrapper['bootstrap_gate'], bootstrap_archive_audit=wrapper['bootstrap_archive_audit'],"),
    ("if json.loads((q.RECORDS/'PREQUERY_EXECUTION.json').read_text())['environment_gate'] != wrapper['environment_gate']:",
     "if any(json.loads((q.RECORDS/'PREQUERY_EXECUTION.json').read_text()).get(key) != wrapper[key]\n"
     "           for key in ('environment_gate', 'interface_gate', 'interface_archive_audit', 'bootstrap_gate', 'bootstrap_archive_audit')):"),
    ("'schema': 'UDM_NATIVE_CLI_AUTHORITY_V3'", "'schema': 'UDM_NATIVE_CLI_AUTHORITY_V44'"),
    ("'repo': str(q.HERE.parents[1]), 'environment_gate': wrapper['environment_gate'],",
     "'repo': str(q.HERE.parents[1]), 'environment_gate': wrapper['environment_gate'],\n"
     "              'interface_gate': wrapper['interface_gate'], 'interface_archive_audit': wrapper['interface_archive_audit'],\n"
     "              'bootstrap_gate': wrapper['bootstrap_gate'], 'bootstrap_archive_audit': wrapper['bootstrap_archive_audit'],\n"
     "              'machine_components': q._components_record(Path(args.components).resolve()),"),
))
finalize = _bind(_original.finalize, (
    ("ticket, _, _ = q.cli_authority(authority['path'], authority['sha256'], 'screen')",
     "ticket, bound, _ = q.cli_authority(authority['path'], authority['sha256'], 'screen')\n"
     "    q._screening_components(ticket, bound)\n"
     "    if any(ticket.get(key) != value.get(key) for key in ('interface_gate', 'interface_archive_audit', 'bootstrap_gate', 'bootstrap_archive_audit')):\n"
     "        raise ValueError('screening ticket differs from independently audited V44 interface')"),
    ("'schema': 'UDM_ADMISSION_ONLY_SCREENING_V3'", "'schema': 'UDM_ADMISSION_ONLY_SCREENING_V44'"),
    ("'environment_gate': value['environment_gate'], 'independent_screener': True,",
     "'environment_gate': value['environment_gate'], 'independent_screener': True,\n"
     "        'interface_gate': value['interface_gate'], 'interface_archive_audit': value['interface_archive_audit'],\n"
     "        'bootstrap_gate': value['bootstrap_gate'], 'bootstrap_archive_audit': value['bootstrap_archive_audit'],"),
    ("'costs': {'native_calls': meter['native_calls']", "'build_costs': _aggregate_build_costs(reports),\n        'bootstrap_costs': _aggregate_bootstrap_costs(reports),\n        'costs': {'native_calls': meter['native_calls']"),
    ("'schema': 'UDM_PROSPECTIVE_NATIVE_FRONTIER_TASK_METADATA_V3'", "'schema': 'UDM_PROSPECTIVE_NATIVE_FRONTIER_TASK_METADATA_V44'"),
))
# Only the CLI parser's required component argument is added. The execution
# dispatcher, modes and all existing required arguments retain original source.
main = _bind(_original.main, (
    ("prepare_parser.add_argument('--screen-root', required=True)",
     "prepare_parser.add_argument('--screen-root', required=True)\n"
     "    prepare_parser.add_argument('--components', required=True)"),
))


if __name__ == '__main__':
    main()
