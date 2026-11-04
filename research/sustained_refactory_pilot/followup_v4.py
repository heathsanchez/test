"""Three prospectively frozen futures and separately labeled native maintenance.

Uses real prior training only; never fits on a future's native outcome.
"""
from dataclasses import asdict
import copy,json,sys,time,zipfile,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pilot_v3_posthoc_repair as m


def refresh(row,native,archive):
    r=copy.deepcopy(row);source=archive.read(r['source']).decode()
    baseline=native.verify(source,r['question'],'D-followup-source-baseline')
    if baseline['cases']!=r['baseline']['cases']:raise ValueError('training baseline changed on requalification')
    r['baseline']=baseline
    for w in r['witnesses']:
        new=native.verify(w['program'],r['question'],'D-followup-source-witness')
        if new['cases']!=w['receipt']['cases']:raise ValueError('training witness changed on requalification')
        w['receipt']=new
    return r


def restore(graph,native,archive,history):
    for row in history:graph.add(refresh(row,native,archive),native)
    graph.reopen()


def exact_program(graph,native,row,version):
    from research.unified_consequence_runtime.developmental_machine import Capability
    program=row['winner']['program'];scope={'source':row['source'],'source_sha256':row['source_sha256'],'question':row['question'],'permission':'NONE'}
    a=native.verify(program,row['question'],'D-unrelated-program-qualification')
    b=native.verify(program,row['question'],'D-unrelated-program-confirmation')
    if a['status']!='PASS_NATIVE' or a['cases']!=b['cases']:raise ValueError('unrelated exact program not qualified')
    proof=graph.machine.put({'first':a,'fresh':b,'scope':scope});e=graph.machine.append('independent_exact_native_program',{'proof':proof,'version':version})
    p=graph.machine.put({'program':program,'scope':scope})
    c=Capability('refactory.exact_native_program',{'subject':scope,'method':'original Refactory Tester'},scope,proof,p,version,(e,),(e,),'INDEPENDENT_VERIFICATION')
    ident=graph.machine.append('executable_capability',asdict(c),(e,));graph.machine.flush();return ident


def invoke_exact(graph,native,ident):
    live=set(graph.machine.mt.live_ids(graph.machine.log))&graph.machine.flash_live_ids()
    if ident not in live:return {'status':'UNKNOWN_WITHDRAWN'}
    cap=graph.machine.descriptor(ident);p=graph.machine.get(cap.program)
    if cap.operation!='refactory.exact_native_program' or p['scope']!=cap.scope:raise ValueError('exact program scope changed')
    r=native.verify(p['program'],p['scope']['question'],'D-unrelated-program-invocation')
    if r['status']!='PASS_NATIVE':raise ValueError('unrelated exact native operation regressed')
    return r


