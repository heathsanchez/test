"""Original inventory consumer boundary; no source task or interpreter runs."""
import json

import pytest

from research.unified_consequence_runtime import qualify_native_frontier_v44 as q


def test_incomplete_inventory_retains_original_refusal_before_execution():
    catalog = json.loads((q.HERE.parents[1]/q.CATALOG_PATH).read_text())
    with pytest.raises(ValueError, match='complete runner-local runtime paths required'):
        q.freeze_runtime_inventory({}, catalog)


def test_complete_catalog_reaches_original_interpreter_boundary(monkeypatch):
    catalog = json.loads((q.HERE.parents[1]/q.CATALOG_PATH).read_text())
    paths = {row['id']: '/declared-not-executed/'+row['id'] for row in catalog['profiles']}
    seen = []

    def before_interpreter(path):
        assert path in paths.values()
        seen.append(path)
        raise PermissionError('stopped before interpreter invocation')

    monkeypatch.setattr(q.environment, 'freeze_runtime', before_interpreter)
    with pytest.raises(PermissionError, match='stopped before interpreter invocation'):
        q.freeze_runtime_inventory(paths, catalog)
    assert len(seen) == 1
