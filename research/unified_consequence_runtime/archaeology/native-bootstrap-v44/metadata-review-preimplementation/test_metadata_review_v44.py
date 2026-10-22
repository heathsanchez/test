"""Independent-review regressions, infrastructure fixtures only."""
import importlib.util
import json
from pathlib import Path
import pytest
from research.unified_consequence_runtime import native_metadata_v44 as metadata
from research.unified_consequence_runtime import native_environment_selection_v44 as selection
path=Path('/workspace/qualification/native-bootstrap-v44-preimplementation/test_native_metadata_v44_acceptance.py')
spec=importlib.util.spec_from_file_location('frozen_v44_review_fixture',path)
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)

@pytest.mark.parametrize('field',['Requires-Python, Requires-Dist','Requires-Python','Description','Undefined, Field'])
def test_no_dynamic_wheel_header_can_license_final_environment_metadata(tmp_path,field):
    raw=fixture.VALID.replace(b'Metadata-Version: 2.1\n',('Metadata-Version: 2.1\nDynamic: '+field+'\n').encode())
    with pytest.raises(ValueError):
        metadata.parse_wheel_metadata(fixture.wheel(tmp_path,raw))

def test_unexpected_unmarked_dependency_in_static_project_is_conflicting_metadata(tmp_path):
    base=(fixture.FIXTURE/'pyproject.toml').read_bytes()
    base=base.replace(b'dynamic = ["requires-python", "dependencies", "classifiers"]',b'dynamic = ["requires-python", "classifiers"]\ndependencies = []')
    details=json.loads((fixture.FIXTURE/'source-metadata.json').read_text())
    details['requires_dist'].append('undeclared-native-bootstrap-package>=99')
    values=fixture.genuine_observation(tmp_path,modifications={'pyproject.toml':base,'source-metadata.json':json.dumps(details).encode()})
    observation,snapshot=values[-2],values[3]
    result=selection.select_profile(snapshot[1],fixture.catalog(),observation=observation)
    assert result['status']=='UNKNOWN'
    assert result['reason']=='UNKNOWN_CONFLICTING_METADATA'
