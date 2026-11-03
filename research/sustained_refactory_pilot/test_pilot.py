import importlib.util
from pathlib import Path
import pytest

P=Path(__file__).with_name('pilot.py')

def module():
    spec=importlib.util.spec_from_file_location('pilot',P)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def test_empty_or_partial_native_maps_never_warrant():
    m=module()
    assert m.classify({},['1'])['status']=='UNKNOWN_INCOMPLETE_NATIVE_TESTS'
    assert m.classify({'1':True},['1','2'])['status']=='UNKNOWN_INCOMPLETE_NATIVE_TESTS'
    assert m.classify({'1':True},['1'])['status']=='PASS_NATIVE'
    assert m.classify({'1':False},['1'])['status']=='FAIL_NATIVE'
    assert m.classify({'1':1},['1'])['status']=='UNKNOWN_INCOMPLETE_NATIVE_TESTS'

def test_eval_rows_cannot_enter_training_memory():
    m=module()
    with pytest.raises(ValueError,match='evaluation'):
        m.support_pairs([{'split':'eval','source':'x','improvements':[[['Return','value'],['CONST',0]]]}])

def test_supported_signatures_need_distinct_sources():
    m=module()
    a={'split':'train','source':'x','improvements':[[['Return','value'],['CONST',0]]]}
    assert len(set((repr(s),p) for s,p in m.support_pairs([a,a])))==1

def test_metadata_selection_is_disjoint_and_complete():
    m=module();p=m.protocol()
    assert len(p['train'])==len(p['eval'])==12
    assert not set(p['train'])&set(p['eval'])
    assert [t for n in [0,4,8,12] for t in p['eval_shards'][str(n)]]==p['eval']

def test_all_arms_receive_same_initial_search():
    m=module();src='def f(x):\n    return x+1\n'
    for arm in 'ABCD':
        assert m.candidates(src,[],arm)==m.candidates(src,[],'A')

def test_oracle_reply_must_bind_source_verifier_and_complete_cases():
    m=module();binding={'protocol':'x','verifier':'y'}
    good={'status':'PASS_NATIVE','passed':1,'tests':1,'cases':{'1':True},'candidate_sha256':'z','binding':binding}
    assert m.check_reply(good,'z',binding)['status']=='PASS_NATIVE'
    for forged in [dict(good,candidate_sha256='other'),dict(good,binding={}),dict(good,passed=0),dict(good,cases={})]:
        with pytest.raises(ValueError):m.check_reply(forged,'z',binding)

def test_selfconsistent_truncated_oracle_map_is_refused():
    # The source-authoritative expected test set contains two cases.
    # A child process must not make a one-case green report authoritative.
    m=module()
    binding={'protocol':'x','verifier':'y','native_case_ids':['1','2']}
    partial={'status':'PASS_NATIVE','passed':1,'tests':1,'cases':{'1':True},
             'candidate_sha256':'z','binding':binding}
    with pytest.raises(ValueError,match='case|coverage|test'):
        m.check_reply(partial,'z',binding)

def test_arm_order_counterbalances_positions():
    m=module();rows=[m.arm_order(i) for i in range(4)]
    assert all(set(r)==set('ABCD') for r in rows)
    assert all(set(r[i] for r in rows)==set('ABCD') for i in range(4))

def test_graph_refuses_wrong_protocol_before_any_task_access():
    import types
    m=module();g=m.Graph.__new__(m.Graph);g.current=['c']
    cap=types.SimpleNamespace(operation='refactory.v104.retained_search',source=m.protocol()['generator_source'],scope={'protocol_binding':'wrong'})
    g.machine=types.SimpleNamespace(mt=types.SimpleNamespace(live_ids=lambda log:['c']),log=[],flash_live_ids=lambda:{'c'},descriptor=lambda key:cap)
    with pytest.raises(ValueError,match='profile'):g.signatures()

def test_graph_refuses_fabricated_support_before_any_task_access():
    import types
    m=module();g=m.Graph.__new__(m.Graph)
    g.machine=types.SimpleNamespace(log=[types.SimpleNamespace(id='x',kind='fabricated',premises=[])])
    with pytest.raises(ValueError,match='forged'):g._check_support('x',[])

def test_graph_refuses_changed_generator_before_any_task_access():
    import types
    m=module();g=m.Graph.__new__(m.Graph);g.current=['c']
    scope={'protocol_binding':m.PROTOCOL_SHA,'input_type':'PythonSourceText','output_type':'CandidateSourceText','authority':'NONE','native_verifier':'Refactory.Tester.tv_code'}
    cap=types.SimpleNamespace(operation='refactory.v104.retained_search',source=m.protocol()['generator_source'],scope=scope,program='p')
    g.machine=types.SimpleNamespace(mt=types.SimpleNamespace(live_ids=lambda log:['c']),log=[],flash_live_ids=lambda:{'c'},descriptor=lambda key:cap,get=lambda key:{'generator':{}})
    with pytest.raises(ValueError,match='generator'):g.signatures()

def test_raw_source_hash_preserves_crlf_bytes(tmp_path):
    m=module();path=tmp_path/'source.py';raw=b'def f():\r\n    return 1\r\n';path.write_bytes(raw)
    assert m.read_source(path).encode()==raw
