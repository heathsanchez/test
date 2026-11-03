#!/usr/bin/env python3
"""Paired import-cost tournament; UNKNOWN checking is never completion."""
import argparse,difflib,json,os,shutil,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'nucleus-reuse-20261104'))
import tournament as t
ROOT=Path(__file__).resolve().parent
original_materialize=t.materialize

def materialize(repo,out,table=False,facts=False):
    k=original_materialize(repo,out,table=table,facts=False)
    if facts:
        import re
        files=list((k/'src').glob('*.rs'))
        old={p:p.read_text() for p in files}
        pattern=r'std::env::var_os\(\s*"(NUCLEUS_[A-Z0-9_]+)"\s*\)\.is_(some|none)\(\)'
        names=sorted({m.group(1) for s in old.values() for m in re.finditer(pattern,s)})
        indices={key:i for i,key in enumerate(names)}
        def replacement(m):
            expr=f'crate::settings::enabled({indices[m.group(1)]},"{m.group(1)}")'
            return expr if m.group(2)=='some' else '!'+expr
        for p,s in old.items():p.write_text(re.sub(pattern,replacement,s))
        lib=k/'src/lib.rs';lib.write_text('mod settings;\n'+lib.read_text())
        checker=k/'src/checker.rs';s=checker.read_text()
        s=t.replace_once(s,') -> Verdict {\n    if !quotient_source_ownership_is_well_ordered(&export)',') -> Verdict {\n    let _settings = crate::settings::SnapshotGuard::enter();\n    if !quotient_source_ownership_is_well_ordered(&export)')
        checker.write_text(s)
        module=(ROOT/'settings.rs').read_text()+'\nconst KEYS:&[&str]=&'+json.dumps(names)+';\n'
        (k/'src/settings.rs').write_text(module)
        with (out/'source.patch').open('a') as f:
            for p,s in old.items():f.write(''.join(difflib.unified_diff(s.splitlines(True),p.read_text().splitlines(True),fromfile='a/metatron-kernel/src/'+p.name,tofile='b/metatron-kernel/src/'+p.name)))
            f.write(''.join(difflib.unified_diff([],module.splitlines(True),fromfile='/dev/null',tofile='b/metatron-kernel/src/settings.rs')))
        t.write_json(out/'snapshot-keys.json',names)
    return k

