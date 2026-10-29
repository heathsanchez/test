"""Original V45 record assembly with new authority and original query lineage.

The existing curation is read at its original location. No metadata query runs,
and its receipt/pool are not copied into the versioned output directory.
"""
import ast
import importlib.util
import inspect
from pathlib import Path
import textwrap
from types import FunctionType

from research.unified_consequence_runtime import qualify_native_frontier_request_v1 as q

ORIGINAL_HELPER_SOURCE = q.HERE/'archaeology/native-namespace-v45/prospective/prepare_records.py'
ORIGINAL_HELPER_SHA256 = 'df8e7901817d94f5064537cc070c4dd5bb6cdcc74a00cbaed3e89b29f8ac0098'
ORIGINAL_RECORDS = q.HERE/'archaeology/native-namespace-v45/prospective'
if ORIGINAL_HELPER_SOURCE.is_symlink() or q.digest(ORIGINAL_HELPER_SOURCE.read_bytes()) != ORIGINAL_HELPER_SHA256:
    raise ValueError('qualified V45 record-assembly source differs')
_spec = importlib.util.spec_from_file_location('_request_qualified_v45_records', ORIGINAL_HELPER_SOURCE)
QUALIFIED_HELPER = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(QUALIFIED_HELPER)
for _name, _value in vars(QUALIFIED_HELPER).items():
    if not _name.startswith('__') and _name != 'q':
        globals().setdefault(_name, _value)
for _name, _value in tuple(vars(QUALIFIED_HELPER).items()):
    if isinstance(_value, FunctionType) and _value.__globals__ is vars(QUALIFIED_HELPER):
        _bound = FunctionType(_value.__code__, globals(), _name, _value.__defaults__, _value.__closure__)
        _bound.__kwdefaults__ = _value.__kwdefaults__
        globals()[_name] = _bound

# Recover the exact qualified V45 source substitutions as inert AST literals.
# Then change only the old-input/new-output metadata locations.
_tree = ast.parse(ORIGINAL_HELPER_SOURCE.read_text())
_assignments = [node for node in _tree.body if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == 'prepare' for target in node.targets)]
if len(_assignments) != 1:
    raise ValueError('qualified preparation source binding differs')
_substitutions = ast.literal_eval(_assignments[0].value.args[1])
_source = textwrap.dedent(inspect.getsource(QUALIFIED_HELPER._carrier._original.prepare))
_metadata_locations = (
    ("curated = Path(args.curation).resolve()", "curated = Path(args.curation).resolve()\n"
     "    if curated != ORIGINAL_RECORDS or Path(args.curation).absolute() != ORIGINAL_RECORDS:\n"
     "        raise ValueError('exact original V45 curation directory required')"),
    ("execution = copy_exact(curated/'PREQUERY_EXECUTION.json', q.RECORDS/'PREQUERY_EXECUTION.json')",
     "execution = descriptor(curated/'PREQUERY_EXECUTION.json', relative=True)"),
    ("pool = copy_exact(curated/'FROZEN_POOL.json', q.RECORDS/'FROZEN_POOL.json')",
     "pool = descriptor(curated/'FROZEN_POOL.json', relative=True)"),
    ("copy_exact(curated/'METADATA_CURATION.json', q.RECORDS/'METADATA_CURATION.json')",
     "descriptor(curated/'METADATA_CURATION.json', relative=True)"),
    ("json.loads((q.RECORDS/'PREQUERY_EXECUTION.json').read_text()).get(key)",
     "json.loads((curated/'PREQUERY_EXECUTION.json').read_text()).get(key)"),
)
for _before, _after in (*_substitutions, *_metadata_locations):
    if _source.count(_before) != 1:
        raise ValueError('original record-assembly transport binding differs: '+_before)
    _source = _source.replace(_before, _after)
exec(compile(_source, __file__+':qualified-original-prepare', 'exec'), globals())


if __name__ == '__main__':
    main()
