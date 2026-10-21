"""Source-free transport controls; no Git, API, source or native operations."""
import importlib.util
import json
import os
from pathlib import Path
from types import FunctionType, SimpleNamespace

import pytest


def load():
    path=Path(os.environ.get('UDM_METADATA_CURATOR',
        '/workspace/udm-v54/research/unified_consequence_runtime/archaeology/experiment-interface-v43/prospective/curate_frontier_v2.py'))
    spec=importlib.util.spec_from_file_location('_metadata_transport_control',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def declared_operation(value):
    return ('original',value)


def test_binding_an_aliased_function_executes_the_new_definition():
    module=load()
    alias=FunctionType(declared_operation.__code__,globals(),'renamed_operation')
    # The transport namespace already contains the old callable, exactly as the
    # inherited _base_query alias does. Running the new callable is the control.
    module.renamed_operation=alias
    changed=module._source_binding(alias,(("'original'","'versioned'"),))
    assert changed(7)==('versioned',7)
    assert alias(7)==('original',7)


class PreApiBoundary(Exception):
    pass


def fixture_context(module,tmp_path,monkeypatch):
    research=tmp_path/'repo/research/unified_consequence_runtime'
    records=research/'new-records';records.mkdir(parents=True)
    prepared={'diagnostic_transport_only':True}
    plan_path=records/'PREQUERY_V2.json';plan_path.write_text(json.dumps(prepared))
    wrapper={'environment_gate':{'artifact_sha256':module.sha256(b'fixed-archive')},
             'catalog':{},'interface_gate':{},'interface_archive_audit':{}}
    gate_path=records/'GATE_WRAPPER.json';gate_path.write_text(json.dumps(wrapper))
    archive=tmp_path/'qualified.zip';archive.write_bytes(b'fixed-archive')
    monkeypatch.setattr(module,'RECORDS',records)
    monkeypatch.setattr(module,'plan',lambda actual:prepared)
    monkeypatch.setattr(module,'committed',lambda root,path:{'path':str(path),
        'source_commit':'a'*40,'sha256':module._LOADED_SHA256})
    # Only source-control transport is doubled. No native/metadata oracle exists.
    monkeypatch.setattr(module,'subprocess',SimpleNamespace(check_output=lambda *args,**kwargs:b''))
    return research,records,plan_path,gate_path,archive,wrapper


def test_four_field_gate_reaches_versioned_validation_before_any_api(tmp_path,monkeypatch):
    module=load();research,records,plan_path,gate_path,archive,wrapper=fixture_context(module,tmp_path,monkeypatch)
    reached=[]
    def gate_boundary(actual):
        assert actual==wrapper
        reached.append('versioned-four-field-gate')
        raise PreApiBoundary('stopped before receipt, API or source access')
    monkeypatch.setattr(module.q,'require_environment_gate',gate_boundary)
    with pytest.raises(PreApiBoundary,match='stopped before receipt'):
        module.query(research,plan_path,gate_path,archive,records)
    assert reached==['versioned-four-field-gate']
    assert not (records/'PREQUERY_EXECUTION.json').exists()


def test_original_first_receipt_guard_still_prevents_replacement(tmp_path,monkeypatch):
    module=load();research,records,plan_path,gate_path,archive,_=fixture_context(module,tmp_path,monkeypatch)
    receipt=records/'PREQUERY_EXECUTION.json';receipt.write_bytes(b'original-diagnostic-receipt')
    with pytest.raises(ValueError,match='prior query receipt retained'):
        module.query(research,plan_path,gate_path,archive,records)
    assert receipt.read_bytes()==b'original-diagnostic-receipt'
