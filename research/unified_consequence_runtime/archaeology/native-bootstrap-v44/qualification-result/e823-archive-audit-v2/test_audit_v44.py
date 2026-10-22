"""Independent source-free audit controls; hostile packets are data only."""
import base64
import copy
import importlib.util
import io
import json
from pathlib import Path
import sys
import tarfile
import zipfile

import pytest


def auditor():
    path = Path(__file__).with_name('audit_v44.py')
    assert path.is_file(), 'independent V44 audit implementation missing'
    spec = importlib.util.spec_from_file_location('v44_independent_auditor', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def valid_report():
    nodes = ['tests/test_native.py::test_protected']
    data = dict(timeout=False, source_mutations=[], unexpected_imports=[], external_project_imports=[],
        changed_test_code=[], plugin_violations=[], collected_test_nodes=nodes, selected_test_nodes=nodes,
        plugin_manifest=[], test_items=[{'nodeid': nodes[0]}], deselected_test_nodes=[], collection_errors=[],
        process_exit_code=0, reports=[{'nodeid':nodes[0], 'when':phase,'outcome':'passed','wasxfail':''}
                                     for phase in ('setup','call','teardown')])
    collection={key:data[key] for key in ('collected_test_nodes','selected_test_nodes','plugin_manifest','test_items')}
    return data,dict(tests=1,passed=1,failures=0,errors=0,skipped=0),collection


def test_claimed_green_does_not_replace_actual_complete_required_assertion_execution():
    m=auditor();data,counts,collection=valid_report()
    assert m.native_status(data,counts,collection)=='PASS_NATIVE'
    data['status']='PASS_NATIVE';data['reports']=[]
    assert m.native_status(data,counts,collection)!='PASS_NATIVE'


@pytest.mark.parametrize('change',('skipped','xfail','deselected','collection','imports','assertion_phase','empty'))
def test_native_authority_bypass_packets_fail_closed(change):
    m=auditor();data,counts,collection=valid_report()
    if change=='skipped':data['reports'][1]['outcome']='skipped';counts.update(passed=0,skipped=1)
    elif change=='xfail':data['reports'][1]['wasxfail']='declared expected failure'
    elif change=='deselected':data['deselected_test_nodes']=collection['selected_test_nodes']
    elif change=='collection':data['selected_test_nodes']=[]
    elif change=='imports':data['unexpected_imports']=['unwarranted/pytest.py']
    elif change=='assertion_phase':data['reports'][1]['when']='setup'
    elif change=='empty':collection['selected_test_nodes']=[];data['selected_test_nodes']=[];data['reports']=[];counts.update(tests=0,passed=0)
    assert m.native_status(data,counts,collection)!='PASS_NATIVE'


def test_packet_requires_exact_nonempty_retained_hash_inventory():
    m=auditor();raw={'report.json':b'{}','checked-report.json':b'{"mode":"run"}'}
    value={'packet':{k:base64.b64encode(v).decode() for k,v in raw.items()},
           'packet_sha256':{k:m.sha(v) for k,v in raw.items()}}
    assert m.verify_packet(value)==raw
    wrong=copy.deepcopy(value);wrong['packet_sha256']['report.json']='0'*64
    with pytest.raises(ValueError):m.verify_packet(wrong)
    wrong=copy.deepcopy(value);del wrong['packet_sha256']['checked-report.json']
    with pytest.raises(ValueError):m.verify_packet(wrong)
    with pytest.raises(ValueError):m.verify_packet({'packet':{},'packet_sha256':{}})


def test_gate_files_are_literal_data_never_executed(tmp_path):
    m=auditor();bad=tmp_path/'must-not-exist'
    source=('TESTS=("test_one.py",)\nBOOTSTRAP_GATE_FILES=tuple(PREFIX+x for x in ("native_metadata_v44.py",*TESTS))+(".github/workflows/x.yml",)\n').encode()
    assert m.gate_files(source)==[m.PREFIX+'native_metadata_v44.py',m.PREFIX+'test_one.py','.github/workflows/x.yml']
    malicious=('BOOTSTRAP_GATE_FILES=__import__("pathlib").Path('+repr(str(bad))+').touch()\n').encode()
    with pytest.raises(ValueError):m.gate_files(malicious)
    assert not bad.exists()


@pytest.mark.parametrize('name',('../outside','/absolute','back\\slash','a/../b'))
def test_unsafe_archive_paths_never_become_host_paths(tmp_path,name):
    m=auditor();store=m.Store(tmp_path/'cache');member=tarfile.TarInfo(name);member.size=1
    with pytest.raises(ValueError):store.add(member,io.BytesIO(b'x'))


def test_duplicate_archive_path_and_symlink_cannot_be_read_as_regular_bytes(tmp_path):
    m=auditor();store=m.Store(tmp_path/'cache');member=tarfile.TarInfo('record.json');member.size=2
    store.add(member,io.BytesIO(b'{}'))
    with pytest.raises(ValueError):store.add(member,io.BytesIO(b'{}'))
    link=tarfile.TarInfo('link.json');link.type=tarfile.SYMTYPE;link.linkname='/etc/passwd';store.add(link)
    with pytest.raises(ValueError):store.raw('link.json')


def test_artifact_zip_digest_cannot_be_relabelled_as_green(tmp_path):
    m=auditor();path=tmp_path/'artifact.zip'
    with zipfile.ZipFile(path,'w') as z:z.writestr('native-result.json','{"status":"PASS_NATIVE"}')
    row={'size_in_bytes':path.stat().st_size,'digest':'sha256:'+m.sha(path.read_bytes())}
    assert m.verify_artifact_digest(path,row)==row['digest'][7:]
    row['digest']='sha256:'+'0'*64
    with pytest.raises(ValueError):m.verify_artifact_digest(path,row)


def test_exact_support_withdrawal_is_recomputed_from_causal_edges():
    m=auditor();rows=[{'id':'a','kind':'support','premises':[],'payload':{}},
      {'id':'b','kind':'capability','premises':['a'],'payload':{}},
      {'id':'u','kind':'support','premises':[],'payload':{}},
      {'id':'c','kind':'outcome','premises':['b'],'payload':{}},
      {'id':'r','kind':'revoke','premises':[],'payload':{'target':'a'}}]
    assert m.live_nodes(rows[:4])=={'a','b','u','c'}
    assert m.live_nodes(rows)=={'u'}



def test_all_uploaded_zip_members_require_complete_unambiguous_evidence_coverage():
    m=auditor()
    core={'MANIFEST.json','SOURCE.tar.gz','NATIVE_BOOTSTRAP_V44_EVIDENCE.tar.gz'}
    body=b'actual retained native evidence'
    entries={'run/RESULT.json':{'kind':'file','sha256':m.sha(body)}}
    names=[*core,'run/RESULT.json']
    m.verify_uploaded_members(names,core,entries,lambda name:body)
    with pytest.raises(ValueError):
        m.verify_uploaded_members([*names,'unindexed.json'],core,entries,lambda name:body)
    ambiguous={'run/RESULT.json':entries['run/RESULT.json'],'RESULT.json':entries['run/RESULT.json']}
    with pytest.raises(ValueError):
        m.verify_uploaded_members([*core,'prefix/run/RESULT.json'],core,ambiguous,lambda name:body)
    wrong=dict(entries,**{'run/RESULT.json':{'kind':'file','sha256':'0'*64}})
    with pytest.raises(ValueError):
        m.verify_uploaded_members(names,core,wrong,lambda name:body)



def capability_lineage_fixture(m):
    program={'schema':'p'};desc={'schema':'s','authority_ceiling':{'external_effects':'NONE'},'source_sha256':{'a.py':'a'*64}}
    scope={'request_sha256':'r'};cap={'operation':'source.observe_native_metadata','source':desc,'scope':scope,'program':'program',
      'observation':'invocation','generation':1,'dependencies':['support'],'evidence':['verified'],'transition':'SCOPED_ADMISSION','supersedes':None}
    support_payload={'family':'source-native-metadata-v44','program':'program','generation':1,'nonce':'e'*64,'supersedes':None,'request':'request','invocation':'invocation'}
    receipt={'schema':'UDM_SOURCE_NATIVE_METADATA_ADMISSION_V44','status':'INDEPENDENT_METADATA_ONLY_NOT_NATIVE_OUTCOME',**support_payload}
    objects={'program':program,'invocation':{'request':'request'},'receipt':receipt}
    nodes={'authority':{'id':'authority','kind':'execution_authority_ceiling','payload':desc['authority_ceiling'],'premises':[]},
      'origin':{'id':'origin','kind':'native_metadata_source_v44','payload':desc,'premises':['authority']},
      'support':{'id':'support','kind':'source_support','payload':support_payload,'premises':['origin','authority']},
      'verified':{'id':'verified','kind':'native_metadata_verification_v44','payload':{'program':'program','receipt':'receipt'},'premises':['support']},
      'cap':{'id':'cap','kind':'executable_capability','payload':cap,'premises':['support','verified']}}
    return nodes,objects,program,desc,scope


@pytest.mark.parametrize('change',('source_subset','missing_origin','forged_ceiling','wrong_origin','nonce','generation','verification','support_payload'))
def test_metadata_lineage_cannot_drop_original_authority_or_source_pins(change):
    m=auditor();nodes,objects,program,desc,scope=capability_lineage_fixture(m)
    m.validate_metadata_lineage(nodes['cap'],nodes,objects,program,desc,scope,1)
    if change=='source_subset':nodes['cap']['payload']['source']={**desc,'source_sha256':{}}
    elif change=='missing_origin':nodes['support']['premises']=[]
    elif change=='forged_ceiling':nodes['authority']['payload']={'external_effects':'self-granted'}
    elif change=='wrong_origin':nodes['origin']['kind']='ordinary_description'
    elif change=='nonce':nodes['support']['payload']['nonce']='replay'
    elif change=='generation':nodes['cap']['payload']['generation']=999
    elif change=='verification':nodes['verified']['premises']=[]
    elif change=='support_payload':nodes['support']['payload']['family']='another-operation'
    with pytest.raises(ValueError):m.validate_metadata_lineage(nodes['cap'],nodes,objects,program,desc,scope,1)


def test_route_publication_requires_exact_capability_evidence_and_validator_source():
    m=auditor();contract={'input_type':'a','output_type':'b','authority_snapshot':'c','verifier_id':'d'}
    cap={'program':'program','source':{'implementation':'exact'},'observation':'observation','scope':{'frontier_contract':contract,'frontier_profiles':['profile']},'evidence':['verify']}
    verified={'id':'verify','kind':'native_metadata_verification_v44','payload':{'program':'program','receipt':'receipt'}}
    nodes={'cap':{'id':'cap','kind':'executable_capability','payload':cap},'verify':verified}
    payload={'schema':'metalogic.native-frontier.route.v1','capability_id':'cap','verification_id':'verify','program':'program','receipt':'receipt',
      'evidence_binding':m.fp(verified['payload']),'source_sha256':m.fp(cap['source']),'validator_source_sha256':'v'*64,
      'contract':contract,'profiles':['profile'],'meaning':'INDEPENDENTLY_WARRANTED_EXECUTABLE_ROUTE_AVAILABLE'}
    node={'id':'route','kind':'native_frontier_route','payload':payload,'premises':['cap','verify']}
    objects={'program':{'p':1},'observation':{'o':1},'receipt':{'r':1}}
    m.validate_publication(node,nodes,objects,{'native_metadata_verification_v44':'v'*64})
    for field in ('program','receipt','evidence_binding','source_sha256','validator_source_sha256'):
        wrong=copy.deepcopy(node);wrong['payload'][field]='forged'
        with pytest.raises(ValueError):m.validate_publication(wrong,nodes,objects,{'native_metadata_verification_v44':'v'*64})
    wrong=copy.deepcopy(node);wrong['premises']=[]
    with pytest.raises(ValueError):m.validate_publication(wrong,nodes,objects,{'native_metadata_verification_v44':'v'*64})



@pytest.mark.parametrize('raw',[
    b'Name: fixture\nVersion: 1.0.0\n\n',
    b'Metadata-Version: 2.1\nVersion: 1.0.0\n\n',
    b'Metadata-Version: 2.1\nName: fixture\n\n',
    b'Metadata-Version: 2.1\nName: another\nVersion: 1.0.0\n\n',
    b'Metadata-Version: 2.1\nName: fixture\nVersion: 2.0.0\n\n',
    b'Metadata-Version: 2.1\nName: fixture\nVersion: 1.0.0\nDynamic: Requires-Python, Requires-Dist\n\n',
])
def test_independent_core_metadata_cannot_accept_missing_forged_or_dynamic_headers(raw):
    m=auditor()
    with pytest.raises(ValueError):m.core_metadata_fields({'fixture-1.0.0.dist-info/METADATA':raw})


def test_fresh_qualification_requires_disjoint_actual_native_build_paths():
    m=auditor()
    a={'evidence':{'build':{'generated_wheel_evidence':{'wheel_path':'/old/observed.whl'}}},'independent_build':{'generated_wheel_evidence':{'wheel_path':'/old/independent.whl'}}}
    b=copy.deepcopy(a);b['evidence']['build']['generated_wheel_evidence']['wheel_path']='/fresh/observed.whl';b['independent_build']['generated_wheel_evidence']['wheel_path']='/fresh/independent.whl'
    assert m.fresh_observation_paths(a,b)
    assert not m.fresh_observation_paths(a,a)
    b['independent_build']['generated_wheel_evidence']['wheel_path']='/old/independent.whl'
    assert not m.fresh_observation_paths(a,b)



def test_original_protected_fixture_bytes_cannot_be_replaced_with_noop_tests():
    m=auditor();full=b'from native_bootstrap_alpha import protected_value\n\n\ndef test_original_pass():\n    assert protected_value() == 41\n\n\ndef test_protected_failure():\n    assert protected_value() == 42\n'
    fixture={'tests/test_protected.py':full,'src/native_bootstrap_alpha/__init__.py':b'def protected_value():\n    return 41\n'}
    passing=full.split(b'\n\ndef test_protected_failure():')[0]+b'\n'
    import_only=passing.split(b'\n\ndef test_original_pass():')[0]+b'\n'
    base=dict(fixture,**{'tests/test_protected.py':import_only});aug=dict(fixture,**{'tests/test_protected.py':passing})
    m.validate_fixture_context('PASS',base,aug,fixture)
    wrong=dict(aug,**{'tests/test_protected.py':passing.replace(b'assert protected_value() == 41',b'pass')})
    with pytest.raises(ValueError):m.validate_fixture_context('PASS',base,wrong,fixture)
    wrong=dict(base,**{'src/native_bootstrap_alpha/__init__.py':b'def protected_value():\n    return 42\n'})
    with pytest.raises(ValueError):m.validate_fixture_context('PASS',wrong,aug,fixture)



def test_independent_reexecution_annotation_requires_actual_fresh_packet_and_costs():
    m=auditor();data,counts,collection=valid_report()
    original={'status':'PASS_NATIVE','junit':counts,'execution':dict(data,costs={'seconds':1}),'costs':{'native_calls':1,'collection_calls':1,'total_seconds':2}}
    fresh=copy.deepcopy(original);fresh['execution']['costs']['seconds']=2;fresh['costs']['total_seconds']=3
    note={'output':'/retained/independent','costs':fresh['costs']};wrapped=dict(original,independent_reexecution=note)
    class Evidence:
        def path_for_absolute(self,path):
            if path!='/retained/independent/receipt.json':raise ValueError('unbound actual packet')
            return 'run/native-pass/independent/receipt.json'
        def js(self,path):return copy.deepcopy(fresh)
    assert m.resolve_independent_receipt(wrapped,Evidence(),'run/native-pass/independent/receipt.json')==fresh
    bad=copy.deepcopy(wrapped);bad['independent_reexecution']['costs']['total_seconds']=999
    with pytest.raises(ValueError):m.resolve_independent_receipt(bad,Evidence(),'run/native-pass/independent/receipt.json')
    bad=copy.deepcopy(wrapped);bad['independent_reexecution']['output']='/unretained/original'
    with pytest.raises(ValueError):m.resolve_independent_receipt(bad,Evidence(),'run/native-pass/independent/receipt.json')
    with pytest.raises(ValueError):m.resolve_independent_receipt(wrapped,Evidence(),'run/wrong/receipt.json')
    fresh['status']='FAIL_NATIVE'
    with pytest.raises(ValueError):m.resolve_independent_receipt(wrapped,Evidence(),'run/native-pass/independent/receipt.json')


def test_metadata_authority_scope_survives_a_prior_native_task_ledger(monkeypatch):
    """Two-ledger orchestration only; no mocked native result may mint a gate."""
    m=auditor()
    metadata_contract={'input_type':'OriginalBackend','output_type':'Metadata','authority_snapshot':'metadata-authority','verifier_id':'metadata-verifier'}
    external_authority={'external_effects':'NONE'}
    native_contract={'task':'different-protected-native-contract'}
    native_authority={'native_assertion_authority':'different-from-external-ceiling'}
    class Source:
        def raw(self,name):
            if name.endswith('decisive_native_frontier.py'):return ('AUTHORITY='+repr(external_authority)).encode()
            if name.endswith('native_bootstrap_runtime_v44.py'):return ('FRONTIER_CONTRACT='+repr(metadata_contract)).encode()
            return b'archived immutable placeholder; not executed'
    observation={'retained':'metadata-bytes'}
    binding={'capability_id':'instrument','consequence_id':'witness','environment_selection_id':'selected','observation_sha256':m.fp(observation),'generation':1}
    metadata_binding={k:v for k,v in binding.items() if k!='environment_selection_id'}
    catalog={'profiles':[]};choice={'status':'CANDIDATE_SOURCE_ENVIRONMENT','selected_profile':'profile','catalog_sha256':m.fp(catalog),'constraints':{'observation_evidence':{'observation_sha256':m.fp(observation)}}}
    native_objects={'binding':binding,'contract':native_contract,'authority':native_authority,'policy':{},'selection':choice,'catalog':catalog,'receipt':{'invocation':'invocation'},'invocation':{'observation':'observation'},'observation':observation}
    def row(ident,kind,payload,premises=()):return {'id':ident,'kind':kind,'payload':payload,'premises':list(premises)}
    native_rows=[row('instrument','support',{'generation':1}),row('witness','support',{'receipt':'receipt'}),
      row('selected','native_environment_selection_v44',{'binding':metadata_binding,'contract_sha256':m.fp(native_contract),'authority_sha256':m.fp(native_authority),'policy_sha256':m.fp({}),'environment_operation_sha256':m.sha(Source().raw('native_environment_v44.py')),'selection':'selection','catalog':'catalog','profile':'profile'},['instrument','witness']),
      row('observed','support',{},['instrument','witness','selected']),
      row('native','executable_capability',{'operation':'native.pytest_suite','source':{'bootstrap_binding':'binding','contract':'contract','suite_authority':'authority','policy':'policy'},'dependencies':['instrument','observed','witness','selected'],'scope':{'metadata_bootstrap':binding}},['instrument','observed','witness','selected'])]
    request={'environment_sha256':'e'*64}
    metadata_objects={'invocation':{'request':'request','observation':'observation'},'request':request,'observation':observation}
    metadata_rows=[row('support','source_support',{}),row('verified','native_metadata_verification_v44',{}),row('metadata','executable_capability',{'operation':'source.observe_native_metadata','dependencies':['support'],'evidence':['verified'],'observation':'invocation'})]
    class Evidence:
        def matching(self,suffix):return ['native/metatron-ledger.jsonl','metadata/metatron-ledger.jsonl']
    def ledger(name,evidence,check):
        if name.startswith('native/'):return native_rows,native_objects,'native'
        return metadata_rows,metadata_objects,'metadata'
    monkeypatch.setattr(m.old,'audit_ledger',ledger)
    monkeypatch.setattr(m,'audit_flash',lambda *args:None)
    monkeypatch.setattr(m.old,'audit_cas_native_links',lambda *args:{'native_capabilities':[]})
    class ScopeChecked(Exception):pass
    def check_scope(node,nodes,objects,program,descriptor,scope,generation):
        assert scope['frontier_contract']==metadata_contract
        assert scope['authority_ceiling']==external_authority
        assert descriptor['authority_ceiling']==external_authority
        raise ScopeChecked('stop before unrelated native/metadata evidence checks')
    monkeypatch.setattr(m,'validate_metadata_lineage',check_scope)
    with pytest.raises(ScopeChecked):m.audit_causal(Source(),Evidence(),{}, {},m.Checks())


def metadata_invocation_artifact_fixture(m):
    buffer=io.BytesIO()
    with zipfile.ZipFile(buffer,'w') as wheel:wheel.writestr('fixture-1.0.0.dist-info/METADATA',b'Metadata-Version: 2.1\nName: fixture\nVersion: 1.0.0\n\n')
    raw=buffer.getvalue();members=m.strict_wheel_members(raw)
    wheels=[{'wheel_path':'/retained/'+phase+'/fixture-1.0.0-py3-none-any.whl','wheel_sha256':m.sha(raw),'wheel_content_sha256':m.fp({n:m.sha(v) for n,v in sorted(members.items())})} for phase in ('observe','independent')]
    retained={'schema':'UDM_RETAINED_MATERIALIZATION_WHEEL_V43','filename':'fixture-1.0.0-py3-none-any.whl','base64':base64.b64encode(raw).decode()}
    observation={'evidence':{'build':{'generated_wheel_evidence':wheels[0]}},'independent_build':{'generated_wheel_evidence':wheels[1]}}
    request={'repo_path':'/retained/immutable-source','commit':'a'*40}
    objects={m.fp(retained):retained,m.fp(request):request,m.fp(observation):observation}
    invocation={'schema':'UDM_RETAINED_SOURCE_NATIVE_METADATA_INVOCATION_V44','request':m.fp(request),'observation':m.fp(observation),'artifacts':[{'evidence':w,'artifact':m.fp(retained)} for w in sorted(wheels,key=lambda value:value['wheel_path'])]}
    class Evidence:
        def path_for_absolute(self,path):
            if path not in {w['wheel_path'] for w in wheels}:raise ValueError('unbound actual native wheel')
            return path
        def raw(self,path):return raw
    return invocation,objects,Evidence()


@pytest.mark.parametrize('change',('empty','one','duplicate','reordered','descriptor','kind','cas_bytes','missing_cas','filename','extra_invocation'))
def test_every_metadata_invocation_requires_both_exact_cas_backed_original_wheels(change):
    m=auditor();invocation,objects,evidence=metadata_invocation_artifact_fixture(m)
    m.validate_metadata_invocation_artifacts(invocation,objects,evidence)
    if change=='empty':invocation['artifacts']=[]
    elif change=='one':invocation['artifacts'].pop()
    elif change=='duplicate':invocation['artifacts'][1]=copy.deepcopy(invocation['artifacts'][0])
    elif change=='reordered':invocation['artifacts'].reverse()
    elif change=='descriptor':invocation['artifacts'][0]['evidence']=dict(invocation['artifacts'][0]['evidence'],wheel_sha256='0'*64)
    elif change=='kind':objects[invocation['artifacts'][0]['artifact']]['schema']='unwarranted-wheel-description'
    elif change=='cas_bytes':objects[invocation['artifacts'][0]['artifact']]['base64']=base64.b64encode(b'forged wheel').decode()
    elif change=='missing_cas':del objects[invocation['artifacts'][0]['artifact']]
    elif change=='filename':objects[invocation['artifacts'][0]['artifact']]['filename']='another.whl'
    elif change=='extra_invocation':invocation['unwarranted_field']=True
    with pytest.raises(ValueError):m.validate_metadata_invocation_artifacts(invocation,objects,evidence)
