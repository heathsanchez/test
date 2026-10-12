#!/usr/bin/env python3
"""Independently decode export-local names and the seven native Nucleus traces.
Reject only the universal Nat.succ/free-variable identification proposal.
Never reinterpret a pinned UNKNOWN as theorem refutation or an Arena ACCEPT.
"""
from __future__ import annotations
import argparse,hashlib,io,json,re,tarfile,zipfile
from copy import deepcopy
from pathlib import Path

ARENA='f6cd590db7f6fb92b8d1b3ca87231d4b0f521f085d73f93abd005f5caaff86d2'
TRACE='3282352b1ae86dd5e2e8cadd15009bc2e845a52ef54f6c51d34938139769e990'
SIX=('init-prelude','perf/grind-ring-5','perf/magma-list-pair-n7',
     'perf/magma-list-pair-n21','perf/magma-list-deep-n21',
     'perf/magma-list-deep-n36')
H='^NUCLEUS_STAGE16_WHNF:left=Proven .*?head: Const \\{ name: NameId\\((\\d+)\\),'

def valid(cond,reason):
    if not cond:raise ValueError(reason)

def exact(path,sha):
    b=Path(path).read_bytes()
    valid(hashlib.sha256(b).hexdigest()==sha,'MUTATED_SOURCE_ARCHIVE:'+str(path))
    return b

def names_of(source):
    rows=[json.loads(x) for x in source.splitlines()]
    meta=rows[0]['meta']['lean']
    valid(meta['version']=='4.34.1' and meta['githash']=='5045d0056413266e57c625dcd7c365b10e377c52',
          'UNPINNED_LEAN_EXPORT')
    names={0:''}
    for row in rows[1:]:
        if 'in' not in row or ('str' not in row and 'num' not in row):continue
        obj=row['str'] if 'str' in row else row['num']
        valid(obj['pre'] in names and row['in'] not in names,'INVALID_EXPORT_NAME_GRAPH')
        name=names[obj['pre']]
        child=obj['str'] if 'str' in row else str(obj['i'])
        names[row['in']]=name+('.' if name else '')+child
    return names

