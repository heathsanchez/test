"""Source-free independent screening transport controls; no native tests."""
import base64
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent


def module():
    path = HERE/'audit_retained_v45.py'
    assert path.is_file(), 'V45 independent screening transport missing'
    spec = importlib.util.spec_from_file_location('v45_screening_audit', path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def record(status='UNKNOWN_SETUP'):
    return {'schema':'UDM_ADMISSION_ONLY_CASE_V45','repository':'fixture/unread',
        'spec_sha256':'a'*64,'screening_mode':'ADMISSION_ONLY_NO_CATALOG_OR_CANDIDATE_SEARCH',
        'accounting_complete':True,'eligible':status in ('PASS_NATIVE','FAIL_NATIVE'),'status':status,
        'total_wall_seconds':1.0,'controller_attempts':{'native_calls':0,'collection_calls':0},
        'build_attempts':{'before':{'builder_attempts':{'build_calls':0,'build_seconds':0.,'records':[]},'verification_attempts':0},
                          'after':{'builder_attempts':{'build_calls':0,'build_seconds':0.,'records':[]},'verification_attempts':0}},
        'bootstrap_attempts':{'before':{'backend_calls':0,'backend_seconds':0.,'records':[]},
                              'after':{'backend_calls':0,'backend_seconds':0.,'records':[]}}}


def test_actual_pass_fail_keep_identical_public_eligibility():
    m=module()
    assert m.public_fields(record('PASS_NATIVE'))==m.public_fields(record('FAIL_NATIVE'))
    assert m.public_fields(record('PASS_NATIVE'))['schema']=='UDM_SEALED_ADMISSION_ENVELOPE_V45'


@pytest.mark.parametrize('version',('V43','V44'))
def test_old_outer_schema_is_not_new_admission(version):
    m=module();r=record('PASS_NATIVE');r['schema']='UDM_ADMISSION_ONLY_CASE_'+version
    with pytest.raises(ValueError):m.public_fields(r)


def test_unknown_cannot_be_promoted():
    m=module();r=record();r['eligible']=True
    with pytest.raises(ValueError):m.public_fields(r)


def test_transport_keeps_metadata_and_generated_build_schemas():
    m=module()
    assert m.transport_literal('UDM_SOURCE_NATIVE_METADATA_OBSERVATION_V44')=='UDM_SOURCE_NATIVE_METADATA_OBSERVATION_V44'
    assert m.transport_literal('UDM_INDEPENDENT_GENERATED_BUILD_VERIFICATION_V43')=='UDM_INDEPENDENT_GENERATED_BUILD_VERIFICATION_V43'
    assert m.transport_literal('native_admission_request_v43')=='native_admission_request_v43'
    assert m.transport_literal('UDM_GENERIC_NATIVE_PYTEST_V43')=='UDM_GENERIC_NATIVE_PYTEST_V45'


@pytest.mark.parametrize('change',('runner','task','candidate'))
def test_exact_v45_receipt_identity_remains_joint_binding(change):
    m=module();contract={'repository':'fixture/unread','commit':'b'*40,'protocol_binding':'p',
        'git_tree':'t','tracked_tree_sha256':'s','file_count':2}
    environment={'executable_sha256':'e'};contract['environment_sha256']=m.fp(environment)
    authority={'schema':'UDM_NATIVE_SUITE_AUTHORITY_V45'};policy={'schema':'UDM_NATIVE_EXECUTION_POLICY_V45'}
    cert={'schema':'UDM_NATIVE_ADMISSION_CERTIFICATE_V45','environment':environment,'plugins':[]}
    candidate={'replacements':[]}
    receipt={'schema':'UDM_GENERIC_NATIVE_PYTEST_V45','repository':contract['repository'],'commit':contract['commit'],
      'protocol_binding':'p','source':{k:contract[k] for k in ('git_tree','tracked_tree_sha256','file_count')},
      'contract_sha256':m.fp(contract),'authority_sha256':m.fp(authority),'policy_sha256':m.fp(policy),
      'certificate_sha256':m.fp(cert),'candidate_sha256':m.fp(candidate),'runner_sha256':'runner',
      'environment':environment,'plugins':[]}
    assert m.archive.receipt_identity_matches(receipt,contract,authority,policy,cert,candidate,'runner')
    if change=='runner':receipt['runner_sha256']='other'
    elif change=='task':receipt['commit']='c'*40
    else:receipt['candidate_sha256']='forged'
    assert not m.archive.receipt_identity_matches(receipt,contract,authority,policy,cert,candidate,'runner')


def test_new_authority_uses_original_typed_git_bytes_and_independent_v45_grammar():
    m=module();before={'tests/test_case.py':b'def test_original():\n    assert 1 == 1\n'}
    after={'tests/test_case.py':b'def test_original():\n    assert 1 == 2\n'}
    def snap(files):return {'files':files,'manifest':[{'path':k,'mode':'100644'} for k in files],
                           'identity':{'git_tree':'tree','tracked_tree_sha256':'sha','file_count':len(files)}}
    actual=m.derive_authority(snap(before),snap(after),'base','augmented','binding','fixture/unread')
    assert actual['schema']=='UDM_NATIVE_SUITE_AUTHORITY_V45'
    assert actual['required_test_nodes']==['tests/test_case.py::test_original']
    assert actual['namespace_certificate']['required_declarations']['tests/test_case.py::test_original']['origin']=='test_original'
    assert actual['source_commit']=='augmented' and actual['baseline_commit']=='base'


@pytest.mark.parametrize('change',('already-exposed','missing-prior','wrong-count'))
def test_supplemental_ros_exposure_is_separate_strict_prequery_boundary(change):
    m=module();plan={'historically_touched_repository_exclusions':['old/exposed'],
       'repository_universe_fixed_before_github_queries':['new/unread']}
    prior={'repositories':['old/exposed']}
    addendum={'repositories':['documentary/exposed','old/exposed'],'repository_count':2}
    m.validate_supplemental_exposure(plan,prior,addendum)
    if change=='already-exposed':plan['repository_universe_fixed_before_github_queries']=['documentary/exposed']
    elif change=='missing-prior':addendum['repositories']=['documentary/exposed'];addendum['repository_count']=1
    else:addendum['repository_count']=3
    with pytest.raises(ValueError):m.validate_supplemental_exposure(plan,prior,addendum)


def test_independent_expected_outer_code_is_required_even_for_schema_valid_receipt():
    m=module();expected={'required_test_nodes':['tests/t.py::test_x'],
      'namespace_certificate':{'required_declarations':{'tests/t.py::test_x':{'path':'tests/t.py','source_sha256':'source'}}}}
    compiled={'declarations':{'tests/t.py::test_x':{'code_sha256':['original']}}}
    packet={'test_items':[{'nodeid':'tests/t.py::test_x','path':'tests/t.py','sha256':'source','code_sha256':'original'}]}
    m.declaration_audit.compare_outer(packet,expected,compiled)
    packet['test_items'][0]['code_sha256']='forged-wrapper'
    with pytest.raises(ValueError):m.declaration_audit.compare_outer(packet,expected,compiled)


def test_final_dossier_requires_all_new_namespace_closures():
    m=module();v={'status':'PASS_RETAINED_SCREENING_BINDINGS','checks':[{'pass':True}],
                 'namespace_authority_closed':False,'declaration_compilations':[]}
    with pytest.raises(ValueError):m.require_closed_dossier(v)


def test_complete_typed_git_identity_keeps_original_keyword_defaults(tmp_path):
    m=module()
    fixtures=m.load(Path(m._raw.HERE)/'test_raw_identity.py','_v45_original_raw_fixture')
    repo,base,aug,before_files,after_files=fixtures.fixture(tmp_path)
    before=m.identity.raw_snapshot(repo,base)
    after=m.identity.raw_snapshot(repo,aug,filesystem=True)
    authority=m.derive_authority(before,after,base,aug,'binding','fixture/unread')
    contract={'repo_path':str(repo),'commit':aug,'repository':'fixture/unread','protocol_binding':'binding',**after['identity']}
    checked=m.identity.audit_source(contract,authority,None,tmp_path,include_scm=False)
    assert checked['coverage_complete'] is True
    assert checked['rederived_authority']==authority
    assert checked['files']==after_files and checked['base_files']==before_files


def test_main_transport_is_closed_before_any_real_inputs():
    m=module();prepared=m.prepare_main_binding()
    assert callable(prepared)
    def strings(code):
        for value in code.co_consts:
            if hasattr(value,'co_consts'):yield from strings(value)
            elif isinstance(value,str):yield value
    constants=set(strings(prepared.__code__))
    assert '--compiler-runtimes' in constants
    assert 'UDM_NATIVE_CLI_AUTHORITY_V45' in constants
    assert 'research/unified_consequence_runtime/native_execution_v45.py' in constants


@pytest.mark.parametrize('change',('missing','altered','failed-compiler'))
def test_dossier_cannot_close_missing_or_changed_independent_compiler_artifacts(tmp_path,change):
    m=module();folder=tmp_path/'compiler';folder.mkdir()
    inp=folder/'input.json';inp.write_text('{}\n')
    out=folder/'output.json';out.write_text('{"schema":"INDEPENDENT_ORIGINAL_DECLARATION_COMPILE_V1"}\n')
    event={'status':'PASS_INDEPENDENT_ORIGINAL_DECLARATION_BINDING','seconds':0.1,
      'input_sha256':m.sha(inp.read_bytes()),'output_sha256':m.sha(out.read_bytes()),
      'command':['selected-python','-I','-B',str(HERE/'fresh_compile.py'),str(inp),str(out)],
      'native_test_execution':False}
    value={'status':'PASS_RETAINED_SCREENING_BINDINGS','checks':[{'pass':True}],
      'namespace_authority_closed':True,'declaration_compilations':[event],
      'cases':[{'eligible':True,'identity':{'native_receipts':[
        {'namespace_compilation':{'path':str(out),'sha256':m.sha(out.read_bytes())}}]}}]}
    m.require_closed_dossier(value)
    if change=='missing':out.unlink()
    elif change=='altered':out.write_text('{}\n')
    else:event['status']='ATTEMPTED_PURE_COMPILE'
    with pytest.raises(ValueError):m.require_closed_dossier(value)


@pytest.mark.parametrize('change',('none','native-image','host-image','stale-environment-path'))
def test_compiler_uses_authenticated_per_case_venv_not_host_profile_path(tmp_path,change):
    m=module();host=tmp_path/'host-profile/bin/python';native=tmp_path/'case/source-environment/native/venv/bin/python'
    for path in (host,native):path.parent.mkdir(parents=True);path.write_bytes(b'fixed interpreter image; source-free data')
    site=native.parent.parent/'lib/python3.12/site-packages'
    for name in ('_pytest/__init__.py','pytest/__init__.py'):
        path=site/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'# authenticated package-source fixture\n')
    profile={'id':'fixture-profile','python_version':'3.12.14','pytest_version':'8.4.1'}
    setup={'contract':{'interpreter':str(native)},'selection':{'selected_profile':profile}}
    environment={'executable':str(native),'executable_sha256':m.sha(native.read_bytes())}
    runtimes={profile['id']:str(host)}
    if change=='native-image':native.write_bytes(b'changed native image')
    elif change=='host-image':host.write_bytes(b'changed selected host image')
    elif change=='stale-environment-path':environment['executable']=str(host)
    if change!='none':
        with pytest.raises(ValueError):m.select_compiler_profile(setup,environment,runtimes)
    else:
        actual=m.select_compiler_profile(setup,environment,runtimes)
        assert actual['interpreter']==str(native) and actual['interpreter']!=str(host)
        assert actual['site']==str(site)
        assert actual['authenticated_python_source']=={
            '_pytest/__init__.py':m.sha(b'# authenticated package-source fixture\n'),
            'pytest/__init__.py':m.sha(b'# authenticated package-source fixture\n')}

