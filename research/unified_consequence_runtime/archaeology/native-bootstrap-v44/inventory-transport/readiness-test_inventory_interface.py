"""Read-only setup-interface probe; malformed paths stop before interpreter use."""
import json
from pathlib import Path
import pytest
from research.unified_consequence_runtime import qualify_native_frontier_v44 as q


def test_incomplete_runtime_paths_return_declared_refusal_before_any_interpreter():
    catalog=json.loads((q.HERE.parents[1]/q.CATALOG_PATH).read_text())
    with pytest.raises(ValueError,match='complete runner-local runtime paths required'):
        q.freeze_runtime_inventory({},catalog)
