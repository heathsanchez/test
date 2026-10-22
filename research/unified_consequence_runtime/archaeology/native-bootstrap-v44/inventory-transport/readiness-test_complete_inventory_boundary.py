"""Actual inherited inventory boundary; no target or interpreter is invoked."""
import json
from pathlib import Path
import pytest
from research.unified_consequence_runtime import qualify_native_frontier_v44 as q


def test_complete_original_profile_paths_reach_interpreter_boundary(monkeypatch):
    catalog=json.loads((q.HERE.parents[1]/q.CATALOG_PATH).read_text())
    paths=json.loads(Path('/workspace/qualification/native-authority-v41-profile-preparation/RUNTIMES.json').read_text())
    seen=[]
    def before_interpreter(path):
        assert path in paths.values()
        seen.append(path)
        raise PermissionError('stopped before any interpreter invocation')
    monkeypatch.setattr(q.environment,'freeze_runtime',before_interpreter)
    with pytest.raises(PermissionError,match='stopped before any interpreter invocation'):
        q.freeze_runtime_inventory(paths,catalog)
    assert len(seen)==1
