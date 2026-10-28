"""V45 local record assembly with all four independently archived gates.

Import performs no curation, source fetch, task selection or native execution.
The independent archive and screening audits must be supplied by their owners.
"""
import importlib.util
from pathlib import Path
from types import FunctionType

from research.unified_consequence_runtime import qualify_native_frontier_v45 as q

_path = q.HERE/'archaeology/native-bootstrap-v44/prospective/prepare_records.py'
_pin = 'd8cc3e99f5404e467bc6cd958ded6019082b7c266279765c1680a485fd4c2576'
if _path.is_symlink() or q.digest(_path.read_bytes()) != _pin:
    raise ValueError('original record-assembly carrier differs')
_spec = importlib.util.spec_from_file_location('_udm_v45_original_records', _path)
_carrier = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_carrier)
for _name, _value in vars(_carrier).items():
    if not _name.startswith('__'):
        globals().setdefault(_name, _value)
for _name, _value in tuple(vars(_carrier).items()):
    if (isinstance(_value, FunctionType) and _value.__module__ == _carrier.__name__
            and _name not in ('prepare', 'finalize')):
        _bound = FunctionType(_value.__code__, globals(), _name, _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        globals()[_name] = _bound


prepare = _bind(_carrier._original.prepare, (
    ("value.update(environment_gate=wrapper['environment_gate'], catalog=wrapper['catalog'],",
     "value.update(environment_gate=wrapper['environment_gate'], catalog=wrapper['catalog'],\n"
     "                 interface_gate=wrapper['interface_gate'], interface_archive_audit=wrapper['interface_archive_audit'],\n"
     "                 bootstrap_gate=wrapper['bootstrap_gate'], bootstrap_archive_audit=wrapper['bootstrap_archive_audit'],\n"
     "                 namespace_gate=wrapper['namespace_gate'], namespace_archive_audit=wrapper['namespace_archive_audit'],"),
    ("if json.loads((q.RECORDS/'PREQUERY_EXECUTION.json').read_text())['environment_gate'] != wrapper['environment_gate']:",
     "if any(json.loads((q.RECORDS/'PREQUERY_EXECUTION.json').read_text()).get(key) != wrapper[key] for key in q.GATE_KEYS):"),
    ("'schema': 'UDM_NATIVE_CLI_AUTHORITY_V3'", "'schema': 'UDM_NATIVE_CLI_AUTHORITY_V45'"),
    ("'repo': str(q.HERE.parents[1]), 'environment_gate': wrapper['environment_gate'],",
     "'repo': str(q.HERE.parents[1]), 'environment_gate': wrapper['environment_gate'],\n"
     "              'interface_gate': wrapper['interface_gate'], 'interface_archive_audit': wrapper['interface_archive_audit'],\n"
     "              'bootstrap_gate': wrapper['bootstrap_gate'], 'bootstrap_archive_audit': wrapper['bootstrap_archive_audit'],\n"
     "              'namespace_gate': wrapper['namespace_gate'], 'namespace_archive_audit': wrapper['namespace_archive_audit'],\n"
     "              'machine_components': q._components_record(Path(args.components).resolve()),"),
))
finalize = _bind(_carrier._original.finalize, (
    ("ticket, _, _ = q.cli_authority(authority['path'], authority['sha256'], 'screen')",
     "ticket, bound, _ = q.cli_authority(authority['path'], authority['sha256'], 'screen')\n"
     "    q._screening_components(ticket, bound)\n"
     "    if any(ticket.get(key) != value.get(key) for key in q.GATE_KEYS):\n"
     "        raise ValueError('screening ticket differs from independently audited V45 gate chain')"),
    ("'schema': 'UDM_ADMISSION_ONLY_SCREENING_V3'", "'schema': 'UDM_ADMISSION_ONLY_SCREENING_V45'"),
    ("'environment_gate': value['environment_gate'], 'independent_screener': True,",
     "'environment_gate': value['environment_gate'], 'independent_screener': True,\n"
     "        'interface_gate': value['interface_gate'], 'interface_archive_audit': value['interface_archive_audit'],\n"
     "        'bootstrap_gate': value['bootstrap_gate'], 'bootstrap_archive_audit': value['bootstrap_archive_audit'],\n"
     "        'namespace_gate': value['namespace_gate'], 'namespace_archive_audit': value['namespace_archive_audit'],"),
    ("'costs': {'native_calls': meter['native_calls']", "'build_costs': _aggregate_build_costs(reports),\n        'bootstrap_costs': _aggregate_bootstrap_costs(reports),\n        'costs': {'native_calls': meter['native_calls']"),
    ("'schema': 'UDM_PROSPECTIVE_NATIVE_FRONTIER_TASK_METADATA_V3'", "'schema': 'UDM_PROSPECTIVE_NATIVE_FRONTIER_TASK_METADATA_V45'"),
))


if __name__ == '__main__':
    main()
