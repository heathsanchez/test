#!/usr/bin/env python3
"""Source-pinned experiments; incomplete checks never qualify as speed wins."""
import argparse
import difflib
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import shutil
import statistics
import subprocess
import tarfile
import time

BASE='a2578e77079719ff2064f910bd82fd01d8e120b6'
INPUT_SHA='22c5de83469408950005589a3bc5ef5157c65549b5a802f85d567c29151306a6'
FLAGS=('RELEVANCE','CONTEXT_BINDER','TYPED_LINEAGE','SUBSTITUTION_RECLOSURE','TYPED_VALUE_NORMALIZATION','PROJECTION_CONTEXT','PROJECTION_CROSSFRAME_512','TYPED_RECEIVER','SOURCE_PAIR_DEPTH8','POLYMORPHIC_PROP_IRREL','PROP_SINGLETON_2P1F','EXPECTED_LAMBDA','FORMED_PROP_DOMAIN_RETRY','TYPED_DATA_CONGRUENCE','TYPED_PROJECTION_SPINE','REPLAY_PROJECTION_MAJOR','REPLAY_NEUTRAL_PROJECTION')
EXPECTED_UNKNOWN={'bugs/eta-ctor-alias','perf/fueled-chain','perf/grind-ring-5','perf/magma-list-deep-n21','perf/magma-list-deep-n36','perf/magma-list-pair-n7','perf/magma-string-n4','perf/magma-string-pair-n9'}

def validate_baseline(rows,expected_count=208,expected_unknown=None):
    expected_unknown=EXPECTED_UNKNOWN if expected_unknown is None else expected_unknown
    if len(rows)!=expected_count or len({r['case'] for r in rows})!=expected_count:
        raise ValueError('missing or duplicate baseline cases')
    if any(r['expected'] not in (0,1) or r['rc'] not in (r['expected'],2) for r in rows):
        raise ValueError('wrong baseline verdict or execution error')
    if {r['case'] for r in rows if r['rc']==2}!=expected_unknown:
        raise ValueError('baseline UNKNOWN membership changed')

