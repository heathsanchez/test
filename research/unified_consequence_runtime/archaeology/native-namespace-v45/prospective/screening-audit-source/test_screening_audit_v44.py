"""Frozen source-free V44 screening audit controls; no target source access."""
import copy
import importlib.util
from pathlib import Path

import pytest


def module():
    path=Path(__file__).with_name('audit_retained_v44.py')
    assert path.is_file(), 'independent V44 screening auditor not implemented'
    spec=importlib.util.spec_from_file_location('v44_screening_audit',path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def record(status='UNKNOWN_SETUP'):
    return {'schema':'UDM_ADMISSION_ONLY_CASE_V44','repository':'fixture/unread',
        'spec_sha256':'a'*64,'screening_mode':'ADMISSION_ONLY_NO_CATALOG_OR_CANDIDATE_SEARCH',
        'accounting_complete':True,'eligible':status in ('PASS_NATIVE','FAIL_NATIVE'),'status':status,
        'total_wall_seconds':1.0,'controller_attempts':{'native_calls':0,'collection_calls':0},
        'build_attempts':{'before':{'builder_attempts':{'build_calls':0,'build_seconds':0.0,'records':[]},'verification_attempts':0},
                          'after':{'builder_attempts':{'build_calls':0,'build_seconds':0.0,'records':[]},'verification_attempts':0}},
        'bootstrap_attempts':{'before':{'backend_calls':0,'backend_seconds':0.0,'records':[]},
                              'after':{'backend_calls':0,'backend_seconds':0.0,'records':[]}}}


def test_both_actual_native_outcomes_have_same_public_eligibility_and_hide_status():
    m=module();good=m.public_fields(record('PASS_NATIVE'));bad=m.public_fields(record('FAIL_NATIVE'))
    assert good==bad
    assert good['schema']=='UDM_SEALED_ADMISSION_ENVELOPE_V44'
    assert good['eligible'] is True and good['status']=='ADMITTED_NATIVE'
    assert 'bootstrap_costs' in good


def test_unknown_cannot_be_promoted_by_public_envelope():
    m=module();r=record();r['eligible']=True
    with pytest.raises(ValueError):m.public_fields(r)


@pytest.mark.parametrize('field,value',[('backend_calls',-1),('backend_calls',1.5),('backend_seconds',float('nan')),('backend_seconds',-1)])
def test_bootstrap_counter_tampering_and_rollback_refuse(field,value):
    m=module();r=record();r['bootstrap_attempts']['after'][field]=value
    with pytest.raises(ValueError):m.bootstrap_costs(r)


def test_bootstrap_record_prefix_cannot_be_rewritten():
    m=module();r=record();r['bootstrap_attempts']['before']['records']=[{'path':'original'}]
    r['bootstrap_attempts']['after']['records']=[{'path':'different'}]
    with pytest.raises(ValueError):m.bootstrap_costs(r)


@pytest.mark.parametrize('change',('missing_witness','generation','observation','request','selection_edge','scope'))
def test_bootstrap_binding_requires_exact_live_source_observation_and_selection(change):
    m=module();binding={'capability_id':'cap','generation':1,'consequence_id':'obs','request_sha256':'r','observation_sha256':'o','environment_selection_id':'choice'}
    request={'commit':'base','protocol_binding':'p','source_identity':{'git_tree':'t'}}
    observed={'source_identity':request['source_identity']}
    selected={'id':'choice','kind':'native_environment_selection_v44','premises':['cap','obs'],'payload':{'binding':{k:v for k,v in binding.items() if k!='environment_selection_id'},'contract_sha256':'c','authority_sha256':'a','policy_sha256':'q'}}
    context={'capability_id':'cap','generation':1,'consequence_id':'obs','request_sha256':'r','observation_sha256':'o',
             'request':request,'observation':observed,'live_ids':{'cap','obs','choice'},'selected':selected,
             'contract_sha256':'c','authority_sha256':'a','policy_sha256':'q','base_commit':'base','protocol_binding':'p','baseline_source':request['source_identity']}
    m.validate_binding(binding,context)
    if change=='missing_witness':context['live_ids'].remove('obs')
    elif change=='generation':binding['generation']=2
    elif change=='observation':binding['observation_sha256']='forged'
    elif change=='request':binding['request_sha256']='wrongtask'
    elif change=='selection_edge':selected['premises']=['cap']
    elif change=='scope':context['base_commit']='differentbase'
    with pytest.raises(ValueError):m.validate_binding(binding,context)


def test_original_native_and_source_checks_are_reused_byte_exactly():
    m=module()
    assert m.old.audit_native.__code__ is m.audit_native.__code__
    assert m.old.audit_partial_packets.__code__ is m.audit_partial_packets.__code__
    assert m.old.validate_context_bytes.__code__ is m.validate_context_bytes.__code__


def test_incomplete_dossier_never_authorizes_finalization():
    m=module()
    for value in ({}, {'status':'PASS_RETAINED_SCREENING_BINDINGS','checks':[]},
                  {'status':'PASS_RETAINED_SCREENING_BINDINGS','checks':[{'pass':False}]}):
        with pytest.raises(ValueError):m.require_closed_dossier(value)


def test_frozen_runtime_alias_reads_exact_regular_target_without_relaxing_case_reader(tmp_path):
    m=module();target=tmp_path/'actual-image';target.write_bytes(b'fixed-executable-image')
    alias=tmp_path/'python';alias.symlink_to(target.name)
    class Reader:
        def read(self,path):
            path=Path(path)
            assert path.resolve()==path and not path.is_symlink()
            return path.read_bytes()
    assert m.runtime_bytes(Reader(),alias)==target.read_bytes()


@pytest.mark.parametrize('change',('other_capability','other_scope','wrong_receipt_generation','missing_witness_edge'))
def test_metadata_witness_cannot_be_rebound_to_another_instrument(change):
    m=module();request={'commit':'base'}
    observation={'metadata':{}}
    invocation={'schema':'UDM_RETAINED_SOURCE_NATIVE_METADATA_INVOCATION_V44',
                'request':m.fp(request),'observation':m.fp(observation),'artifacts':[]}
    binding={'capability_id':'cap','generation':1}
    cap={'generation':1,'scope':{'request_sha256':m.fp(request)},'program':'program'}
    receipt={'schema':'UDM_SOURCE_NATIVE_METADATA_EXECUTION_V44','status':'INDEPENDENT_METADATA_ONLY_NOT_NATIVE_OUTCOME',
             'instrument':'cap','generation':1,'program':'program','invocation':m.fp(invocation)}
    witness={'kind':'verified_consequence','premises':['cap'],'payload':{'family':'source-native-metadata-v44',
             'receipt':m.fp(receipt),'request':m.fp(request),'observation':m.fp(observation)}}
    m.validate_invocation_binding(binding,cap,witness,receipt,request,observation,invocation)
    if change=='other_capability':receipt['instrument']='other'
    elif change=='other_scope':cap['scope']['request_sha256']='otherrequest'
    elif change=='wrong_receipt_generation':receipt['generation']=2
    elif change=='missing_witness_edge':witness['premises']=[]
    with pytest.raises(ValueError):m.validate_invocation_binding(binding,cap,witness,receipt,request,observation,invocation)


@pytest.mark.parametrize('change',('missing_history','exposed_universe'))
def test_complete_prior_exposure_union_cannot_be_weakened(change):
    m=module();prior={'repositories':['old/source','other/exposed']}
    plan={'historically_touched_repository_exclusions':['old/source','other/exposed'],
          'repository_universe_fixed_before_github_queries':['new/unread']}
    m.validate_exposure(plan,prior)
    if change=='missing_history':plan['historically_touched_repository_exclusions']=['old/source']
    else:plan['repository_universe_fixed_before_github_queries']=['other/exposed']
    with pytest.raises(ValueError):m.validate_exposure(plan,prior)


@pytest.mark.parametrize('change',('wrong_family','admission_receipt','program','request','observation'))
def test_metadata_execution_schema_cannot_be_replaced_by_another_cas_receipt(change):
    m=module();request={'commit':'base'};observation={'metadata':{}}
    invocation={'schema':'UDM_RETAINED_SOURCE_NATIVE_METADATA_INVOCATION_V44','request':m.fp(request),'observation':m.fp(observation),'artifacts':[]}
    binding={'capability_id':'cap','generation':1};cap={'generation':1,'scope':{'request_sha256':m.fp(request)},'program':'program'}
    receipt={'schema':'UDM_SOURCE_NATIVE_METADATA_EXECUTION_V44','status':'INDEPENDENT_METADATA_ONLY_NOT_NATIVE_OUTCOME',
             'instrument':'cap','generation':1,'program':'program','invocation':m.fp(invocation)}
    witness={'kind':'verified_consequence','premises':['cap'],'payload':{'family':'source-native-metadata-v44',
             'receipt':m.fp(receipt),'request':m.fp(request),'observation':m.fp(observation)}}
    if change=='wrong_family':witness['payload']['family']='unrelated-family'
    elif change=='admission_receipt':receipt['schema']='UDM_SOURCE_NATIVE_METADATA_ADMISSION_V44'
    elif change=='program':receipt['program']='different'
    elif change=='request':invocation['request']='different'
    else:invocation['observation']='different'
    receipt['invocation']=m.fp(invocation);witness['payload']['receipt']=m.fp(receipt)
    with pytest.raises(ValueError):m.validate_invocation_binding(binding,cap,witness,receipt,request,observation,invocation)


def test_metadata_selection_cannot_lose_its_exact_binding_while_admitted():
    m=module();setup={'status':'PREPARED','selection':{'constraints':{'observation_evidence':{'source_identity':'actual'}}},'bootstrap_binding':None}
    with pytest.raises(ValueError):m.validate_selection_binding_presence(setup,{'eligible':True,'controller_attempts':{'native_calls':2,'collection_calls':4}})


def test_lawful_partial_metadata_refusal_preserves_original_five_field_binding():
    m=module();binding={k:'held' for k in ('capability_id','generation','consequence_id','request_sha256','observation_sha256')}
    setup={'status':'UNKNOWN_SETUP','selection':{'constraints':{'observation_evidence':{}}},'bootstrap_binding':binding}
    m.validate_selection_binding_presence(setup,{'eligible':False,'controller_attempts':{'native_calls':0,'collection_calls':0}})
    with pytest.raises(ValueError):m.validate_selection_binding_presence(setup,{'eligible':True,'controller_attempts':{'native_calls':2,'collection_calls':4}})


def test_unindexed_failed_original_metadata_build_cannot_disappear_from_costs(tmp_path):
    m=module();case=tmp_path/'case-000';output=case/'source-environment/native-metadata-bootstrap/admission/nonce/observe';output.mkdir(parents=True)
    import json
    (output/'build-attempt.json').write_text(json.dumps({'schema':'udm.generic-build-attempt.v1','build_calls':1,'build_seconds':.2,'status':'UNKNOWN_BUILD_EXECUTION'}))
    class Reader:
        def js(self,path):return json.loads(Path(path).read_text())
    with pytest.raises(ValueError):m._bootstrap_attempts(Reader(),case,record())


@pytest.mark.parametrize('change',('schema','build_packages','native_packages','profile'))
def test_selected_environment_witness_binds_both_actual_package_inventories(change):
    m=module();profile={'id':'modern'}
    value={'schema':'UDM_VERIFIED_NATIVE_ENVIRONMENT_SELECTION_V44','build_packages_sha256':'b','native_packages_sha256':'n','profile':profile}
    m.validate_environment_selection_identity(value,'modern','b','n',profile)
    if change=='schema':value['schema']='unverified'
    elif change=='build_packages':value['build_packages_sha256']='forged'
    elif change=='native_packages':value['native_packages_sha256']='forged'
    else:value['profile']={'id':'other'}
    with pytest.raises(ValueError):m.validate_environment_selection_identity(value,'modern','b','n',profile)


@pytest.mark.parametrize('change',('empty','missing_cas','altered_backup','other_path'))
def test_two_metadata_wheels_need_exact_retained_cas_backups(change):
    import base64
    m=module();raw=b'opaque exact wheel data; parser qualified separately'
    first={'wheel_path':'/retained/one/example.whl','wheel_sha256':m.sha(raw)}
    second={'wheel_path':'/retained/two/example.whl','wheel_sha256':m.sha(raw)}
    backup={'schema':'UDM_RETAINED_MATERIALIZATION_WHEEL_V43','filename':'example.whl','base64':base64.b64encode(raw).decode()}
    objects={'backup':backup}
    invocation={'artifacts':[{'evidence':first,'artifact':'backup'},{'evidence':second,'artifact':'backup'}]}
    observation={'evidence':{'build':{'generated_wheel_evidence':first}},'independent_build':{'generated_wheel_evidence':second}}
    m.validate_invocation_artifacts(invocation,observation,objects,lambda path:raw)
    if change=='empty':invocation['artifacts']=[]
    elif change=='missing_cas':objects.clear()
    elif change=='altered_backup':backup['base64']=base64.b64encode(b'altered').decode()
    else:invocation['artifacts'][0]['evidence']=dict(first,wheel_path='/other/one/example.whl')
    with pytest.raises(ValueError):m.validate_invocation_artifacts(invocation,observation,objects,lambda path:raw)
