"""Retained-byte interval controls, no Git or target process runs."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import pytest

HERE=Path(__file__).resolve().parent


def module():
    p=HERE/'audit_retained_v45.py';s=importlib.util.spec_from_file_location('v45_source_index_audit',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


@pytest.mark.parametrize('change',('none','status','source-after','raw-before','raw-after','missing-raw','current-index','restoration'))
def test_source_and_index_interval_authenticates_all_retained_raw_bytes(tmp_path,change):
    m=module();raw=b'original pre-audit index bytes';digest=hashlib.sha256(raw).hexdigest()
    def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v))
    source={'source_commit':'a'*40,'files':[{'path':'original.py','mode':'100644','sha256':'b'*64}]}
    before=tmp_path/'SCREENING_SOURCE_BEFORE.json';write(before,source);write(tmp_path/'SCREENING_SOURCE_AFTER.json',source)
    controller={'source_snapshot':{'path':str(before),'sha256':m.sha(before.read_bytes())}}
    snap={'schema':'UDM_GIT_INDEX_SNAPSHOT_V4','git_common_dir':str(tmp_path/'git'),
      'indexes':[{'path':str(tmp_path/'git/index'),'exists':True,'size_bytes':len(raw),'sha256':digest}]}
    for phase in ('before','after'):
        folder=tmp_path/('source-index-'+phase+'-screening');write(folder/'SNAPSHOT.json',snap)
        (folder/'index-0.bytes').write_bytes(raw)
    report={'status':'PASS_SOURCE_AND_INDEX_BYTES','source_unchanged':True,'index_changes':[],
      'restored_any_index':False,'before_indexes':copy.deepcopy(snap),'after_indexes':copy.deepcopy(snap)}
    current=copy.deepcopy(snap)
    if change=='status':report['status']='UNKNOWN_SOURCE_OR_INDEX_CHANGED'
    elif change=='source-after':write(tmp_path/'SCREENING_SOURCE_AFTER.json',{})
    elif change=='raw-before':(tmp_path/'source-index-before-screening/index-0.bytes').write_bytes(b'changed')
    elif change=='raw-after':(tmp_path/'source-index-after-screening/index-0.bytes').write_bytes(b'changed')
    elif change=='missing-raw':(tmp_path/'source-index-after-screening/index-0.bytes').unlink()
    elif change=='current-index':current['indexes'][0]['sha256']='c'*64
    elif change=='restoration':report['restored_any_index']=True
    write(tmp_path/'SOURCE_INDEX_SCREENING_AUDIT.json',report)
    if change=='none':
        checked=m.audit_source_index_interval(m.old.Audit(),tmp_path,controller,current=current)
        assert checked['status']=='PASS_AUTHENTICATED_ORIGINAL_SOURCE_INDEX_INTERVAL'
    else:
        with pytest.raises(ValueError):m.audit_source_index_interval(m.old.Audit(),tmp_path,controller,current=current)