def run_group(cmd,timeout,**kwargs):
    capture=kwargs.pop('capture_output',False)
    if capture:kwargs.update(stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    p=subprocess.Popen(cmd,start_new_session=True,**kwargs)
    try:
        stdout,stderr=p.communicate(timeout=timeout)
        return subprocess.CompletedProcess(cmd,p.returncode,stdout,stderr)
    except subprocess.TimeoutExpired:
        try:os.killpg(p.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        stdout,stderr=p.communicate()
        return subprocess.CompletedProcess(cmd,124,stdout,stderr)

SUMMARY=r'test result: (?:ok|FAILED)\. (\d+) passed; (\d+) failed; (\d+) ignored; (\d+) measured; (\d+) filtered out;'
def native_target_valid(rc,stdout):
    matches=re.findall(SUMMARY,stdout)
    running=re.findall(r'^running (\d+) tests?$',stdout,re.M)
    if len(matches)!=1 or len(running)!=1:return False
    passed,failed,ignored,measured,filtered=map(int,matches[0])
    if int(running[0])!=passed+failed+ignored+measured:return False
    if len(failures(stdout))!=failed:return False
    return (rc==0 and failed==0) or (rc==101 and failed>0)

def native_suite(kernel,env,out):
    cmd=['cargo','test','--release','--locked','--manifest-path',str(kernel/'Cargo.toml'),'--no-run','--message-format=json']
    built=run_group(cmd,timeout=600,env=env,capture_output=True)
    (out/'native-build.log').write_bytes(built.stdout+built.stderr)
    if built.returncode:return dict(compiled=False,targets={})
    targets={}
    for line in built.stdout.decode(errors='replace').splitlines():
        try:d=json.loads(line)
        except json.JSONDecodeError:continue
        if d.get('reason')=='compiler-artifact' and d.get('executable') and d.get('profile',{}).get('test'):
            key=d['target']['name']+'|'+','.join(d['target']['kind'])
            targets[key]=d['executable']
    if not targets:return dict(compiled=False,targets={})
    report={}
    for key,exe in sorted(targets.items()):
        r=run_group([exe,'--include-ignored'],timeout=900,env=env,capture_output=True)
        raw=(r.stdout+r.stderr).decode(errors='replace')
        (out/('native-'+key.replace('|','-')+'.log')).write_text(raw)
        counts=re.findall(SUMMARY,raw)
        report[key]=dict(rc=r.returncode,complete=native_target_valid(r.returncode,raw),failures=failures(raw),counts=list(map(int,counts[0])) if len(counts)==1 else None)
    # Rustdoc is not a test executable produced by --no-run; account for it separately.
    doc=run_group(['cargo','test','--release','--locked','--manifest-path',str(kernel/'Cargo.toml'),'--doc','--','--include-ignored'],timeout=600,env=env,capture_output=True)
    raw=(doc.stdout+doc.stderr).decode(errors='replace');(out/'native-rustdoc.log').write_text(raw)
    counts=re.findall(SUMMARY,raw)
    report['rustdoc']=dict(rc=doc.returncode,complete=native_target_valid(doc.returncode,raw),failures=failures(raw),counts=list(map(int,counts[0])) if len(counts)==1 else None)
    result=dict(compiled=True,targets=report)
    write_json(out/'native-targets.json',result)
    return result

def native_reports_match(candidate,reference):
    if not candidate['compiled'] or not reference['compiled']:return False
    a=candidate['targets'];b=reference['targets']
    if set(a)!=set(b):return False
    for key in a:
        x,y=a[key],b[key]
        if not x['complete'] or not y['complete'] or x['rc']!=y['rc'] or x['failures']!=y['failures']:return False
        if sum(x['counts'][:4])<sum(y['counts'][:4]):return False
    return True

def geometric(xs):
    return math.exp(sum(math.log(x) for x in xs)/len(xs))

def qualifies(row):
    a=row.get('instructions',[]);b=row.get('reference_instructions',[])
    return bool(row.get('parity') and row.get('native_parity') and row.get('mathlib_rc')==0
        and row.get('reference_mathlib_rc')==0 and row.get('input_sha')==INPUT_SHA and len(a)==len(b)==3
        and all(isinstance(x,(int,float)) and x>0 for x in a+b)
        and all(x<y for x,y in zip(a,b)) and geometric([x/y for x,y in zip(a,b)])<=.98)

def select_winner(rows):
    good=[r for r in rows if qualifies(r)]
    return min(good,key=lambda r:geometric(r['instructions'])) if good else None

def write_json(path,value):
    Path(path).write_text(json.dumps(value,indent=2,sort_keys=True)+'\n')

def digest(path):
    with open(path,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def run_env():
    e={k:v for k,v in os.environ.items() if not k.startswith('NUCLEUS_')}
    e.update({'NUCLEUS_EXPERIMENTAL_'+f:'1' for f in FLAGS})
    return e

def replace_once(text,old,new):
    assert text.count(old)==1,(old[:90],text.count(old))
    return text.replace(old,new,1)

def hybrid_table(text):
    start=text.index('#[derive(Clone, Debug)]\npub struct IdTable')
    return text[:start]+'''#[derive(Clone, Debug)]
pub struct IdTable<I, T> {
    dense: Vec<Option<T>>,
    sparse: HashMap<u64, T>,
    count: usize,
    marker: PhantomData<fn(I) -> I>,
}
impl<I,T> Default for IdTable<I,T> {
    fn default()->Self {Self{dense:Vec::new(),sparse:HashMap::new(),count:0,marker:PhantomData}}
}
impl<I:TableId,T> IdTable<I,T> {
    pub fn insert(&mut self,id:I,value:T)->Result<(),DuplicateId>{
        let raw=id.raw();
        if self.get(id).is_some(){return Err(DuplicateId{kind:I::KIND,id:raw});}
        let idx=usize::try_from(raw).ok();
        // Sparse hostile IDs never force an allocation proportional to their numeric value.
        if let Some(i)=idx.filter(|&i|i<=self.dense.len().saturating_add(4096)
            && i<=self.count.saturating_mul(2).saturating_add(4096)) {
            if i>=self.dense.len(){self.dense.resize_with(i+1,||None);}
            self.dense[i]=Some(value);
        }else{self.sparse.insert(raw,value);}
        self.count+=1;Ok(())
    }
    pub fn get(&self,id:I)->Option<&T>{
        let raw=id.raw();
        usize::try_from(raw).ok().and_then(|i|self.dense.get(i)).and_then(Option::as_ref)
            .or_else(||self.sparse.get(&raw))
    }
    pub fn contains(&self,id:I)->bool{self.get(id).is_some()}
    pub fn len(&self)->usize{self.count}
    pub fn is_empty(&self)->bool{self.count==0}
    pub fn values(&self)->impl Iterator<Item=&T>{
        self.dense.iter().filter_map(Option::as_ref).chain(self.sparse.values())
    }
    pub fn iter_raw(&self)->impl Iterator<Item=(u64,&T)>{
        self.dense.iter().enumerate().filter_map(|(i,v)|v.as_ref().map(|v|(i as u64,v)))
            .chain(self.sparse.iter().map(|(i,v)|(*i,v)))
    }
}
'''

TABLE_TEST='''
#[test]
fn mixed_dense_holes_extreme_sparse_ids_match_reference_after_clone(){
    use std::collections::HashMap;
    let mut t=IdTable::<ExprId,u64>::default();let mut reference=HashMap::new();
    let mut ids=vec![u64::MAX,1<<40,8192,2,0,1,4095,4096];
    ids.extend((0..10000).rev());
    for id in ids {
        let old=reference.get(&id).copied();let r=t.insert(ExprId(id),id^123);
        assert_eq!(r.is_err(),old.is_some());
        reference.entry(id).or_insert(id^123);
        assert_eq!(t.get(ExprId(id)).copied(),reference.get(&id).copied());
    }
    let c=t.clone();assert_eq!(c.len(),reference.len());
    assert_eq!(c.iter_raw().map(|(k,v)|(k,*v)).collect::<HashMap<_,_>>(),reference);
    assert_eq!(c.values().count(),reference.len());assert!(!c.is_empty());
    assert_eq!(c.get(ExprId(100_000_001)),None);
}
'''

def shared_facts(typecheck,checker):
    fields={'closed_spine_eligibility':'HashMap<ExprId, bool>',
        'source_support':'HashMap<ExprId, Vec<u64>>',
        'paired_source_support':'HashMap<(ExprId, ExprId), Vec<(u64, u64)>>'}
    declaration='''// Completed source-only analyses; no typing or evaluation authority is shared.
pub(crate) struct SharedSourceAnalysis<'a> {
    expressions: &'a IdTable<ExprId, Expr>,
    levels: &'a IdTable<LevelId, Level>,
'''+''.join(f'    {name}: Rc<RefCell<{ty}>>,\n' for name,ty in fields.items())+'''}
impl<'a> SharedSourceAnalysis<'a> {
    pub(crate) fn new(expressions:&'a IdTable<ExprId,Expr>,levels:&'a IdTable<LevelId,Level>)->Self {
        Self { expressions,levels,
'''+''.join(f'            {name}:Rc::new(RefCell::new(HashMap::new())),\n' for name in fields)+'''        }
    }
}
'''
    typecheck=replace_once(typecheck,"pub struct TypeChecker<'a> {",declaration+"\npub struct TypeChecker<'a> {")
    for name,ty in fields.items():
        typecheck=replace_once(typecheck,f'    {name}: RefCell<{ty}>,',f'    {name}: Rc<RefCell<{ty}>>,')
        typecheck=re.sub(r'('+name+r':\s*)RefCell::new\(HashMap::new\(\)\)',r'\1Rc::new(RefCell::new(HashMap::new()))',typecheck)
    method='''
    pub(crate) fn with_source_analysis(mut self,source:&SharedSourceAnalysis<'a>)->Self {
        assert!(std::ptr::eq(self.expressions,source.expressions));
        assert!(std::ptr::eq(self.levels,source.levels));
'''+''.join(f'        self.{name}=source.{name}.clone();\n' for name in fields)+'''        self
    }
'''
    typecheck=replace_once(typecheck,"impl<'a> TypeChecker<'a> {","impl<'a> TypeChecker<'a> {"+method)
    a=checker.index('fn check_export_with_policy(');b=checker.index('\nfn recursor_claims_external_constructor',a)
    section=checker[a:b]
    section=replace_once(section,'    let mut environment = Environment::empty();',
        '    let source_analysis = crate::typecheck::SharedSourceAnalysis::new(&export.exprs,&export.levels);\n    let mut environment = Environment::empty();')
    assert section.count('.with_delta_policy(delta_policy);')>=4
    section=section.replace('.with_delta_policy(delta_policy);','.with_delta_policy(delta_policy).with_source_analysis(&source_analysis);')
    checker=checker[:a]+section+checker[b:]
    typecheck+='''
#[cfg(test)]
mod shared_source_analysis_regression {
    use super::*;
    #[test]
    fn completed_syntax_support_reuses_across_environments_without_typing_authority(){
        let mut es=IdTable::default();let mut ls=IdTable::default();
        ls.insert(LevelId(0),Level::Zero).unwrap();
        es.insert(ExprId(0),Expr::BVar(3)).unwrap();
        for i in 1..12 {es.insert(ExprId(i),Expr::App{fun:ExprId(i-1),arg:ExprId(0)}).unwrap();}
        let shared=SharedSourceAnalysis::new(&es,&ls);
        let e1=Environment::empty();let e2=Environment::empty();
        let c1=TypeChecker::new(&es,&ls,&e1).with_source_analysis(&shared);
        let c2=TypeChecker::new(&es,&ls,&e2).with_source_analysis(&shared);
        let mut enough=512;assert_eq!(c1.complete_source_support(ExprId(11),&mut enough),Some(vec![3]));
        let mut tiny=2;assert_eq!(c2.complete_source_support(ExprId(11),&mut tiny),Some(vec![3]));
        // A free source variable remains untypable in the empty checked context.
        assert!(!c2.infer(ExprId(0),64).is_proven());
    }
    #[test]
    #[should_panic]
    fn different_source_tables_cannot_share_analysis(){
        let a=IdTable::default();let b=IdTable::default();let ls=IdTable::default();
        let shared=SharedSourceAnalysis::new(&a,&ls);let env=Environment::empty();
        let _=TypeChecker::new(&b,&ls,&env).with_source_analysis(&shared);
    }
}
'''
    return typecheck,checker

def materialize(repo,out,table=False,facts=False):
    out.mkdir(parents=True,exist_ok=True)
    archive=subprocess.check_output(['git','archive',BASE,'metatron-kernel'],cwd=repo)
    import io
    with tarfile.open(fileobj=io.BytesIO(archive)) as tf:tf.extractall(out,filter='data')
    kernel=out/'metatron-kernel';original={}
    for p in ('src/id.rs','src/typecheck.rs','src/checker.rs'):
        original[p]=(kernel/p).read_text()
    if table:(kernel/'src/id.rs').write_text(hybrid_table(original['src/id.rs']))
    if facts:
        t,c=shared_facts(original['src/typecheck.rs'],original['src/checker.rs'])
        (kernel/'src/typecheck.rs').write_text(t);(kernel/'src/checker.rs').write_text(c)
    with (kernel/'tests/id_table.rs').open('a') as f:f.write(TABLE_TEST)
    patch=''
    for p,old in original.items():
        patch+=''.join(difflib.unified_diff(old.splitlines(True),(kernel/p).read_text().splitlines(True),fromfile='a/metatron-kernel/'+p,tofile='b/metatron-kernel/'+p))
    (out/'source.patch').write_text(patch)
    return kernel

def build(kernel,out,profile='standard'):
    env=dict(os.environ)
    env['CARGO_TARGET_DIR']=str(out/'target')
    if profile!='standard':env['RUSTFLAGS']='-C target-cpu=native'
    if profile=='native-fat':env['CARGO_PROFILE_RELEASE_LTO']='fat'
    cmd=['cargo','build','--release','--locked','--manifest-path',str(kernel/'Cargo.toml')]
    r=subprocess.run(cmd,capture_output=True,env=env,timeout=600)
    (out/'build.log').write_bytes(r.stdout+r.stderr)
    if r.returncode:return None,env
    binary=out/'nucleus';shutil.copy2(out/'target/release/metatron-kernel',binary)
    return binary,env

def replay(binary,manifest,root,env,out):
    rows=[]
    for old in manifest:
        p=root/'inputs'/old['relative_path'];assert digest(p)==old['sha256']
        with p.open('rb') as f:
            r=run_group([str(binary)],stdin=f,capture_output=True,env=env,timeout=240);rc=r.returncode;tail=r.stderr[-800:].decode(errors='replace')
        rows.append(dict(case=old['case'],expected=old['expected'],rc=rc,sha256=old['sha256'],terminal=tail))
        write_json(out,rows)
    return rows

def failures(raw):
    return sorted(set(re.findall(r'^test (.+?) \.\.\. FAILED$',raw,re.M)))

def measure(binary,source,env,directory,timeout=1800,perf=False):
    directory.mkdir(parents=True,exist_ok=True)
    cmd=['/usr/bin/time','-f','wall=%e\nuser=%U\nsystem=%S\nrss_kb=%M','-o',str(directory/'time.txt'),str(binary)]
    if perf:cmd=['perf','stat','-x,','-e','instructions','-o',str(directory/'perf.csv'),'--']+cmd
    start=time.monotonic()
    with open(source,'rb') as src,(directory/'stdout').open('wb') as stdout,(directory/'stderr').open('wb') as stderr:
        r=run_group(cmd,stdin=src,stdout=stdout,stderr=stderr,env=env,timeout=timeout);rc=r.returncode
    row=dict(rc=rc,wall_observed=time.monotonic()-start)
    if (directory/'time.txt').exists():
        for line in (directory/'time.txt').read_text().splitlines():
            if '=' in line:
                k,v=line.split('=',1)
                try:row[k]=float(v)
                except ValueError:pass
    if perf and (directory/'perf.csv').exists():
        for line in (directory/'perf.csv').read_text().splitlines():
            bits=line.split(',')
            if len(bits)>2 and bits[2]=='instructions':
                try:row['instructions']=int(bits[0])
                except ValueError:pass
    write_json(directory/'result.json',row)
    return row

def probe_perf(out):
    if not shutil.which('perf'):return False
    r=subprocess.run(['perf','stat','-x,','-e','instructions','--','true'],capture_output=True)
    (out/'perf-probe.txt').write_bytes(r.stdout+r.stderr)
    return r.returncode==0

def corpus(args):
    repo=Path(args.repo).resolve();out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)
    root=Path(args.inputs).resolve();manifest=json.loads((root/'inputs-manifest.json').read_text());assert len(manifest)==208
    env=run_env();write_json(out/'configuration.json',{k:v for k,v in env.items() if k.startswith('NUCLEUS_')})
    write_json(out/'provenance.json',dict(base=BASE,harness=os.environ.get('GITHUB_SHA'),rustc=subprocess.check_output(['rustc','--version']).decode(),uname=subprocess.check_output(['uname','-a']).decode(),input_manifest_sha=digest(root/'inputs-manifest.json')))
    state={};baseline=None;native_baseline=None
    for name,table,facts in [('baseline',False,False),('dense',True,False),('facts',False,True),('dense-facts',True,True)]:
        arm=out/name;kernel=materialize(repo,arm,table,facts)
        binary,build_env=build(kernel,arm)
        info=dict(name=name,built=binary is not None,profile='standard',source_patch_sha=digest(arm/'source.patch'))
        if binary is None:state[name]=info;write_json(out/'state.json',state);continue
        native_env=build_env|env
        nr=native_suite(kernel,native_env,arm)
        info.update(native_targets=nr,binary_sha=digest(binary))
        if name=='baseline':native_baseline=nr
        info['native_parity']=native_reports_match(nr,native_baseline)
        rows=replay(binary,manifest,root,env,arm/'verdicts.json')
        if name=='baseline':validate_baseline(rows);baseline=rows
        diffs=[dict(case=a['case'],baseline=a['rc'],candidate=b['rc']) for a,b in zip(baseline,rows) if a['rc']!=b['rc']]
        info.update(parity=not diffs,differences=diffs,counts={str(k):sum(r['rc']==k for r in rows) for k in (0,1,2)})
        if name=='baseline':assert info['counts']=={'0':121,'1':79,'2':8},info
        state[name]=info;write_json(out/'state.json',state)
        print('ARM '+json.dumps(info),flush=True)
        shutil.rmtree(arm/'target',ignore_errors=True)
    # The benchmark cohort is fixed by baseline acceptance and input size, never candidate outcomes.
    accepted={r['case'] for r in baseline if r['rc']==0}
    cohort=sorted([r for r in manifest if r['case'] in accepted],key=lambda r: (root/'inputs'/r['relative_path']).stat().st_size,reverse=True)[:8]
    write_json(out/'cohort.json',cohort)
    perf=probe_perf(out);measurements=[]
    viable=[n for n,s in state.items() if s.get('parity') and s.get('native_parity')]
    for roundno in range(3):
        order=viable if roundno%2==0 else list(reversed(viable))
        for name in order:
            for old in cohort:
                tag=old['case'].replace('/','__')
                result=measure(out/name/'nucleus',root/'inputs'/old['relative_path'],env,out/name/f'cohort-{roundno}-{tag}',timeout=240,perf=perf)
                measurements.append(dict(arm=name,round=roundno,case=old['case'],**result))
        write_json(out/'cohort-measurements.json',measurements)
    print('CORPUS_TOURNAMENT_COMPLETE '+json.dumps({'arms':state,'perf_available':perf}),flush=True)

def mathlib(args):
    out=Path(args.out).resolve();out.mkdir(parents=True,exist_ok=True)
    source=Path(args.mathlib).resolve();assert digest(source)==INPUT_SHA
    previous=Path(args.previous).resolve();state=json.loads((previous/'state.json').read_text());env=run_env();perf=probe_perf(out)
    measurements=[];eligible=[n for n,s in state.items() if s.get('parity') and s.get('native_parity')]
    for roundno in range(3):
        for name in eligible if roundno%2==0 else list(reversed(eligible)):
            if roundno and (any(r['rc']!=0 for r in measurements if r['arm']==name)
                or any(r['rc']!=0 for r in measurements if r['arm']=='baseline')):continue
            r=measure(previous/name/'nucleus',source,env,out/name/f'round-{roundno}',timeout=1800,perf=perf)
            measurements.append(dict(arm=name,round=roundno,**r));write_json(out/'measurements.json',measurements)
            print('MATHLIB '+json.dumps(measurements[-1]),flush=True)
    baseline=[r for r in measurements if r['arm']=='baseline'];rows=[]
    for name in eligible:
        runs=[r for r in measurements if r['arm']==name]
        row=state[name]|dict(input_sha=INPUT_SHA,mathlib_rc=0 if all(r['rc']==0 for r in runs) else next(r['rc'] for r in runs if r['rc']!=0),reference_mathlib_rc=0 if all(r['rc']==0 for r in baseline) else next(r['rc'] for r in baseline if r['rc']!=0),instructions=[r['instructions'] for r in runs if 'instructions'in r],reference_instructions=[r['instructions'] for r in baseline if 'instructions'in r],full_runs=runs)
        row['qualified_instruction_win']=qualifies(row);rows.append(row)
    write_json(out/'summary.json',dict(arms=rows,winner=select_winner(rows),perf_available=perf))
    print('FULL_MATHLIB_TOURNAMENT '+json.dumps({'winner':select_winner(rows),'complete_accepts':[r['name'] for r in rows if r['mathlib_rc']==0],'perf_available':perf}),flush=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['corpus','mathlib']);p.add_argument('--repo',default='.');p.add_argument('--out',required=True);p.add_argument('--inputs');p.add_argument('--mathlib');p.add_argument('--previous');args=p.parse_args()
    (corpus if args.phase=='corpus' else mathlib)(args)

if __name__=='__main__':main()
