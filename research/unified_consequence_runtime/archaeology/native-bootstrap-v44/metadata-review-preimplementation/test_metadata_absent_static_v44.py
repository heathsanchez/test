"""PEP621 omitted, non-dynamic runtime dependencies stay an empty contract."""
import importlib.util,json
from pathlib import Path
import pytest
from research.unified_consequence_runtime import native_environment_selection_v44 as selection
p=Path('/workspace/qualification/native-bootstrap-v44-preimplementation/test_native_metadata_v44_acceptance.py')
spec=importlib.util.spec_from_file_location('frozen_v44_absent_fixture',p)
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)

@pytest.mark.parametrize('extra_runtime',[False,True])
def test_absent_static_dependencies_are_empty_and_keep_lawful_test_extras(tmp_path,extra_runtime):
    base=(fixture.FIXTURE/'pyproject.toml').read_bytes().replace(b'dynamic = ["requires-python", "dependencies", "classifiers"]',b'dynamic = ["requires-python", "classifiers"]')
    details=json.loads((fixture.FIXTURE/'source-metadata.json').read_text())
    if extra_runtime:details['requires_dist'].append('undeclared-native-bootstrap-package>=99')
    values=fixture.genuine_observation(tmp_path,modifications={'pyproject.toml':base,'source-metadata.json':json.dumps(details).encode()})
    result=selection.select_profile(values[3][1],fixture.catalog(),observation=values[-2])
    assert result['status']==('UNKNOWN' if extra_runtime else 'CANDIDATE_SOURCE_ENVIRONMENT')
    if extra_runtime:assert result['reason']=='UNKNOWN_CONFLICTING_METADATA'
