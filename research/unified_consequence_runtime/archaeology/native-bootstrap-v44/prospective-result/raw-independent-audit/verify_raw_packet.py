"""Independent, data-only readback of the exact closed V44 screening packet."""
from pathlib import Path
from types import FunctionType
import hashlib
import importlib.util
import json
import math
import os
import stat
import subprocess
import time

PACKET=Path('/workspace/qualification/native-bootstrap-v44-final-raw-packet')
ROOT=Path('/workspace/qualification/native-frontier-v44-operator')
REPO=Path('/workspace/udm-v54')
OUT=Path(__file__).resolve().parent/'ATTEMPT_003'
SOURCE='77c2ef539aed252e037c5c0a67dd62816d5306b4'
PREQUERY='b112b69dcda962c9323cbcd13aefdcd580a5449a'
AUTHORITY='8c1ae9852b4cc60fb8773863b790c18b0b9dc4c1733fddb96e4a577e5a0dc0b0'
VERIFIER=Path('/workspace/qualification/experiment-interface-v43-negative-archive-prep/independent_verify_cas.py')
VERIFIER_SHA='05ea4d635494f045ab5c39c1420c2143ffec22110577e6492b9d9d1bfa92a018'
PREFIX='research/unified_consequence_runtime/archaeology/native-bootstrap-v44/prospective/'
CHECKS=[]

def sha(raw):return hashlib.sha256(raw).hexdigest()

def check(name,condition):
    CHECKS.append({'check':name,'pass':bool(condition)})
    if not condition:raise ValueError(name)

def strict(raw):
    def pairs(rows):
        result={}
        for key,value in rows:
            if key in result:raise ValueError('duplicate JSON key')
            result[key]=value
        return result
    def invalid(value):raise ValueError('nonfinite JSON: '+value)
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid)

def js(path):return strict(Path(path).read_bytes())

def fingerprint(value):return sha(json.dumps(value,sort_keys=True,separators=(',',':')).encode())

def original_verifier():
    check('original independent readback implementation pin',not VERIFIER.is_symlink() and sha(VERIFIER.read_bytes())==VERIFIER_SHA)
    spec=importlib.util.spec_from_file_location('independent_v43_cas_readback',VERIFIER)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    # Original qualified functions; only the documentary V44 data labels differ.
    namespace=dict(vars(module),SCHEMA='UDM_CONTENT_ADDRESSED_RAW_EVIDENCE_ARCHIVE_V44',SCOPE='RAW_SCREENING_AND_SCIENTIFIC_EVIDENCE_DATA_ONLY_NO_PROMOTION')
    for name,value in tuple(vars(module).items()):
        if isinstance(value,FunctionType) and value.__globals__ is vars(module):
            bound=FunctionType(value.__code__,namespace,name,value.__defaults__,value.__closure__)
            bound.__kwdefaults__=value.__kwdefaults__;namespace[name]=bound
    return namespace

def translated(row):
    row=dict(row);row.pop('path',None);row['mode']=int(row['mode'],8)
    return row

def coverage_projection(rows):
    return [dict({key:row[key] for key in ('repo','status','closed_pr_count','closed_pr_window','qualifying_prs')},
                 query_endpoints=len(row['query_coverage'])) for row in rows]

def component_pinset_matches(boundary,raw):
    config=strict(raw)
    return (boundary['source_pins_sha256']==sha(raw)
            and boundary['source_pins']=={key:config[key] for key in ('development','metatron','flash')})

