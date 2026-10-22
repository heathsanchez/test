"""Frozen source-free upload path-authority controls; no target execution."""
import importlib.util
from pathlib import Path
import pytest

def module():
    path=Path(__file__).with_name('audit_actual_archive.py');spec=importlib.util.spec_from_file_location('archive_data_audit',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

def test_exact_uploaded_scope_disambiguates_committed_nested_readme_from_root_basename():
    m=module();raw=b'actual committed nested report README';name='test/test/'+m.ROOT+'archive-verification/README.md'
    source={'README.md':{'kind':'file','sha256':m.sha(b'unrelated root readme')},m.ROOT+'archive-verification/README.md':{'kind':'file','sha256':m.sha(raw)}}
    assert m.uploaded_binding(name,raw,source,{})==[('source',m.ROOT+'archive-verification/README.md')]

@pytest.mark.parametrize('change',('undeclared_scope','changed_bytes','ambiguous_evidence'))
def test_upload_scope_unknown_changed_or_ambiguous_paths_refuse(change):
    m=module();raw=b'original archived file';key=m.ROOT+'README.md';name='test/test/'+key
    source={key:{'kind':'file','sha256':m.sha(raw)}};evidence={}
    if change=='undeclared_scope':source={'README.md':{'kind':'file','sha256':m.sha(raw)}};name='test/test/README.md'
    elif change=='changed_bytes':raw=b'changed uploaded payload'
    elif change=='ambiguous_evidence':
        source={};name='outer/report.json';evidence={'report.json':{'kind':'file','sha256':m.sha(raw)},'outer/report.json':{'kind':'file','sha256':m.sha(b'another payload')}}
    with pytest.raises(ValueError):m.uploaded_binding(name,raw,source,evidence)
