"""Install exact reviewed new V43 records and write a query-free prequery.

Trusted root runs this after the independent audit and source HOLD release.
No existing differing file is overwritten. No metadata/source query or Git
mutation is performed. This installer itself has not performed installation.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

READINESS = Path('/workspace/qualification/experiment-interface-v43-prospective-readiness')
INPUTS_SHA256 = '2fdc871279cf2c9c5b028f5b9f1e337fb5c46419f701779950d04bd946b7bc36'
AUDIT_SHA256 = '650ad69d0c2ca929ec3e13c17828e752911b66f96772f74471e2c10405245a34'
REPORT_SHA256 = 'd6ba4346d4acf9b7d7e9997b4c453a3a2ecbcfe160e64f6f29d284cfb272f198'
RESULT_SHA256 = '61ffe7857fde05f459152a3f94f340f221c9aee814558cbfba494d8cf358d599'
INTERFACE_ARCHIVE_SHA256 = '4c9ba1bd8029efd06aa192e86d75f78d1326316a0becc2a84a4b85a9b6f0f033'
SOURCE_COMMIT = '5a449e7d6be3a54d42e2098804904c2e1223ae51'
RECORDS = Path('research/unified_consequence_runtime/archaeology/experiment-interface-v43/prospective')
OLD_GATE = {
    'artifact_id':12338856551,
    'artifact_sha256':'25edc3c805bf7cf8a050b9c3c5c4e640a8ea8dbc2b5a7920157b5201c4ca6460',
    'qualification_result_sha256':'10d6d2255be781ea18b795b00e849a3075cd385f4bd5993d94bc72c6c039af7a',
    'result_path':'research/unified_consequence_runtime/archaeology/native-authority-v42/CI_39582982718_RESULT.json',
    'run_id':39582982718,'source_commit':'f1779c7443ae6035dee502a201d95d778056c05d',
    'status':'ADMISSION_ONLY_QUALIFIED'}
CATALOG = {'path':'research/unified_consequence_runtime/archaeology/native-authority-v41/ENVIRONMENT_CATALOG.json',
    'sha256':'2050def754f8b0b7d39f3ea256a6c4a5997876fd21ebd6a1afb134b06cb8dfc6'}


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def exact(path, expected):
    path=Path(path)
    if path.is_symlink() or not path.is_file() or sha(path)!=expected:
        raise ValueError('exact independently retained bytes required: '+str(path))
    return path.read_bytes()


def install(repo, relative, data, installed):
    target=repo/relative
    if not target.resolve().is_relative_to(repo) or target.is_symlink():
        raise ValueError('ordinary in-repository new file required: '+str(target))
    if target.exists():
        if target.read_bytes()!=data:
            raise ValueError('refusing to overwrite different existing bytes: '+str(target))
    else:
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as stream:stream.write(data)
    installed[Path(relative).as_posix()]=hashlib.sha256(data).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=Path('/workspace/udm-v54'))
    parser.add_argument('--python',type=Path,default=Path('/workspace/qualification/native-authority-v42-controller/bin/python'))
    parser.add_argument('--audit-dir',type=Path,default=Path('/workspace/qualification/experiment-interface-v43-ci-independent-audit/RUN_39682460349_ATTEMPT_004'))
    parser.add_argument('--old-artifact',type=Path,default=Path('/workspace/qualification/native-authority-v42-ci-observer/native-authority-v42-39582982718.zip'))
    parser.add_argument('--interface-artifact',type=Path,default=Path('/workspace/qualification/experiment-interface-v43-ci-observer/experiment-interface-v43-39682460349-connector.zip'))
    args=parser.parse_args()
    repo=args.repo.absolute()
    if repo.resolve()!=repo or repo.is_symlink():raise ValueError('canonical repository root required')
    manifest=json.loads(exact(READINESS/'ASSEMBLY_INPUTS.json',INPUTS_SHA256))
    inputs=[(row,exact(row['source'],row['sha256'])) for row in manifest['files']]
    audit_raw=exact(args.audit_dir/'INTERFACE_ARCHIVE_AUDIT.json',AUDIT_SHA256)
    report_raw=exact(args.audit_dir/'REPORT.json',REPORT_SHA256)
    result_raw=exact(args.audit_dir/'QUALIFICATION_RESULT.json',RESULT_SHA256)
    audit,report,result=map(json.loads,(audit_raw,report_raw,result_raw))
    if (audit.get('schema')!='UDM_V43_INDEPENDENT_INTERFACE_ARCHIVE_AUDIT_V1'
            or audit.get('status')!='PASS_INDEPENDENT_ARCHIVE_AUDIT'
            or audit.get('all_native_packets_checked') is not True
            or report.get('status')!='PASS_BOUNDED_NATIVE_INTERFACE_ARTIFACT_AUDIT'
            or report.get('failures') or len(report.get('checks',[]))!=5039
            or report.get('source_commit')!=SOURCE_COMMIT
            or result.get('source_commit')!=SOURCE_COMMIT or result.get('mode')!='whole'):
        raise ValueError('actual complete independently audited gate required')
    gate=audit['interface_gate']
    if (gate['source_commit']!=SOURCE_COMMIT or gate['run_id']!=39682460349
            or gate['artifact_id']!=12386633479 or gate['artifact_sha256']!=INTERFACE_ARCHIVE_SHA256
            or gate['qualification_result_sha256']!=RESULT_SHA256
            or Path(gate['result_path'])!=repo/RECORDS/'CI_39682460349_RESULT.json'):
        raise ValueError('independent gate descriptor differs from exact accepted run')
    if sha(args.old_artifact)!=OLD_GATE['artifact_sha256'] or sha(args.interface_artifact)!=INTERFACE_ARCHIVE_SHA256:
        raise ValueError('exact original and whole-interface ZIPs required')
    exact(repo/OLD_GATE['result_path'],OLD_GATE['qualification_result_sha256'])
    exact(repo/CATALOG['path'],CATALOG['sha256'])
    for name,expected in audit['gate_files_sha256'].items():exact(repo/name,expected)
    review=json.loads((READINESS.parent/'experiment-interface-v43-prospective-protocol-review/FINAL_REVIEW.json').read_text())
    if (review.get('status')!='PASS_FINAL_READINESS_PROTOCOL_REVIEW_ONLY'
            or review.get('draft_freeze_sha256')!=manifest['draft_freeze_sha256']):
        raise ValueError('reviewed exact readiness freeze required')
    installed={}
    for row,data in inputs:install(repo,row['target'],data,installed)
    install(repo,RECORDS/'CI_39682460349_RESULT.json',result_raw,installed)
    install(repo,RECORDS/'INTERFACE_ARCHIVE_AUDIT.json',audit_raw,installed)
    install(repo,RECORDS/'INTERFACE_INDEPENDENT_REPORT.json',report_raw,installed)
    wrapper={'environment_gate':OLD_GATE,'catalog':CATALOG,'interface_gate':gate,
        'interface_archive_audit':{'path':(RECORDS/'INTERFACE_ARCHIVE_AUDIT.json').as_posix(),'sha256':AUDIT_SHA256}}
    sys.path.insert(0,str(repo))
    from research.unified_consequence_runtime import qualify_native_frontier_v43 as q
    q.require_environment_gate(wrapper)
    install(repo,RECORDS/'GATE_WRAPPER.json',(q.canonical(wrapper)+'\n').encode(),installed)
    check=json.loads((READINESS/'UNFROZEN_UNIVERSE_GRAMMAR_CHECK.json').read_text())
    names=check['candidate_names']
    if (len(names)!=9 or check['frozen'] is not False or check['network_queries']!=0
            or check['overlap_prior_exposure'] or names!=sorted(set(names))):
        raise ValueError('exact reviewed fixed-nine grammar/exposure proposal required')
    universe={'schema':'UDM_NATIVE_AUTHORITY_V43_DECLARED_UNIVERSE_V1','repositories':names,
        **{key:wrapper[key] for key in ('environment_gate','interface_gate','interface_archive_audit')}}
    install(repo,RECORDS/'DECLARED_UNIVERSE.json',(q.canonical(universe)+'\n').encode(),installed)
    command=[str(args.python.absolute()),'-B',str(repo/RECORDS/'curate_frontier.py'),
        '--write-prequery',str(repo/RECORDS/'PREQUERY.json'),'--universe',str(repo/RECORDS/'DECLARED_UNIVERSE.json'),
        '--environment-gate',str(repo/RECORDS/'GATE_WRAPPER.json'),'--qualification-artifact',str(args.old_artifact.absolute()),
        '--interface-qualification-artifact',str(args.interface_artifact.absolute())]
    completed=subprocess.run(command,cwd=repo,text=True,capture_output=True)
    (READINESS/'ASSEMBLY_PREQUERY.stdout').write_text(completed.stdout)
    (READINESS/'ASSEMBLY_PREQUERY.stderr').write_text(completed.stderr)
    if completed.returncode:raise ValueError('query-free prequery assembly refused; retained exact stderr')
    installed[(RECORDS/'PREQUERY.json').as_posix()]=sha(repo/RECORDS/'PREQUERY.json')
    summary={'schema':'UDM_V43_REVIEWED_PROSPECTIVE_ASSEMBLY_V1','status':'ASSEMBLED_MUST_COMMIT_BEFORE_METADATA_QUERY',
        'inputs_sha256':INPUTS_SHA256,'interface_audit_sha256':AUDIT_SHA256,'installed_files_sha256':installed,
        'prequery_command':command,'metadata_queries':0,'target_source_queries':0,'native_or_model_calls':0,
        'git_mutations':0,'old_gate':OLD_GATE,'catalog':CATALOG,'interface_gate':gate}
    (READINESS/'ASSEMBLY_RESULT.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':summary['status'],'files':len(installed),'metadata_queries':0,'git_mutations':0},sort_keys=True))


if __name__=='__main__':main()
