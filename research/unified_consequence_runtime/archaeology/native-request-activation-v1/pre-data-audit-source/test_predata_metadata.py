"""Pure metadata identity controls; no task source, native or network calls."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

HERE=Path(__file__).resolve().parent


def module():
    path=HERE/'predata_metadata.py'
    assert path.is_file(), 'versioned pre-data metadata auditor missing'
    spec=importlib.util.spec_from_file_location('request_v1_predata',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def exposure():
    return {'schema':'UDM_NATIVE_NAMESPACE_V45_PRIOR_EXPOSURE_V1',
            'repositories':['old/exposed'],'repository_count':1,
            'input_files_sha256':{'old/input.json':'a'*64},'boundary':'bounded original evidence'}


def test_reconstructed_exposure_matches_canonical_value_not_nonexistent_old_file():
    m=module();value=exposure()
    plan={'qualification_and_universe':{'prior_exposure_sha256':m.fp(value)}}
    pretty=(json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
    assert hashlib.sha256(pretty).hexdigest()!=m.fp(value)
    checked=m.validate_exposure_fingerprint(plan,value)
    assert checked['semantic_fingerprint']==m.fp(value)
    assert checked['record_existed_at_original_freeze'] is False


@pytest.mark.parametrize('change',('pretty-file-hash','changed-value','duplicate-repository','wrong-count'))
def test_changed_or_wrongly_hashed_original_exposure_is_refused(change):
    m=module();value=exposure()
    plan={'qualification_and_universe':{'prior_exposure_sha256':m.fp(value)}}
    if change=='pretty-file-hash':plan['qualification_and_universe']['prior_exposure_sha256']=hashlib.sha256((json.dumps(value,indent=2)+'\n').encode()).hexdigest()
    elif change=='changed-value':value['boundary']='changed historical boundary'
    elif change=='duplicate-repository':value['repositories'].append('old/exposed')
    else:value['repository_count']=2
    with pytest.raises(ValueError):m.validate_exposure_fingerprint(plan,value)


@pytest.mark.parametrize('spent,expected',[(25.756850843,7174.243149157),(7200.0,0.0)])
def test_original_screening_time_is_not_renewed(spent,expected):
    m=module();assert m.remaining_screening_seconds(7200,spent)==pytest.approx(expected)


@pytest.mark.parametrize('spent',[-1,float('nan'),float('inf'),True,7200.1])
def test_invalid_or_exhausted_carryover_refuses(spent):
    m=module()
    with pytest.raises(ValueError):m.remaining_screening_seconds(7200,spent)
