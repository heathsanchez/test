"""Reconstruct the original pre-query metadata authority without querying tasks.

The original V45 curator and original independent metadata predicates are reused
from their exact pinned bytes. Reconstruction creates a new witness; it never
claims that a missing PRIOR_EXPOSURE.json existed at the historical freeze.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path,PurePosixPath
import re
import subprocess
import sys
import time

OLD_AUDITOR=Path('/workspace/qualification/native-namespace-v45-screening-audit-preparation/audit_retained_v45.py')
OLD_AUDITOR_SHA='54ccf0321316a02ac13d9f44982b365550eb1c2abdfee8d2249224b3bac70411'


def sha(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def fp(value):return sha(canonical(value).encode())


def require(value,message):
    if not value:raise ValueError(message)


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    result=importlib.util.module_from_spec(spec);sys.modules[name]=result;spec.loader.exec_module(result);return result


def original_auditor():
    require(not OLD_AUDITOR.is_symlink() and sha(OLD_AUDITOR.read_bytes())==OLD_AUDITOR_SHA,
            'original independently frozen V45 screening auditor differs')
    result=load(OLD_AUDITOR,'_request_v1_original_v45_metadata_auditor');result.verify_freeze();return result


def validate_exposure_fingerprint(plan,exposure):
    names=exposure['repositories']
    require(names==sorted(set(names)) and type(exposure['repository_count']) is int
            and exposure['repository_count']==len(names),'original exposure identities duplicate or count differs')
    semantic=fp(exposure)
    require(plan['qualification_and_universe']['prior_exposure_sha256']==semantic,
            'original canonical exposure fingerprint differs; pretty-file SHA is not semantic authority')
    return {'semantic_fingerprint':semantic,'repository_count':len(names),
            'record_existed_at_original_freeze':False,
            'boundary':'New reconstruction from original code and pinned inputs, not an invented old file.'}


def remaining_screening_seconds(total,known_old_outer_seconds):
    require(type(total) is int and total==7200,'original total screening ceiling differs')
    require(type(known_old_outer_seconds) in (int,float) and math.isfinite(known_old_outer_seconds)
            and 0<=known_old_outer_seconds<=total,'unknown, invalid or over-budget original screening cost')
    return total-known_old_outer_seconds


def git_blob(repo,commit,relative):
    require(isinstance(commit,str) and re.fullmatch('[0-9a-f]{40}',commit),'exact original source commit required')
    p=PurePosixPath(relative)
    require(not p.is_absolute() and '..' not in p.parts and str(p)==relative and '\\' not in relative,
            'noncanonical original metadata/source path')
    env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_NO_LAZY_FETCH='1',PYTHONDONTWRITEBYTECODE='1')
    return subprocess.check_output(['git','--no-replace-objects','-c','core.fsmonitor=false','-C',str(repo),
                                   'show',commit+':'+relative],env=env,stderr=subprocess.PIPE)


def committed_bytes(repo,commit,path,expected_sha=None):
    path=Path(path).absolute()
    require(path.resolve()==path and path.is_file() and not path.is_symlink()
            and path.is_relative_to(repo),'original input is not a regular canonical repository file')
    raw=path.read_bytes();relative=path.relative_to(repo).as_posix()
    require(git_blob(repo,commit,relative)==raw,'original committed metadata bytes changed: '+relative)
    require(expected_sha is None or sha(raw)==expected_sha,'original held metadata hash differs: '+relative)
    return raw


def inspect_original(repo,records,prequery_commit,screening_commit):
    """Validate only committed source/metadata, no target blobs or oracle calls."""
    repo,records=Path(repo).resolve(),Path(records).resolve()
    require(records==repo/'research/unified_consequence_runtime/archaeology/native-namespace-v45/prospective',
            'exact original V45 metadata record root required')
    plan_raw=committed_bytes(repo,prequery_commit,records/'PREQUERY.json')
    pre_raw=committed_bytes(repo,screening_commit,records/'PREQUERY_EXECUTION.json')
    metadata_raw=committed_bytes(repo,screening_commit,records/'METADATA_CURATION.json')
    pool_raw=committed_bytes(repo,screening_commit,records/'FROZEN_POOL.json')
    plan,pre,metadata,pool=[json.loads(raw) for raw in (plan_raw,pre_raw,metadata_raw,pool_raw)]
    require(pre['source_commit']==prequery_commit and pre['state']=='PREQUERY_COMMITTED_BEFORE_QUERIES'
            and pre['target_query_count_before_receipt']==0,'original query commitment/provenance differs')
    for key in ('plan','code','gate_descriptor'):
        row=pre[key];require(row['source_commit']==prequery_commit,'original metadata descriptor has another commit')
        committed_bytes(repo,prequery_commit,repo/row['path'],row['sha256'])
    require(sha(plan_raw)==pre['plan']['sha256']==metadata['prequery_plan_sha256'],
            'original metadata plan hash chain differs')
    require(sha(pre_raw)==metadata['prequery_execution_sha256']==pool['prequery_execution_sha256'],
            'original execution receipt hash chain differs')
    require(sha(metadata_raw)==pool['metadata_curation_sha256'],'original complete metadata curation hash differs')
    require(pool['screening_budget']==plan['screening_budget']==pre['screening_budget']
            and pool['screening_budget']['total_screening_wall_seconds']==7200,
            'original fixed pool screening budget differs')
    require(pool['requested_roles']==pre['requested_roles']==plan['requested_roles']==2,
            'original deterministic role count differs')
    code_path=repo/pre['code']['path']
    require(sha(code_path.read_bytes())==plan['curation_code_sha256'],'original plan code pin differs')
    if str(repo) not in sys.path:sys.path.insert(0,str(repo))
    curator=load(code_path,'_request_v1_original_A_v45_curator')
    exposure=curator._exposure_record()
    reconstructed=validate_exposure_fingerprint(plan,exposure)
    research=repo/'research/unified_consequence_runtime'
    input_pins={}
    for name,digest in exposure['input_files_sha256'].items():
        raw=committed_bytes(repo,prequery_commit,research/name,digest)
        input_pins[(research/name).relative_to(repo).as_posix()]=sha(raw)
    auditor=original_auditor()
    metadata_summary=auditor._raw.audit_metadata(plan,pre,metadata,pool)
    supplemental_raw=committed_bytes(repo,prequery_commit,records/'SUPPLEMENTAL_PREQUERY_FREEZE.json')
    supplemental=json.loads(supplemental_raw)
    inputs=supplemental['inputs']
    for row in inputs.values():committed_bytes(repo,prequery_commit,repo/row['path'],row['sha256'])
    require(inputs['prequery']['sha256']==sha(plan_raw),'supplemental original prequery binding differs')
    declared=json.loads((repo/inputs['declared_universe']['path']).read_bytes())
    require(declared['repositories']==plan['repository_universe_fixed_before_github_queries'],
            'original declared universe identity/order differs')
    addendum=json.loads((repo/inputs['additional_prior_exposure']['path']).read_bytes())
    auditor.validate_supplemental_exposure(plan,exposure,addendum)
    require(supplemental['query_count_before_receipt']==0 and supplemental['native_calls']==0
            and supplemental['model_calls']==0,'supplemental pre-data boundary differs')
    return {'status':'PASS_ORIGINAL_COMMITTED_METADATA_AND_RECONSTRUCTED_EXPOSURE_ONLY',
        'original_prequery_commit':prequery_commit,'original_screening_commit':screening_commit,
        'original_metadata_root':str(records),'metadata_summary':metadata_summary,
        'original_record_sha256':{'PREQUERY.json':sha(plan_raw),'PREQUERY_EXECUTION.json':sha(pre_raw),
             'METADATA_CURATION.json':sha(metadata_raw),'FROZEN_POOL.json':sha(pool_raw)},
        'original_curator':pre['code'],'reconstructed_exposure':exposure,
        'exposure_reconstruction':reconstructed,'original_exposure_input_files_sha256':input_pins,
        'supplemental_freeze_sha256':sha(supplemental_raw),'supplemental_exposure_count':len(addendum['repositories']),
        'original_metadata_costs':metadata['costs'],'fresh_metadata_queries':0,'target_source_reads':0,
        'native_test_executions':0,'model_calls':0,'scientific_verdicts':{'G'+str(i):'UNKNOWN' for i in range(2,7)}}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('repo','original-records','out'):parser.add_argument('--'+name,type=Path,required=True)
    for name in ('prequery-commit','screening-commit'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args();out=args.out.absolute();out.mkdir(parents=True,exist_ok=False)
    started=time.monotonic();result={'status':'UNKNOWN_ORIGINAL_METADATA_RECONSTRUCTION'}
    try:
        if str(args.repo.resolve()) not in sys.path:sys.path.insert(0,str(args.repo.resolve()))
        from research.unified_consequence_runtime.qualify_experiment_interface_v43 import index_interval
        with index_interval(args.repo,out/'ROOT_INDEX_INTERVAL'):
            result=inspect_original(args.repo,args.original_records,args.prequery_commit,args.screening_commit)
        if 'reconstructed_exposure' in result:
            raw=(json.dumps(result['reconstructed_exposure'],sort_keys=True,indent=2)+'\n').encode()
            (out/'RECONSTRUCTED_ORIGINAL_EXPOSURE.NEW_WITNESS.json').write_bytes(raw)
            result['materialized_new_witness']={'path':str(out/'RECONSTRUCTED_ORIGINAL_EXPOSURE.NEW_WITNESS.json'),
                'sha256':sha(raw),'old_file_existence_claim':False,
                'semantic_fingerprint':result['exposure_reconstruction']['semantic_fingerprint']}
    except Exception as error:result['smallest_obstruction']=type(error).__name__+': '+str(error)
    result.update(schema='UDM_REQUEST_ACTIVATION_V1_ORIGINAL_METADATA_RECONSTRUCTION',
        wall_seconds=time.monotonic()-started,fresh_target_queries=0,native_test_executions=0,model_calls=0)
    (out/'RESULT.json').write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(canonical({k:result[k] for k in ('status','smallest_obstruction','wall_seconds') if k in result}))
    return int(result['status'].startswith('UNKNOWN'))


if __name__=='__main__':raise SystemExit(main())
