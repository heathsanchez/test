"""DRAFT: data-only final packaging over the existing V43 archive machinery.

No native worker, learner, constructor, model or archived source is executed.
A passing archive check grants no new scientific or external authority.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
from types import FunctionType

PREFIX='research/unified_consequence_runtime/'
OLD=PREFIX+'archaeology/experiment-interface-v43/prospective-result/archive-verification/'
BUILDER_SHA256='98f44e38b0b5e71a168e6ffe30e616ad7f3125dc4f381ef3d9a60f76865150d8'
VERIFIER_SHA256='05ea4d635494f045ab5c39c1420c2143ffec22110577e6492b9d9d1bfa92a018'
CAS_SCHEMA='UDM_CONTENT_ADDRESSED_RAW_EVIDENCE_ARCHIVE_V44'
CAS_SCOPE='RAW_SCREENING_AND_SCIENTIFIC_EVIDENCE_DATA_ONLY_NO_PROMOTION'
CAS_BOUNDARY=('Lossless raw screening, refusal, scientific-process and audit bytes, with original path, mode and link metadata. '
              'No extraction, archived-code execution, native replay or new scientific promotion.')
BASE='8830a66fcb261b192d98da495b6cb91697d21f28'
BASE_FILES=2628
OWNED_BRANCH='research/udm-native-bootstrap-v44-20261022'
OPERATOR_ROOT='/workspace/qualification/native-frontier-v44-operator'
UNKNOWN={f'G{i}':'UNKNOWN' for i in range(2,7)}
HEX64=re.compile(r'[0-9a-f]{64}\Z')
HEX40=re.compile(r'[0-9a-f]{40}\Z')


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def strict(raw):
    def pairs(values):
        result={}
        for key,value in values:
            if key in result:raise ValueError('duplicate JSON key')
            result[key]=value
        return result
    def invalid(value):raise ValueError('nonfinite JSON constant: '+value)
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid)


def write_once(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as output:json.dump(value,output,sort_keys=True,indent=2,allow_nan=False);output.write('\n')


def trusted(repo,name,expected):
    root=Path(repo).resolve();path=root/OLD/name
    if path.is_symlink() or path.resolve()!=path or digest(path)!=expected:
        raise ValueError('original data-archive implementation changed: '+name)
    spec=importlib.util.spec_from_file_location('_trusted_v43_'+path.stem,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    # New data labels only; the qualified original algorithms are byte-identical.
    namespace=dict(vars(module),SCHEMA=CAS_SCHEMA,SCOPE=CAS_SCOPE,BOUNDARY=CAS_BOUNDARY)
    for key,value in tuple(vars(module).items()):
        if isinstance(value,FunctionType) and value.__globals__ is vars(module):
            rebound=FunctionType(value.__code__,namespace,value.__name__,value.__defaults__,value.__closure__)
            rebound.__kwdefaults__=value.__kwdefaults__;namespace[key]=rebound
    return type('ArchiveFunctions',(),namespace)


def cas_verifier(repo):return trusted(repo,'independent_verify_cas.py',VERIFIER_SHA256)


def pack(repo,source,archive,manifest,readback,summary):
    builder=trusted(repo,'build_data_archive.py',BUILDER_SHA256)
    builder.build(source,archive,manifest,summary)
    original=cas_verifier(repo).verify(archive,manifest,source)
    result={'schema':'UDM_V44_DATA_ARCHIVE_READBACK_V1','status':'PASS_ARCHIVE_READBACK_ONLY',
            'original_verdict':original,'original_verifier_sha256':VERIFIER_SHA256,
            'manifest_schema':CAS_SCHEMA,'manifest_scope':CAS_SCOPE,'verdicts':dict(UNKNOWN),
            'boundary':CAS_BOUNDARY}
    write_once(readback,result)
    return result


def bound(root,name,pin):
    if (not isinstance(name,str) or not name or name.startswith('/') or '\x00' in name
            or str(PurePosixPath(name))!=name or any(p in ('','.','..') for p in name.split('/'))):
        raise ValueError('unsafe committed record path')
    path=Path(root)/name
    if path.is_symlink() or path.resolve()!=path or not path.is_file():
        raise ValueError('record missing or redirected: '+name)
    if (set(pin)!={'sha256','bytes'} or not HEX64.fullmatch(pin.get('sha256',''))
            or type(pin.get('bytes')) is not int or pin['bytes']<0
            or path.stat().st_size!=pin['bytes'] or digest(path)!=pin['sha256']):
        raise ValueError('committed record digest/size changed: '+name)
    return path


def check(repo,expectation,expectation_sha256,expected_source,out,components):
    repo,expectation,out=Path(repo).resolve(),Path(expectation).absolute(),Path(out).absolute()
    if (not HEX64.fullmatch(expectation_sha256) or expectation.is_symlink()
            or expectation.resolve()!=expectation or digest(expectation)!=expectation_sha256):
        raise ValueError('externally pinned final expectation required')
    expected=strict(expectation.read_bytes())
    if (expected.get('schema')!='UDM_V44_FINAL_EVIDENCE_EXPECTATION_V1'
            or expected.get('mode')!='ARCHIVE_ONLY_NO_SCIENTIFIC_PROMOTION'
            or not HEX40.fullmatch(expected_source)):
        raise ValueError('wrong final archive-only expectation or source')
    root=expectation.parent
    files=expected['files']
    for name,pin in files.items():bound(root,name,pin)
    for name,pin in expected.get('repository_records',{}).items():bound(repo,name,pin)
    roles=expected['roles']
    if set(roles)!={'final_result','independent_audit','report'} or any(name not in files for name in roles.values()):
        raise ValueError('exact result, independent audit and report must all be pinned')
    result=strict((root/roles['final_result']).read_bytes())
    audit=strict((root/roles['independent_audit']).read_bytes())
    if result.get('verdicts')!=expected['retained_scientific_verdicts']:
        raise ValueError('retained scientific verdict bytes differ; archive never promotes them')
    if audit.get('status')!=expected['retained_independent_audit_status']:
        raise ValueError('retain the actual independent audit status, including UNKNOWN')
    gates=expected['qualified_gate_references']
    if (not {'environment_v42','interface_v43','bootstrap_v44'} <= {row['kind'] for row in gates}
            or len({row['kind'] for row in gates})!=len(gates)):
        raise ValueError('all original and final native gate references must be retained')
    for row in gates:
        gate=row['descriptor']
        if (gate.get('status')!='ADMISSION_ONLY_QUALIFIED' or not HEX40.fullmatch(gate.get('source_commit',''))
                or any(type(gate.get(k)) is not int or gate[k]<=0 for k in ('run_id','artifact_id'))
                or any(not HEX64.fullmatch(gate.get(k,'')) for k in ('artifact_sha256','qualification_result_sha256'))):
            raise ValueError('missing exact upstream native qualification reference')
        result_pin=expected['repository_records'][row['result_record']]
        if result_pin['sha256']!=gate['qualification_result_sha256']:
            raise ValueError('upstream native result reference is not the exact retained bytes')
    if not expected['archives']:raise ValueError('raw evidence archive required even on shortfall')
    archive_checks=[]
    for item in expected['archives']:
        if (set(item)!={'archive','manifest','readback','source_root'}
                or any(item[key] not in files for key in ('archive','manifest','readback'))
                or not (item['source_root']==OPERATOR_ROOT or item['source_root'].startswith(OPERATOR_ROOT+'/'))):
            raise ValueError('raw archive, full manifest and actual readback must all be pinned')
        manifest=strict((root/item['manifest']).read_bytes())
        if manifest['source_root']!=item['source_root']:
            raise ValueError('raw evidence source identity differs from independently declared publication scope')
        actual=cas_verifier(repo).verify(root/item['archive'],root/item['manifest'],None)
        retained=strict((root/item['readback']).read_bytes())
        old=retained['original_verdict']
        if (retained.get('schema')!='UDM_V44_DATA_ARCHIVE_READBACK_V1' or old.get('status')!='PASS'
                or old.get('source_lstat_and_bytes_verified') is not True
                or retained.get('original_verifier_sha256')!=VERIFIER_SHA256
                or any(old.get(k)!=actual[k] for k in ('archive_sha256','archive_bytes','external_manifest_sha256',
                    'source_counts','source_entries','unique_objects','source_regular_bytes','unique_object_bytes'))):
            raise ValueError('retained source/readback evidence does not bind the full raw archive')
        archive_checks.append(actual)
    # Reuse the existing source and component algorithms. They execute only Git
    # reads/archive and byte checks; no qualification/native entrypoint is called.
    from research.unified_consequence_runtime import qualify_native_bootstrap_v44 as qualifier
    if components is None:raise ValueError('full original component source checkouts required')
    out.mkdir(parents=True,exist_ok=True)
    with qualifier.original.index_interval(repo,out/'final-source-index-interval'):
        ci_ref=os.environ.get('GITHUB_REF')
        if ci_ref is not None:
            if ci_ref!='refs/heads/'+OWNED_BRANCH or os.environ.get('GITHUB_SHA')!=expected_source:
                raise ValueError('archive publication is restricted to exact owned branch/source')
        elif qualifier.original._git(repo,'rev-parse','--abbrev-ref','HEAD').decode().strip()!=OWNED_BRANCH:
            raise ValueError('archive publication requires the isolated owned research branch')
        source=qualifier._source(repo)
        if (source['source_commit']!=expected_source or source.get('v43_preserved_files')!=BASE_FILES
                or qualifier.BASE!=BASE):
            raise ValueError('owned source or complete 2628-file baseline/mode preservation differs')
    record={'schema':'UDM_V44_FINAL_ARCHIVE_INTEGRITY_RESULT_V1',
            'status':'PASS_ARCHIVE_INTEGRITY_ONLY_NO_NATIVE_REPLAY',
            'source_commit':source['source_commit'],'baseline_commit':BASE,'preserved_files':BASE_FILES,
            'source_files':len(source['files']),'expectation_sha256':expectation_sha256,
            'raw_archives':archive_checks,'qualified_gate_references':gates,
            'retained_independent_audit_status':audit['status'],
            'retained_scientific_verdicts':result['verdicts'],'verdicts':dict(UNKNOWN),
            'native_calls':0,'model_calls':0,'new_source_queries':0,'index_restoration':False,
            'boundary':'Archive integrity and source preservation only. Actual native/scientific/comparator claims remain exactly those in the separately pinned original evidence.'}
    archives=qualifier.original.archive(repo,out,preparation=(root,),components=components)
    if archives['source_commit']!=expected_source:raise ValueError('publication source changed during archiving')
    record['full_source_archive']={'path':'SOURCE.tar.gz','sha256':archives['source_sha256']}
    record['component_source_status']=archives['component_source_status']
    record['component_source_manifest_sha256']=archives['component_source_manifest_sha256']
    record['full_evidence_archive']={'path':'EXPERIMENT_INTERFACE_V43_EVIDENCE.tar.gz','sha256':archives['archive_sha256']}
    write_once(out/'CI_ARCHIVE_RESULT.json',record)
    return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='mode',required=True)
    p=sub.add_parser('pack');p.add_argument('--repo',type=Path,required=True);p.add_argument('--source',type=Path,required=True)
    for name in ('archive','manifest','readback','summary'):p.add_argument('--'+name,type=Path,required=True)
    c=sub.add_parser('check');c.add_argument('--repo',type=Path,required=True);c.add_argument('--expectation',type=Path,required=True)
    c.add_argument('--expectation-sha256',required=True);c.add_argument('--expected-source-commit',required=True)
    c.add_argument('--out',type=Path,required=True);c.add_argument('--components',type=Path,required=True)
    args=parser.parse_args();os.environ['GIT_OPTIONAL_LOCKS']='0';os.environ['PYTHONDONTWRITEBYTECODE']='1'
    if args.mode=='pack':value=pack(args.repo,args.source,args.archive,args.manifest,args.readback,args.summary)
    else:value=check(args.repo,args.expectation,args.expectation_sha256,args.expected_source_commit,args.out,args.components)
    print(json.dumps(value,sort_keys=True,indent=2,allow_nan=False))


if __name__=='__main__':main()
