"""Post-hoc causal efficiency diagnostic; no future source or training is added."""
import json,time,zipfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import followup_v4 as f
m=f.m

def main():
    start=time.perf_counter();out=m.WORK/'cost_ablation_run_v5';out.mkdir(exist_ok=False);z=zipfile.ZipFile(m.WORK/'refactory_data_sealed.zip');native=m.setup(out,m.WORK/'external-refactory',z)
    history=[r for r in json.loads((m.WORK/'pilot_run_v3/rows.json').read_text()) if r['split']=='train' and r['arm']=='D']
    g=m.Graph(out/'D-graph');f.restore(g,native,z,history);task='data/question_5/code/wrong/wrong_5_001.py'
    before=m.episode(native,z,task,'D',g.signatures(),'eval')
    old=next(r for r in json.loads((m.WORK/'pilot_run_v3/rows.json').read_text()) if r['arm']=='D' and r['split']=='eval' and r['status']=='WARRANTED_BOUNDED_REPAIR')
    unrelated=f.exact_program(g,native,old,1)
    g.machine.append('revoke',{'target':unrelated,'reason':'cost ablation actual unrelated executable'});g.machine.flush()
    irrelevant=m.episode(native,z,task,'D',g.signatures(),'eval')
    removed=sorted({d for i in g.current for d in g.machine.descriptor(i).dependencies})
    for i in removed:g.machine.append('revoke',{'target':i,'reason':'cost ablation acquired priority support'})
    g.machine.flush();without=m.episode(native,z,task,'D',g.signatures(),'eval')
    f.restore(g,native,z,history);restored=m.episode(native,z,task,'D',g.signatures(),'eval')
    rows={'before':before,'irrelevant':irrelevant,'without':without,'restored':restored}
    if not all(r['status']=='WARRANTED_BOUNDED_REPAIR' for r in rows.values()):raise ValueError('protected success changed')
    if not (before['native_calls']==irrelevant['native_calls']==restored['native_calls']==3 and without['native_calls']==5):raise ValueError('two-call saving not reproduced')
    if without['signatures'] or not restored['signatures']:raise ValueError('priority withdrawal/restoration failed')
    result={'status':'WARRANTED_BOUNDED_TWO_NATIVE_CALL_SEARCH_SAVING','posthoc':True,'source':task,'new_behavioral_capability':False,'same_outcome':True,'baseline_history_and_ledger_share_saving':True,'removed_ancestors':removed,'removed_unrelated_executable':unrelated,'rows':rows,'native_calls':native.number,'elapsed_seconds':time.perf_counter()-start,'all_in_positive_economics':False}
    m.write(out/'result.json',result)
if __name__=='__main__':
    try:main()
    except Exception as e:m.write(m.WORK/'cost_ablation_run_v5/STOP.json',{'status':'UNKNOWN','reason':str(e)});raise
