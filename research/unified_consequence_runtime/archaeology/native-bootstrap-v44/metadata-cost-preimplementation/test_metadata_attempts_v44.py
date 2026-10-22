"""Original native-backend build accounting, not developmental qualification."""
import importlib.util
from pathlib import Path
import sys
import pytest
from research.unified_consequence_runtime import native_metadata_v44 as metadata
path=Path('/workspace/qualification/native-bootstrap-v44-preimplementation/test_native_metadata_v44_acceptance.py')
spec=importlib.util.spec_from_file_location('frozen_v44_accounting_fixture',path)
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)

def test_no_command_before_environment_refusal(tmp_path):
    before=metadata.attempt_snapshot()
    repo,commit,_=fixture.make_repo(tmp_path)
    with pytest.raises(ValueError):
        metadata.observe(repo,commit,sys.executable,tmp_path/'bad-env',environment_sha256='0'*64,timeout=60)
    after=metadata.attempt_snapshot()
    assert after['build_calls']==before['build_calls']
    assert after['records']==before['records']

def test_failed_original_backend_command_is_retained_and_charged(tmp_path):
    before=metadata.attempt_snapshot()
    repo,commit,_=fixture.make_repo(tmp_path,modifications={'source-metadata.json':b'invalid JSON original fixture'})
    with pytest.raises(RuntimeError):
        metadata.observe(repo,commit,sys.executable,tmp_path/'failed',environment_sha256=fixture.environment_sha(),timeout=60)
    after=metadata.attempt_snapshot()
    assert after['build_calls']-before['build_calls']==1
    assert len(after['records'])-len(before['records'])==1
    row=after['records'][-1]
    assert row['phase']=='observe'
    assert row['build_calls']==1 and row['build_seconds']>=0
    assert row['status']=='UNKNOWN_BUILD_EXECUTION'
    assert Path(row['output'],'build-attempt.json').is_file()

def test_original_acquisition_and_independent_rebuild_count_separately(tmp_path):
    before=metadata.attempt_snapshot()
    fixture.genuine_observation(tmp_path)
    after=metadata.attempt_snapshot()
    assert after['build_calls']-before['build_calls']==2
    rows=after['records'][len(before['records']):]
    assert [r['phase'] for r in rows]==['observe','verify']
    assert all(r['build_calls']==1 and r['status']=='BUILD_COMMAND_PASS' for r in rows)
    assert after['build_seconds']-before['build_seconds']==pytest.approx(sum(r['build_seconds'] for r in rows))