def main():
    root=m.WORK;out=root/'followup_run_v4';out.mkdir(exist_ok=False);start=time.perf_counter()
    plan=json.loads((m.HERE/'followup_v4.json').read_text());archive=zipfile.ZipFile(root/'refactory_data_sealed.zip')
    history=[r for r in json.loads((root/'pilot_run_v3/rows.json').read_text()) if r['split']=='train' and r['arm']=='D']
    native=m.setup(out,root/'external-refactory',archive);graph=m.Graph(out/'D-graph');restore(graph,native,archive,history)
    sigs=graph.signatures();m.write(out/'initial-memory.json',{'signatures':sigs,'prior_source':'c4cc55d79a7ebc879491475276531959799d37cd','training_subjects':[r['source'] for r in history]})
    # First independent qualification of the previously unopened fifth objective.
    ref=archive.read('data/question_5/code/reference/reference.py').decode()
    q5=native.verify(ref,'question_5','COMMON-new-family-reference-control')
    bad=native.verify('def __missing__(): return None\n','question_5','COMMON-new-family-negative-control')
    m.write(out/'new-family-controls.json',{'reference':q5,'negative':bad})
    if q5['status']!='PASS_NATIVE' or bad['status']!='FAIL_NATIVE':raise ValueError('UNKNOWN_NEW_FAMILY_ADMISSION')
    ledger_priorities=m.selected(history)
    rows=[]
    for i,task in enumerate(plan['future_tasks']):
        for arm in m.arm_order(i):
            before=time.perf_counter()
            chosen=[] if arm=='A' else (graph.signatures() if arm=='D' else (ledger_priorities if arm=='C' else m.selected(history)))
            retrieve=time.perf_counter()-before
            row=m.episode(native,archive,task,arm,chosen,'eval');row['retrieval_seconds']=retrieve
            rows.append(row);m.write(out/'future-rows.json',rows)
            print('FUTURE',task,arm,row['status'],flush=True)
        paired={r['arm']:r for r in rows if r['source']==task}
        if paired['D']['status']=='WARRANTED_BOUNDED_REPAIR' and paired['A']['status']!='WARRANTED_BOUNDED_REPAIR':
            causal=m.causal_checks(graph,native,archive,task,paired['D']);m.write(out/(Path(task).stem+'-causal.json'),causal)
            if causal['status']!='WARRANTED_BOUNDED_CAUSAL_SEARCH_REUSE':raise ValueError('causal future gain not qualified')
        if native.number>1200 or time.perf_counter()-start>1200:raise ValueError('frozen followup budget exhausted')
    # Post-hoc engineering controls use already exposed programs; never training.
    exposed=json.loads((root/'pilot_run_v3/rows.json').read_text())
    unrelated=next(r for r in exposed if r['arm']=='D' and r['split']=='eval' and r['status']=='WARRANTED_BOUNDED_REPAIR')
    u=exact_program(graph,native,unrelated,1);u_before=invoke_exact(graph,native,u);before=graph.signatures()
    graph.machine.append('revoke',{'target':u,'reason':'actual unrelated native executable removal'});graph.machine.flush()
    if graph.signatures()!=before:raise ValueError('unrelated executable removal changed independent priority')
    u_removed=invoke_exact(graph,native,u)
    task=plan['future_tasks'][0];protected_before=next(r for r in rows if r['source']==task and r['arm']=='D')
    protected_irrelevant=m.episode(native,archive,task,'D',graph.signatures(),'eval')
    u=exact_program(graph,native,unrelated,2)
    ancestors=sorted({p for ident in graph.current for p in graph.machine.descriptor(ident).dependencies})
    for ident in ancestors:graph.machine.append('revoke',{'target':ident,'reason':'actual retained-priority ancestor withdrawal'})
    graph.machine.flush()
    if graph.signatures():raise ValueError('priority survived ancestor withdrawal')
    absent=m.episode(native,archive,task,'D',graph.signatures(),'eval');u_survives=invoke_exact(graph,native,u)
    restore(graph,native,archive,history)
    restored=m.episode(native,archive,task,'D',graph.signatures(),'eval')
    if graph.signatures()!=before or restored['status']!=protected_before['status'] or protected_irrelevant['status']!=protected_before['status']:
        raise ValueError('native priority restoration/noninterference failed')
    nodes={n.id:n for n in graph.machine.log};support=graph.machine.descriptor(graph.current[0]).dependencies[0];source_root=nodes[support].premises[0]
    graph.machine.append('revoke',{'target':source_root,'reason':'controlled source-assumption withdrawal'});graph.machine.flush()
    if graph.signatures():raise ValueError('changed source assumption retained dependent priority')
    u_assumption=invoke_exact(graph,native,u);restore(graph,native,archive,history)
    if graph.signatures()!=before:raise ValueError('source requalification failed')
    maintenance={'status':'PASS_BOUNDED_NATIVE_MAINTENANCE','prospective_learning_claim':False,'source_assumption_is_controlled':True,
        'priority_bundle_before':before,'removed_ancestors':ancestors,'unrelated_before':u_before,'unrelated_removed':u_removed,
        'unrelated_after_ancestor_withdrawal':u_survives,'unrelated_after_source_assumption_withdrawal':u_assumption,
        'source_root_withdrawn':source_root,'protected_before':protected_before,'protected_irrelevant_removal':protected_irrelevant,'protected_without_priority':absent,'protected_restored':restored}
    m.write(out/'maintenance.json',maintenance)
    summary={'status':'EXECUTED_FROZEN_THREE_FUTURES_AND_NATIVE_MAINTENANCE','plan':plan,
        'outcomes':[{k:r[k] for k in ['source','arm','status','native_calls']} for r in rows],
        'native_calls':native.number,'elapsed_seconds':time.perf_counter()-start,'model_calls':0,
        'scope':'Within-family and withheld objective-family transfer in original Refactory; not a second software domain or unrestricted G3.'}
    m.write(out/'summary.json',summary)

if __name__=='__main__':
    try:main()
    except Exception as e:
        m.write(m.WORK/'followup_run_v4/STOP.json',{'status':'STOPPED_UNKNOWN','exception':type(e).__name__,'reason':str(e)});raise
