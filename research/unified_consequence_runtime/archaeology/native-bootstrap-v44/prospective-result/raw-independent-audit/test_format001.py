"""Source-free controls for exact original-record to summary projection."""
import importlib.util
from pathlib import Path
import pytest

def module():
    path=Path(__file__).with_name('verify_raw_packet.py')
    spec=importlib.util.spec_from_file_location('raw_packet_auditor',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

def fixture():
    return [{'repo':'fixture/unread','status':'NO_QUALIFYING_CANDIDATE','closed_pr_count':2,
             'closed_pr_window':{'page':1},'qualifying_prs':[],
             'query_coverage':[{'endpoint':'one'},{'endpoint':'two'}],
             'candidates':[{'retained':'full raw records checked independently'}]}]

def test_exact_summary_projection_never_demands_raw_only_fields():
    m=module()
    assert m.coverage_projection(fixture())==[{'repo':'fixture/unread','status':'NO_QUALIFYING_CANDIDATE',
        'closed_pr_count':2,'closed_pr_window':{'page':1},'qualifying_prs':[],'query_endpoints':2}]

@pytest.mark.parametrize('field,value',[('repo','other/unread'),('status','QUALIFYING_METADATA_CANDIDATE'),
    ('closed_pr_count',3),('closed_pr_window',{'page':2}),('qualifying_prs',[1]),
    ('query_coverage',[{'endpoint':'one'}])])
def test_all_declared_summary_fields_remain_exact(field,value):
    m=module();rows=fixture();expected=m.coverage_projection(rows);rows[0][field]=value
    assert m.coverage_projection(rows)!=expected

@pytest.mark.parametrize('change',('raw_digest','component_commit','component_pin'))
def test_component_boundary_preserves_exact_raw_pinset_and_projection(change):
    import json
    m=module();config={key:{'commit':'original','files':{'one.py':'exact'}} for key in ('development','metatron','flash')}
    config['schema']='retained original full file'
    raw=json.dumps(config,indent=2).encode()
    boundary={'source_pins_sha256':m.sha(raw),'source_pins':{key:config[key] for key in ('development','metatron','flash')}}
    assert m.component_pinset_matches(boundary,raw)
    if change=='raw_digest':raw+=b'\n'
    elif change=='component_commit':boundary['source_pins']['development']['commit']='forged'
    else:boundary['source_pins']['flash']['files']['one.py']='forged'
    assert not m.component_pinset_matches(boundary,raw)