def main():
    OUT.mkdir(exist_ok=False)
    started=time.monotonic();audit={'schema':'UDM_V44_INDEPENDENT_RAW_PACKET_AUDIT_V1','status':'UNKNOWN','checks':CHECKS}
    try:
        archive=PACKET/'RAW_SCREENING_PACKET.tar.gz';manifest=PACKET/'RAW_SCREENING_PACKET.MANIFEST.json'
        check('held archive exact digest and size',sha(archive.read_bytes())=='80e5a5678bd1c713ab8aeb7fabd9c12b8bef85b6274a4302e4c8887968738d34' and archive.stat().st_size==8529335)
        check('held external manifest exact digest and size',sha(manifest.read_bytes())=='628cc380368ba698f8a05cf552bf680eab953092fd3e2db61abbc5cd415e1482' and manifest.stat().st_size==297606)
        original=original_verifier();verdict=original['verify'](archive,manifest,ROOT)
        check('strict original full CAS and actual-source verification',verdict['status']=='PASS' and verdict['source_entries']==1351 and verdict['unique_objects']==457 and verdict['source_counts']=={'directory':318,'file':1033,'symlink':0})
        readback=js(PACKET/'RAW_SCREENING_PACKET.READBACK.json')
        check('producer readback exact held bytes',sha((PACKET/'RAW_SCREENING_PACKET.READBACK.json').read_bytes())=='5d9c5b7ad30a2cd17e24567e339b6af97a32e36df5d642a1497301e9748d348f')
        check('independent replay equals every producer readback field',verdict==readback['original_verdict'])
        data=js(manifest);files=data['files']
        before=js(PACKET/'ORIGINAL_OPERATOR_INVENTORY.json')
        attachments=js(PACKET/'ATTACHMENT_FILES.json')
        old={row['path']:translated(row) for row in before['entries']}
        new={'archive-attachments/'+row['path']:translated(row) for row in attachments['entries']}
        check('original inventory exact held digest',sha((PACKET/'ORIGINAL_OPERATOR_INVENTORY.json').read_bytes())=='34adfb5a98ff27b46d675876775a4bb3180a2e7728aebfa1a525fe7c178d97f8')
        check('all original 1151 paths unchanged',len(old)==1151 and all(files.get(name)==row for name,row in old.items()))
        check('all documentary 199 attachment entries retained',len(new)==199 and all(files.get(name)==row for name,row in new.items()))
        check('exact lossless inventory union no omission or extra',set(files)==set(old)|set(new)|{'archive-attachments'} and len(files)==1351)
        for row in js(PACKET/'PACKET_DESCRIPTORS.json')['files']:
            path=Path(row['path'])
            check('sidecar identity:'+row['name'],path.parent==PACKET and path.name==row['name'] and not path.is_symlink() and sha(path.read_bytes())==row['sha256'] and path.stat().st_size==row['bytes'] and stat.S_IMODE(path.stat().st_mode)==int(row['mode'],8))
        check('original actor exact held bytes',sha((ROOT/'SCREENING_ACTOR_ATTESTATION.json').read_bytes())=='3fe66d3232595fa23b90a4aa8f8bc9a155872d7a4379183df7bf3fa6db1c9291')
        check('original controller exact held bytes',sha((ROOT/'ORDERED_PROCESS_COSTS.json').read_bytes())=='5ea1296374faa661bd175e24ac0b4e2a486256cc0241cc9119de04767dcb98b1')
        actor=js(ROOT/'SCREENING_ACTOR_ATTESTATION.json');controller=js(ROOT/'ORDERED_PROCESS_COSTS.json')
        check('actor bounded original authority and no solver/retry access',actor['source_commit']==SOURCE and actor['prequery_commit']==PREQUERY and actor['authority_sha256']==AUTHORITY and actor['independent_screener'] is True and actor['search_or_policy_outcomes_accessed'] is False and actor['learner_future_source_accessed'] is False and actor['native_test_reruns_or_case_retries_performed'] is False and actor['source_unchanged'] is True and actor['index_changes']==[])
        check('complete exactly ordered once-only original processes',controller['source_commit']==SOURCE and controller['authority_sha256']==AUTHORITY and controller['completed'] is True and controller['retries_performed'] is False and [row['index'] for row in controller['cases']]==[0,1] and all(row['returncode']==0 for row in controller['cases']))
        transport=js(ROOT/'archive-attachments/COMMITTED_SOURCE_TRANSPORT.json')
        check('exact immutable source transport commit',transport['source_commit']==SOURCE)
        env=dict(os.environ,GIT_OPTIONAL_LOCKS='0')
        for row in transport['files']:
            path=ROOT/'archive-attachments/screening-commit-source'/row['path']
            raw=path.read_bytes()
            original_blob=subprocess.check_output(['git','-C',str(REPO),'show',SOURCE+':'+row['path']],env=env)
            check('committed original source transport:'+row['path'],raw==original_blob and sha(raw)==row['sha256'] and len(raw)==row['bytes'] and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==row['git_blob'])
        check('all committed prospective source records included',len([row for row in transport['files'] if row['path'].startswith(PREFIX)])==26)
        records=ROOT/'archive-attachments/screening-commit-source'/PREFIX
        plan=js(records/'PREQUERY.json');curation=js(records/'METADATA_CURATION.json');pool=js(records/'FROZEN_POOL.json');exposure=js(records/'PRIOR_EXPOSURE.json')
        check('complete declared nine-repository source universe',len(plan['repository_universe_fixed_before_github_queries'])==9 and plan['repository_universe_fixed_before_github_queries']==[row['repo'] for row in curation['repositories']])
        check('all original prior exposure exclusions retained',set(exposure['repositories'])<=set(plan['historically_touched_repository_exclusions']) and not set(exposure['repositories'])&set(plan['repository_universe_fixed_before_github_queries']))
        check('all seven metadata negatives retained without resampling',sum(row['status']=='NO_QUALIFYING_CANDIDATE' for row in curation['repositories'])==7 and len(pool['pool'])==2)
        check('committed exact complete ordered requests',all(js(ROOT/f'requests/request-{i:03d}.json')['spec']==spec for i,spec in enumerate(pool['pool'])))
        auditpath=ROOT/'archive-attachments/independent-screening-audit/ACTUAL_SCREENING_ATTEMPT_001/SCREENING_AUDIT.json'
        check('actual independent screening audit retained byte-for-byte',sha(auditpath.read_bytes())=='9b50d86e36b11eaf3e78a0c4b4d022cd8a71bf6f8cd8453c63c33a80f91b241b')
        actual=js(auditpath)
        check('actual supplied-run audit source and full pool closure',actual['status']=='PASS_ADMISSION_ONLY_SCREENING_AUDIT' and actual['source_commit']==SOURCE and actual['counts']=={'screened_cases':2,'eligible_cases':0} and actual['all_checks_closed'] is True and len(actual['checks'])==39 and all(row['pass'] for row in actual['checks']))
        dependencies=js(ROOT/'archive-attachments/INDEPENDENT_AUDITOR_DEPENDENCIES.json')
        for row in dependencies['files']:
            path=Path(row['path'])
            check('frozen independent auditor transport:'+row['original_path'],path.is_relative_to(ROOT) and sha(path.read_bytes())==row['sha256']==row['original_sha256'] and path.stat().st_size==row['bytes'])
        check('all frozen 30 audit dependencies retained',len(dependencies['files'])==30 and dependencies['frozen_auditor']['sha256']=='ee045a6252174ad5d23ba6b932283855656e5067dea3cc3d3cbf3748282c8be6')
        coverage=js(ROOT/'archive-attachments/SOURCE_COVERAGE_AND_SHORTFALL.json')
        check('source coverage exact closed campaign',coverage['source_commit']==SOURCE and coverage['prequery_commit']==PREQUERY and coverage['screening_authority_sha256']==AUTHORITY and coverage['metadata_universe']['ordered_records']==coverage_projection(curation['repositories']) and coverage['screening']['eligible']==0 and coverage['screening']['fixed_pool']==2)
        for i in range(2):
            case=ROOT/f'screening/case-{i:03d}';report=js(case/'SCREENING_CASE.json')
            check('unchanged original refusal:'+str(i),report['status']=='UNKNOWN_CONTRACT' and report['eligible'] is False and coverage['screening']['cases'][i]['reason']==report['setup']['reason'])
            check('no actual native or backend launch:'+str(i),report['controller_attempts']['native_calls']==report['controller_attempts']['collection_calls']==0 and report['bootstrap_attempts']['after']['backend_calls']-report['bootstrap_attempts']['before']['backend_calls']==0 and not list(case.rglob('checked-report.json')) and not list(case.rglob('build-attempt.json')))
            ledger=case/'machine-state/metatron-ledger.jsonl';rows=[strict(line) for line in ledger.read_bytes().splitlines() if line.strip()]
            check('no scientific acquisition in causal state:'+str(i),not any(row['kind'] in ('executable_capability','native_frontier_route','native_environment_selection_v44') for row in rows))
        costs=actual['costs']
        check('all actual native/backend/build launch counters remain zero',all(costs[k]==0 for k in ('native_calls','collection_calls','build_calls','verification_attempts','metadata_backend_calls')))
        check('original parent and nested intervals preserved without double charging',costs['controller_wall_seconds']==controller['wall_seconds'] and math.isclose(costs['sum_case_inclusive_wall_seconds'],sum(row['total_wall_seconds'] for row in coverage['screening']['cases']),abs_tol=1e-8) and coverage['costs']['metadata_curation']==curation['costs'] and coverage['costs']['metadata_parent_process_seconds']==18.110675445001107 and controller['nested_intervals_not_additive'] is True)
        unknown={f'G{i}':'UNKNOWN' for i in range(2,7)}
        check('no scientific promotion from packaging or audit',coverage['verdicts']==actual['scientific_verdicts']==readback['verdicts']==unknown)
        boundary=js(ROOT/'archive-attachments/COMPONENT_ARCHIVE_BOUNDARY.json')
        check('full original component trees explicitly separate final-CI artifacts','Separate final-CI' in boundary['complete_original_component_source_trees'] and component_pinset_matches(boundary,(ROOT/'archive-attachments/screening-commit-source/research/unified_consequence_runtime/developmental_sources.json').read_bytes()))
        for row in boundary['pinned_original_files']:
            check('original component pinned file:'+row['original_path'],sha(Path(row['path']).read_bytes())==row['sha256']==row['original_sha256'] and Path(row['path']).stat().st_size==row['bytes'])
        audit.update(status='PASS_DATA_ONLY_ARCHIVE_AND_SCOPE',original_verifier={'path':str(VERIFIER),'sha256':VERIFIER_SHA,'data_labels_only':['SCHEMA','SCOPE']},archive={'path':str(archive),'sha256':sha(archive.read_bytes()),'bytes':archive.stat().st_size},manifest={'path':str(manifest),'sha256':sha(manifest.read_bytes())},independently_recomputed_readback=verdict,source_union={'original_entries':len(old),'attachment_entries':len(new),'attachment_root_entries':1,'total_entries':len(files)},source_commit=SOURCE,actual_audit_sha256=sha(auditpath.read_bytes()),costs=costs,metadata_parent_process_seconds=coverage['costs']['metadata_parent_process_seconds'],verdicts=unknown)
    except Exception as error:
        audit['error']=type(error).__name__+': '+str(error)
    audit.update(archive_extracted=False,archived_code_executed=False,new_source_queries=0,new_native_calls=0,new_collection_calls=0,new_model_calls=0,scope='Independent data retention/source-union and original bounded refusal/cost evidence only. No acquisition, solver/comparator, containment or general source-universe exhaustiveness claim.',audit_wall_seconds=time.monotonic()-started,auditor_source_sha256=sha(Path(__file__).read_bytes()))
    with (OUT/'REPORT.json').open('x') as stream:json.dump(audit,stream,sort_keys=True,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({'status':audit['status'],'checks':len(CHECKS),'failures':sum(not row['pass'] for row in CHECKS),'report_sha256':sha((OUT/'REPORT.json').read_bytes())},sort_keys=True))
    return 0 if audit['status']=='PASS_DATA_ONLY_ARCHIVE_AND_SCOPE' else 1

if __name__=='__main__':raise SystemExit(main())