def inspect(row,source):
    valid(row['verdict']==2,'NOT_NATIVE_UNKNOWN:'+row['case'])
    valid(hashlib.sha256(source).hexdigest()==row['sha256'],
          'SOURCE_DIGEST_MISMATCH:'+row['case'])
    names=names_of(source)
    o=row['observations']
    for name in ('NUCLEUS_STAGE16_WHNF:','NUCLEUS_STAGE16_CONVERSION_OUTCOME:',
                 'NUCLEUS_STAGE16_SOURCE_CONTEXT:','NUCLEUS_STAGE16_TYPED_OPERAND:'):
        valid(len(o.get(name,[]))>=2,'MISSING_TYPED_OBSERVATIONS:'+row['case'])
    seen=[]
    for i in (0,1):
        lhs=o['NUCLEUS_STAGE16_WHNF:'][i]
        m=re.search(H,lhs)
        valid(m is not None and 'right=Proven { value: Neutral(Neutral { head: Free(FreeId(0)), spine: [] })' in lhs,
              'NOT_CONST_SUCC_VS_FREE0:'+row['case'])
        index=int(m.group(1))
        valid(names.get(index)=='Nat.succ',
              'UNSUPPORTED_EXPORTED_CONSTANT:'+row['case']+':'+str(names.get(index)))
        conv=o['NUCLEUS_STAGE16_CONVERSION_OUTCOME:'][i]
        valid('Refuted { obstruction: ObstructionId("distinct-neutral-heads") }' in conv
              and 'expanded_result=Refuted' in conv
              and 'guarded_fallback_result=Refuted' in conv,
              'NOT_SOURCE_BOUND_RIGID_SEPARATOR:'+row['case'])
        ctx=o['NUCLEUS_STAGE16_SOURCE_CONTEXT:'][i]
        valid('right_syntax=Some(BVar(' in ctx,'UNSUPPORTED_SOURCE_ARGUMENT:'+row['case'])
        seen.append({'ordinal':i,'local_id':index,'decoded_name':names[index],
                     'opposite_head':'FreeId(0)','scope':'source-typed candidate premise'})
    valid('left_syntax=Some(BVar(1)):right_syntax=Some(BVar(1))'
           in o['NUCLEUS_STAGE16_SOURCE_CONTEXT:'][1],
          'MISSING_CAPTURED_ENVIRONMENT_SEPARATOR:'+row['case'])
    return {'case':row['case'],'source_sha256':row['sha256'],
            'verdict':'UNKNOWN','attempted_arguments':seen,
            'same_ast_different_capture':True}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--arena-zip',required=True)
    p.add_argument('--trace-zip',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    arena=exact(a.arena_zip,ARENA)
    trace=exact(a.trace_zip,TRACE)
    with zipfile.ZipFile(io.BytesIO(trace)) as z:
        seven=json.loads(z.read('seven.json'))
        report=json.loads(z.read('report.json'))
    valid(len(seven)==7 and report['verdict']==2,'DIAGNOSTIC_SET_MISMATCH')
    by={r['case']:r for r in seven}
    valid(set(by)==set(SIX)|{'perf/fueled-chain'},'SEVEN_CASES_CHANGED')
    with zipfile.ZipFile(io.BytesIO(arena)) as z:
        with tarfile.open(fileobj=io.BytesIO(z.read('lean-arena-tests.tar.gz')),mode='r:gz') as tar:
            source={name:tar.extractfile('good/'+name+'.ndjson').read() for name in SIX}
    checks=[inspect(by[name],source[name]) for name in SIX]
    f=by['perf/fueled-chain']
    valid(f['verdict']==2 and 'value: Lam {' in
          f['observations']['NUCLEUS_STAGE16_WHNF:'][0],
          'FUELED_NOT_DISTINCT_LAMBDA_SHAPE')
    mutations={}
    for name in ('wrong_head','wrong_free','changed_source'):
        row=deepcopy(by['init-prelude'])
        if name=='wrong_head':
            row['observations']['NUCLEUS_STAGE16_WHNF:'][0]=row['observations']['NUCLEUS_STAGE16_WHNF:'][0].replace('NameId(3)','NameId(999999)',1)
        if name=='wrong_free':
            row['observations']['NUCLEUS_STAGE16_WHNF:'][0]=row['observations']['NUCLEUS_STAGE16_WHNF:'][0].replace('FreeId(0)','FreeId(999)',1)
        if name=='changed_source':row['sha256']='0'*64
        try:inspect(row,source['init-prelude'])
        except ValueError:mutations[name]='REJECTED'
        else:raise AssertionError('SCOPE_FORGERY_PASSED:'+name)
    receipt={
      'status':'PASS_SOURCE_BOUND_STAGE16_RIGID_NEUTRAL_NO_GO',
      'arena_artifact':11272848230,'arena_archive_sha256':ARENA,
      'arena_source_commit':'b1d6e91d6de351f9bcf21e6b039f4d51d6b9bb42',
      'stage16_artifact':11724049727,'stage16_archive_sha256':TRACE,
      'stage16_source_commit':'ad207417730ac2ec1264f630872be34345127b41',
      'checked_six_case_pairs':12,'cases':checks,'mutation_controls':mutations,
      'fueled_chain':'separate_lambda_lambda_shape',
      'complete_nucleus_accepts_gained':0,
      'inference':'Universally identifying the observed Nat.succ neutral with an unrelated free neutral is invalid. The failed strict field-application route cannot justify acceptance; other kernel-valid routes remain UNKNOWN.'
    }
    dest=Path(a.output);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(receipt,sort_keys=True,indent=2)+'\\n')
    print(json.dumps({k:receipt[k] for k in ('status','checked_six_case_pairs','complete_nucleus_accepts_gained','mutation_controls')},sort_keys=True))

if __name__=='__main__':main()