t.materialize=materialize
OBSERVER='''
use std::io::{self,BufReader};use std::time::Instant;
use metatron_kernel::{parser,checker};
fn main(){std::thread::Builder::new().stack_size(64*1024*1024).spawn(run).unwrap().join().unwrap();}
fn run(){
 let t=Instant::now();let p=match parser::parse(BufReader::new(io::stdin().lock())){Ok(x)=>x,Err(e)=>{eprintln!("PARSE_ERROR {e}");std::process::exit(3)}};
 eprintln!("PHASE_PARSE_SECONDS {}",t.elapsed().as_secs_f64());
 let t=Instant::now();let e=match p.resolve(){Ok(x)=>x,Err(e)=>{eprintln!("RESOLVE_ERROR {e}");std::process::exit(3)}};
 eprintln!("PHASE_RESOLVE_SECONDS {}",t.elapsed().as_secs_f64());
 let t=Instant::now();let v=checker::check_export(e,checker::Limits::default());eprintln!("PHASE_CHECK_SECONDS {}",t.elapsed().as_secs_f64());std::process::exit(v.exit_code());
}
'''
def full(args):
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True);source=Path('/tmp/mathlib.ndjson');assert t.digest(source)==t.INPUT_SHA
    env=t.run_env();env['NUCLEUS_TRACE_DOWNSTREAM']='1';env['NUCLEUS_TRACE_IMPORT']='1'
    t.write_json(out/'provenance.json',dict(base=t.BASE,harness=os.environ.get('GITHUB_SHA'),input_sha=t.INPUT_SHA,configuration={k:v for k,v in env.items() if k.startswith('NUCLEUS_')},arms={'baseline':'original','dense':'dense','facts':'settings-snapshot','dense-facts':'dense+settings-snapshot'},qualification='IMPORT_AND_PARTIAL_CHECK_DIAGNOSTICS_ONLY'))
    arms={}
    for name,dense,fast in [('baseline',False,False),('dense',True,False),('facts',False,True),('dense-facts',True,True)]:
        arm=out/name;k=materialize(Path.cwd(),arm,dense,fast)
        ex=k/'examples/phase_observer.rs';ex.parent.mkdir(exist_ok=True);ex.write_text(OBSERVER)
        benv=dict(os.environ,CARGO_TARGET_DIR=str(arm/'target'))
        r=t.run_group(['cargo','build','--release','--locked','--manifest-path',str(k/'Cargo.toml'),'--example','phase_observer'],env=benv,capture_output=True,timeout=600)
        (arm/'build.log').write_bytes(r.stdout+r.stderr)
        if r.returncode:raise RuntimeError('observer build failed: '+name)
        if fast:
            test=t.run_group(['cargo','test','--release','--locked','--manifest-path',str(k/'Cargo.toml'),'--lib','settings_snapshot_tests'],env=benv,capture_output=True,timeout=600)
            (arm/'settings-controls.log').write_bytes(test.stdout+test.stderr)
            if test.returncode:raise RuntimeError('settings snapshot controls failed: '+name)
        binary=arm/'observer';shutil.copy2(arm/'target/release/examples/phase_observer',binary);shutil.rmtree(arm/'target')
        arms[name]=binary
    perf=t.probe_perf(out);rows=[]
    for roundno,order in enumerate([['baseline','dense','facts','dense-facts'],['dense-facts','facts','dense','baseline'],['facts','baseline','dense-facts','dense']]):
        for name in order:
            dest=out/name/f'round-{roundno}'
            row=dict(arm=name,round=roundno,**t.measure(arms[name],source,env,dest,timeout=900,perf=perf))
            stderr=(dest/'stderr').read_text()
            for label in ['PARSE','RESOLVE','CHECK']:
                import re
                m=re.search('PHASE_'+label+r'_SECONDS ([0-9.]+)',stderr)
                if m:row[label.lower()]=float(m[1])
            row['same_unknown_boundary']=row['rc']==2 and "name=List.Perm.recOnSwap':stage=theorem.value:verdict=UNKNOWN:reason=application-function-type" in stderr
            row['complete_mathlib_accept']=row['rc']==0
            rows.append(row);t.write_json(out/'measurements.json',rows);print(json.dumps(row),flush=True)
            if row['rc'] not in (0,2) or 'resolve' not in row:raise RuntimeError('incomplete parse/resolve observation')
    baseline={r['round']:r for r in rows if r['arm']=='baseline'}
    summary={}
    for name in arms:
        rs=[r for r in rows if r['arm']==name]
        summary[name]=dict(import_ratio=t.geometric([(r['parse']+r['resolve'])/(baseline[r['round']]['parse']+baseline[r['round']]['resolve']) for r in rs]),partial_wall_ratio=t.geometric([r['wall_observed']/baseline[r['round']]['wall_observed'] for r in rs]),max_rss_kb=max(r['rss_kb'] for r in rs),same_boundary=all(r['same_unknown_boundary'] for r in rs),complete_accepts=sum(r['complete_mathlib_accept'] for r in rs))
    t.write_json(out/'summary.json',dict(arms=summary,perf_available=perf,qualified_mathlib_speed_winner=None,qualification='IMPORT_AND_PARTIAL_CHECK_DIAGNOSTICS_ONLY'))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['corpus','full']);p.add_argument('--out',required=True);p.add_argument('--inputs');p.add_argument('--repo',default='.');args=p.parse_args()
    if args.phase=='corpus':t.corpus(args)
    else:full(args)
