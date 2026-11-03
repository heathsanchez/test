"""Post-hoc acquisition-floor diagnosis on the FIRST exposed training program.

This never alters the pilot or opens a new task pool. Reuses original V98 rich
mutations and V100 family balancing, rather than creating a winning repair.
"""
import ast,copy,hashlib,json,os,sys,subprocess,time,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pilot

def original_base(source_repo):
    ns={'ast':ast,'copy':copy}
    p='experiments/METALOGIC_V98_RICH_K_PROTECTED_DYNAMIC_RANKING.py'
    raw=subprocess.check_output(['git','-C',str(source_repo),'show','426c54f7c774560e0fabe7213c5ef333b1327c71:'+p])
    tree=ast.parse(raw)
    defs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='rich_candidates' or isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in {'CMP','BIN','BOOL'} for t in n.targets)]
    exec(compile(ast.Module(body=defs,type_ignores=[]),p,'exec'),ns)
    ns['ORIGINAL_RICH']=ns['rich_candidates']
    q='experiments/METALOGIC_V100_BALANCED_K_CROSS_SOURCE_ORGANS.py'
    second=subprocess.check_output(['git','-C',str(source_repo),'show','426c54f7c774560e0fabe7213c5ef333b1327c71:'+q])
    f=[n for n in ast.parse(second).body if isinstance(n,ast.FunctionDef) and n.name=='balanced_rich_candidates']
    exec(compile(ast.Module(body=f,type_ignores=[]),q,'exec'),ns)
    return ns['balanced_rich_candidates'],{p:pilot.sha(raw),q:pilot.sha(second)}

def main():
    work=pilot.WORK;out=work/'posthoc_acquisition_diagnostic';out.mkdir(exist_ok=False)
    p=pilot.protocol();task=p['train'][0];q=task.split('/')[1]
    archive=zipfile.ZipFile(work/'refactory_data_sealed.zip');native=pilot.setup(out,work/'external-refactory',archive)
    source=archive.read(task).decode();base=native.verify(source,q,'COMMON-posthoc-original-baseline')
    original,root=pilot.generator();strong,pins=original_base(root)
    result={'status':'POSTHOC_CALIBRATION_RUNNING','source':task,'source_sha256':pilot.sha(source.encode()),
        'pilot_protocol_sha256':pilot.PROTOCOL_SHA,'original_source_pins':pins,'baseline':base,'arms':[],
        'boundary':'Exposed-source diagnosis only. No prospective G2/G3, new primitive, transfer or memory advantage claim.'}
    for cap in [32,320]:
        for name,programs in [('V104_CONSTRUCTOR_ONLY',[(repr((s,b)),text) for s,b,text in original.generate_candidates(root,source,cap=cap)]),
                              ('ORIGINAL_V100_V102_BASE',strong(source,cap))]:
            rows=[];best=base['passed'];solved=False
            for kind,program in programs:
                r=native.verify(program,q,name+'-posthoc-candidate')
                rows.append({'kind':kind,'program':program,'receipt':r})
                if r['status'] in ('PASS_NATIVE','FAIL_NATIVE'):best=max(best,r['passed'])
                if r['status']=='PASS_NATIVE':
                    confirm=native.verify(program,q,name+'-posthoc-confirmation')
                    solved=confirm['status']=='PASS_NATIVE' and confirm['cases']==r['cases']
                    if solved:break
            result['arms'].append({'method':name,'cap':cap,'tested':len(rows),'best_passed':best,'full_solution':solved,'rows':rows})
            pilot.write(out/'result.json',result)
            print(name,cap,'tested',len(rows),'best',best,'full',solved,flush=True)
        if any(a['full_solution'] for a in result['arms'] if a['cap']==cap):break
    result['status']='EXECUTED_POSTHOC_ACQUISITION_DIAGNOSIS';result['native_calls']=native.number
    pilot.write(out/'result.json',result)
if __name__=='__main__':main()
