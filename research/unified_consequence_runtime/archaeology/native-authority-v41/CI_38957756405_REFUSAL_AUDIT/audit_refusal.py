"""Offline audit of an expected scientific readiness refusal, never native PASS.

The scientific artifact is a partial source delivery. Its owned-source pack is
combined with the independently hashed earlier admission artifact's full source
pack; only that verified union may establish complete c553 source closure.
"""
from __future__ import annotations
import argparse
import collections
import datetime
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import stat
import sys
import tarfile
import time
import zipfile

sys.path.insert(0,'/workspace/qualification/native-authority-v41-artifact-audit')
from audit_v41 import decode, read, sha, hash_file, safe, tar_members
from screening_checks import audit_screening

HERE=Path(__file__).resolve().parent
PREFIX='research/unified_consequence_runtime/archaeology/native-authority-v41/'
EXPECTED_SOURCE='c55350361a443875a23751a3ffec312497819484'
EXPECTED_SHA='fc007e1cb2436f71acfec8e03d9bac247f198046a927a23984d2efb726461e45'
OWNED=('research/unified_consequence_runtime/','.github/workflows/','docs/')
PACKET_BASE='native-authority-v41-screening-complete-evidence'


def unique_zip(packet):
    names=set()
    for info in packet.infolist():
        name=safe(info.filename,info.is_dir())
        if name in names:raise ValueError('duplicate ZIP name: '+name)
        names.add(name)
        if stat.S_ISLNK(info.external_attr>>16):raise ValueError('ZIP symlink: '+name)
    return names


def _manifest_path(packet,archive_name):
    candidates=[name for name in packet.namelist() if (name=='MANIFEST.json' or name.endswith('/MANIFEST.json'))
                and name.removesuffix('MANIFEST.json')+archive_name in packet.namelist()]
    if len(candidates)!=1:raise ValueError('one unique manifest with sibling archive required')
    return candidates[0]


def scientific_envelope(path,expected,out,check):
    actual=hash_file(path)
    check(actual==(expected['scientific_artifact_sha256'],expected['scientific_artifact_bytes']),
          'independent scientific artifact SHA256/size',actual=actual)
    if actual!=(expected['scientific_artifact_sha256'],expected['scientific_artifact_bytes']):
        raise ValueError('scientific artifact identity mismatch')
    with zipfile.ZipFile(path) as packet:
        names=unique_zip(packet);manifest_name=_manifest_path(packet,'NATIVE_SELECTION_V41_EVIDENCE.tar.gz')
        prefix=manifest_name.removesuffix('MANIFEST.json');manifest_raw=packet.read(manifest_name);manifest=decode(manifest_raw)
        check(manifest['schema']=='UDM_NATIVE_SELECTION_EVIDENCE_MANIFEST_V41'
              and manifest['source_commit']==EXPECTED_SOURCE and str(manifest['run_id'])==str(expected['scientific_run_id'])
              and str(manifest['run_attempt'])=='1','scientific manifest exact schema/source/run')
        check(manifest['mode']=='REPRODUCTION_OF_COMMITTED_PREOUTCOME_PROTOCOL','scientific manifest reproduction boundary')
        raw=packet.read(prefix+manifest['packet']['path'])
        check(manifest['packet']=={'path':'NATIVE_SELECTION_V41_EVIDENCE.tar.gz','sha256':sha(raw),'bytes':len(raw)},
              'scientific evidence packet exact digest/bytes')
        files,rows,_=tar_members(raw)
        actual_manifest={name:{'sha256':row['sha256'],'bytes':row['bytes']} for name,row in rows.items()}
        check(manifest['files']==actual_manifest and manifest['symlinks']=={},'scientific exact safe evidence inventory and every raw byte')
        check(manifest['archive_member_readback_verification']=={'status':'PASS_EXACT_MANIFEST_MEMBERS_AND_BYTES','members':len(files)},
              'scientific archive readback claim matches independent inventory')
        wanted={'CI_BOUNDARY.json','READINESS.json','CI_ASSESSMENT.json','ORIGINAL_METHOD_OBJECTS.json','source-packs/UDM_SOURCE.tar.gz'}
        check(set(files)==wanted,'only expected pre-bootstrap refusal evidence retained',actual=sorted(files))
        outer={}
        for info in packet.infolist():
            if info.is_dir():continue
            raw2=packet.read(info.filename);outer[info.filename]={'sha256':sha(raw2),'bytes':len(raw2)}
            logical=info.filename.removeprefix(prefix)
            if logical=='MANIFEST.json':continue
            wanted_record=manifest['packet'] if logical==manifest['packet']['path'] else manifest['files'].get(logical)
            check(wanted_record is not None and all(outer[info.filename][key]==wanted_record[key] for key in ('sha256','bytes')),
                  'every outer scientific file covered by exact manifest',path=info.filename)
        check(len(outer)==6,'exact six outer scientific files',actual=len(outer))
    out.mkdir(parents=True,exist_ok=False)
    (out/'MANIFEST.json').write_bytes(manifest_raw)
    (out/'OUTER_INVENTORY.json').write_text(json.dumps(outer,sort_keys=True,indent=2)+'\n')
    (out/'NESTED_INVENTORY.json').write_text(json.dumps(actual_manifest,sort_keys=True,indent=2)+'\n')
    for name,raw in files.items():
        if name.endswith('.tar.gz'):continue
        target=out/'evidence'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    return files,manifest


def combined_source(args,files,expected,check):
    scientific,scientific_rows,pax=tar_members(files['source-packs/UDM_SOURCE.tar.gz'])
    inventory=read(args.source_inventory)
    check(inventory['commit']==EXPECTED_SOURCE and sha(Path(args.source_inventory).read_bytes())==expected['source_inventory_sha256'],
          'independent exact c553 inventory identity')
    intended={name:row for name,row in inventory['files'].items() if name.startswith(OWNED)}
    check(scientific_rows==intended and len(scientific_rows)==expected['scientific_sourcepack_files'],
          'scientific source pack exact filtered owned scope bytes/modes',actual=len(scientific_rows),expected=len(intended))
    check(pax.get('comment')==EXPECTED_SOURCE,'scientific source pack Git commit PAX binding')
    previous_hash=hash_file(args.earlier_artifact)
    check(previous_hash==(expected['earlier_artifact_sha256'],expected['earlier_artifact_bytes']),
          'independent earlier full-source artifact digest/size',actual=previous_hash)
    if previous_hash!=(expected['earlier_artifact_sha256'],expected['earlier_artifact_bytes']):raise ValueError('earlier artifact identity mismatch')
    with zipfile.ZipFile(args.earlier_artifact) as packet:
        unique_zip(packet);name=_manifest_path(packet,'SOURCE.tar.gz');prefix=name.removesuffix('MANIFEST.json')
        manifest=decode(packet.read(name));old_raw=packet.read(prefix+'SOURCE.tar.gz')
        check(manifest['source_commit']==expected['earlier_source_commit'] and str(manifest['run_id'])=='38954969411'
              and manifest['files']['SOURCE.tar.gz']==sha(old_raw),'earlier exact source pack manifest/run/commit')
        earlier,earlier_rows,earlier_pax=tar_members(old_raw)
    old_inventory=read(args.earlier_inventory)
    check(old_inventory['commit']==expected['earlier_source_commit'] and earlier_rows==old_inventory['files']
          and len(earlier_rows)==expected['earlier_sourcepack_files'],'earlier complete1666 raw source inventory/modes')
    check(earlier_pax.get('comment')==expected['earlier_source_commit'],'earlier full source Git PAX binding')
    conflicts=[name for name in set(earlier_rows)&set(scientific_rows) if earlier_rows[name]!=scientific_rows[name]]
    check(not conflicts,'source pack overlap byte/mode preservation',conflicts=conflicts)
    combined=dict(earlier);combined.update(scientific)
    combined_rows=dict(earlier_rows);combined_rows.update(scientific_rows)
    check(combined_rows==inventory['files'] and len(combined_rows)==expected['full_source_files'],
          'two independently hashed artifact source packs provide exact complete2156 c553 source closure')
    missing=sorted(set(earlier_rows)-set(scientific_rows))
    check(len(missing)==expected['earlier_full_source_files_omitted_from_scientific_pack'],
          'scientific standalone source delivery remains explicitly partial',omitted_prior_files=len(missing))
    preservation={}
    for label,path in (('base',args.base_inventory),('v3',args.v3_inventory),('admission',args.earlier_inventory)):
        prior=read(path)
        changes=[name for name,row in prior['files'].items() if combined_rows.get(name)!=row]
        check(not changes,'all prior '+label+' source files preserved byte-for-byte with Git modes',changes=changes)
        preservation[label]={'commit':prior['commit'],'files':len(prior['files']),'changed_or_missing':changes,'inventory_sha256':sha(Path(path).read_bytes())}
    for name,digest in expected['committed_record_sha256'].items():
        check(name in combined and sha(combined[name])==digest,'pre-artifact committed scientific record pin',path=name)
    return combined,{'full_source_files':len(combined_rows),'scientific_owned_pack_files':len(scientific_rows),
                     'earlier_full_pack_files':len(earlier_rows),'scientific_standalone_omitted_prior_files':missing,
                     'combined_full_closure':combined_rows==inventory['files'],'overlap_conflicts':conflicts,
                     'preservation':preservation,'scientific_sourcepack_sha256':sha(files['source-packs/UDM_SOURCE.tar.gz']),
                     'earlier_sourcepack_sha256':sha(old_raw)}


def readiness(files,manifest,source,expected,check):
    ready=decode(files['READINESS.json']);assess=decode(files['CI_ASSESSMENT.json']);boundary=decode(files['CI_BOUNDARY.json'])
    protocol=decode(source[PREFIX+'FRONTIER_PROTOCOL.json'])
    check(protocol['schema']=='UDM_NATIVE_FRONTIER_PROTOCOL_V41' and protocol['state']=='PREPARED_NOT_FROZEN',
          'committed frontier remains unready, with no outcome-selected finalization')
    check(ready=={'schema':'UDM_COMMITTED_FRONTIER_CI_READINESS_V41','status':expected['readiness_status'],
                 'target_source_accessed':False,'new_admission_screening_performed':False,
                 'smallest_obstruction':expected['readiness_obstruction']},'exact expected scientific readiness RED')
    check(assess['schema']=='UDM_NATIVE_SELECTION_CI_ASSESSMENT_V41' and assess['status']==expected['scientific_assessment']
          and assess['mode']=='REPRODUCTION_OF_COMMITTED_PREOUTCOME_PROTOCOL'
          and all(assess['G'+str(i)]=='UNKNOWN' for i in range(2,7))
          and assess['actual_coding_agent_in_CI'] is False and assess['agent_status']=='PENDING_ACTUAL_EXECUTION',
          'scientific assessment retains G2-G6 UNKNOWN and no CI coding-agent execution')
    check(not any(key in assess for key in ('native_status','native_verdicts','measured_conditions','measured_future_results','machine_costs')),
          'assessment contains no manufactured native/baseline/comparator result')
    check(boundary['schema']=='UDM_NATIVE_SELECTION_CI_BOUNDARY_V41' and boundary['source_commit']==EXPECTED_SOURCE
          and str(boundary['run_id'])==str(expected['scientific_run_id']) and str(boundary['run_attempt'])=='1'
          and boundary['mode']=='REPRODUCTION_OF_COMMITTED_PREOUTCOME_PROTOCOL'
          and boundary['new_metadata_selection'] is False and boundary['actual_coding_agent_in_CI'] is False
          and boundary['raw_independent_screening_future_reports_required'] is False and boundary['G4']=='UNKNOWN',
          'CI boundary honestly describes reproduction with no new selection/agent/native claim')
    objects=decode(files['ORIGINAL_METHOD_OBJECTS.json'])
    check(objects['objects']==[] and len(objects['errors'])==3
          and {row['source'] for row in objects['errors']}==set(expected['method_source_errors'])
          and all(row['error']=='ValueError: original source object not available or hash differs' for row in objects['errors'])
          and manifest['archive_errors']==objects['errors'],
          'all three expected missing original method source objects retained as explicit errors; no full method artifact claim')
    check({name for name in files if name.startswith('source-packs/')}=={'source-packs/UDM_SOURCE.tar.gz'},
          'no fabricated external component source packs after early readiness failure')
    refusal=source[PREFIX+'FINALIZATION_REFUSAL.log'].decode()
    check('screening shortfall; no outcome-selected replacement permitted' in refusal
          and 'Traceback' in refusal,'actual unchanged finalizer refusal retained')
    return {'readiness':ready,'assessment':assess,'method_source_objects':0,'method_source_errors':objects['errors'],
            'method_artifact_status':'PARTIAL_THREE_ORIGINAL_METHOD_SOURCE_OBJECTS_UNAVAILABLE',
            'native_baseline_ledger_agent_comparators':'NOT_EXECUTED_NATIVE_OBLIGATION_NOT_ADMITTED'}


def payload_checks(source,expected,check):
    prefix=PREFIX+'SCREENING_INDEPENDENT_AUDIT/'
    base=prefix+'archive/'+PACKET_BASE
    raw=source[base+'.tar.gz'];descriptor=decode(source[base+'.descriptor.json'])
    manifest_raw=source[base+'.manifest.json'];manifest=decode(manifest_raw)
    verification_raw=source[base+'.verification.json'];verification=decode(verification_raw)
    exclusions_raw=source[base+'.exclusions.json'];exclusions=decode(exclusions_raw)
    check(sha(raw)==expected['screening_archive_sha256'] and len(raw)==expected['screening_archive_bytes'],
          'committed sealed screening payload exact pre-artifact digest/size')
    check(descriptor['schema']=='UDM_V41_SCREENING_COMPLETE_EVIDENCE_ARCHIVE'
          and descriptor['sha256']==sha(raw) and descriptor['size_bytes']==len(raw)
          and descriptor['manifest']['sha256']==sha(manifest_raw)
          and descriptor['verification']['sha256']==sha(verification_raw)
          and descriptor['exclusions']['sha256']==sha(exclusions_raw), 'screening descriptor exact archive/manifest/verification/exclusions binding')
    check(manifest['schema']=='UDM_V41_SCREENING_ARCHIVE_MANIFEST','screening member manifest schema')
    wanted={row['archive_path']:row for row in manifest['members']}
    check(len(wanted)==len(manifest['members'])==expected['screening_archive_members'],'screening declared member uniqueness/count')
    observed={};regular={};types=collections.Counter()
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as packet:
        for member in packet:
            name=safe(member.name,member.isdir())
            if name in observed:raise ValueError('duplicate screening archive member: '+name)
            row={'mode':member.mode}
            if member.isfile():
                value=packet.extractfile(member).read();regular[name]=value
                row.update(type='file',size=len(value),sha256=sha(value))
            elif member.isdir():row['type']='directory'
            elif member.issym():row.update(type='symlink',target=member.linkname)
            else:raise ValueError('unexpected screening member type: '+name)
            observed[name]=row;types[row['type']]+=1
            original=wanted.get(name,{})
            check(all(original.get(key)==value for key,value in row.items()),'every screening member exact mode/bytes/link target',path=name)
    check(set(observed)==set(wanted),'all screening manifest members present and none unlisted')
    check(types=={'file':expected['screening_archive_regular'],'symlink':expected['screening_archive_symlinks'],
                  'directory':expected['screening_archive_directories']},'exact screening regular/link/directory counts',actual=dict(types))
    check(manifest['regular_file_count']==types['file'] and manifest['symlink_count']==types['symlink']
          and manifest['directory_count']==types['directory']
          and manifest['regular_file_bytes']==sum(len(value) for value in regular.values()),'screening manifest byte/type totals independently recomputed')
    check(verification['schema']=='UDM_V41_SCREENING_ARCHIVE_REOPEN_VERIFICATION' and verification['status']=='PASS'
          and verification['archive_sha256']==sha(raw) and verification['archive_size_bytes']==len(raw)
          and verification['members']==len(observed) and not verification['failures']
          and verification['reopened_regular_files_checked']==types['file']
          and verification['reopened_symlinks_checked']==types['symlink']
          and verification['reopened_directories_checked']==types['directory'],'retained screening readback verification matches independent reopening')
    first='sealed/case-000/source-environment/metadata-source/README.rst'
    check(observed[first]['type']=='symlink' and observed[first]['target']=='docs/intro.rst',
          'first wcwidth obstruction is actual retained README.rst link, Git mode120000')
    check(exclusions['schema']=='UDM_V41_SCREENING_ARCHIVE_EXCLUSIONS'
          and exclusions['no_foreign_base_source_excluded'] is True
          and exclusions['all_foreign_git_objects_indexes_symlinks_gitlink_directories_retained'] is True,
          'screening exclusions remain explicit rather than deleting foreign refusal evidence')
    semantics=audit_screening(source,regular,check)
    return {'archive_sha256':sha(raw),'archive_bytes':len(raw),'members':len(observed),'member_types':dict(types),
            'symlinks_traversed_or_extracted':False,'semantics':semantics,'exclusions':exclusions}, observed


def ci_api(args,expected,check):
    run=read(args.run_json);job=read(args.job_json);artifacts=read(args.artifacts_json)
    check(run['id']==expected['scientific_run_id'] and run['head_sha']==EXPECTED_SOURCE and run['run_attempt']==1
          and run['status']=='completed' and run['conclusion']=='failure'
          and run['path']=='.github/workflows/udm-prospective-native-selection-v41.yml', 'exact retained API run is scientific RED')
    rows=[row for row in artifacts['artifacts'] if row['id']==expected['scientific_artifact_id']]
    check(len(rows)==1,'one exact scientific artifact in retained API record')
    artifact=rows[0]
    check(artifact['name']=='prospective-native-selection-v41-'+EXPECTED_SOURCE+'-1'
          and artifact['digest']=='sha256:'+expected['scientific_artifact_sha256']
          and artifact['size_in_bytes']==expected['scientific_artifact_bytes'] and artifact['expired'] is False
          and artifact['workflow_run']['id']==expected['scientific_run_id']
          and artifact['workflow_run']['head_sha']==EXPECTED_SOURCE,'retained scientific artifact API identity/digest')
    check(job['run_id']==expected['scientific_run_id'] and job['head_sha']==EXPECTED_SOURCE
          and job['status']=='completed' and job['conclusion']=='failure','retained CI job exact scientific failure source/run')
    def step(name):
        rows=[row for row in job['steps'] if row['name']==name]
        if len(rows)!=1:raise ValueError('unique expected CI step missing: '+name)
        return rows[0]
    ready=step('Require committed ready frontier and sealed public admission evidence')
    assess=step('Assess actual scientific result without promoting UNKNOWN or pending agent arms')
    archive=step('Archive exact source, original methods, native packets, states and all costs')
    upload=step('Run actions/upload-artifact@v4')
    check(ready['conclusion']==assess['conclusion']=='failure','readiness and scientific assessment genuinely RED')
    check(archive['conclusion']==upload['conclusion']=='success' and archive['number']>assess['number']>ready['number'],
          'always archival/upload succeeds after scientific refusal')
    skipped=[
        'Prepare both fresh runtimes using the unchanged qualified bootstrap',
        'Prepare the declared V41 profile and validate every runtime package before freeze',
        'Install real pinned component checkouts and original method objects',
        'Freeze fresh runner-local identities and exact committed source',
        'Execute native MSI V104 developmental selection and actual counterfactuals']
    for name in skipped:
        value=step(name)
        check(value['conclusion']=='skipped' and value['number']>ready['number'],
              'readiness refusal precedes skipped runtime/bootstrap/MSI/baseline/comparator work',step=name)
    later_checkouts=[row for row in job['steps'] if row['name']=='Run actions/checkout@v4' and row['number']>ready['number']]
    check(len(later_checkouts)==6 and all(row['conclusion']=='skipped' for row in later_checkouts),
          'all later external component/source checkouts skipped')
    return {'run_conclusion':run['conclusion'],'job_conclusion':job['conclusion'],
            'readiness_step':ready,'assessment_step':assess,'archive_step':archive,'upload_step':upload,
            'skipped_execution_steps':skipped,
            'record_sha256':{str(path):sha(Path(path).read_bytes()) for path in (args.run_json,args.job_json,args.artifacts_json)}}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact',type=Path,required=True);p.add_argument('--earlier-artifact',type=Path,required=True)
    p.add_argument('--source-inventory',type=Path,required=True);p.add_argument('--earlier-inventory',type=Path,required=True)
    p.add_argument('--base-inventory',type=Path,required=True);p.add_argument('--v3-inventory',type=Path,required=True)
    p.add_argument('--run-json',type=Path,required=True);p.add_argument('--job-json',type=Path,required=True)
    p.add_argument('--artifacts-json',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();start=time.monotonic();failures=[];checks=0;sections=[]
    def check(condition,label,**details):
        nonlocal checks
        checks+=1
        if not condition:failures.append({'check':label,**details})
    report={'schema':'UDM_V41_INDEPENDENT_SCIENTIFIC_REFUSAL_AUDIT_V1','status':'FAIL_INCOMPLETE_AUDIT',
            'source_commit':EXPECTED_SOURCE,'scientific_status':'RED_NO_ADMITTED_NATIVE_TASK',
            'native_baseline_or_comparator_execution':'NOT_EXECUTED_NATIVE_OBLIGATION_NOT_ADMITTED',
            'verdicts':{f'G{i}':'UNKNOWN' for i in range(2,7)},'failures':failures,'completed_sections':sections,
            'auditor_native_calls':0,'auditor_collection_calls':0,'auditor_git_calls':0,'auditor_network_calls':0,
            'artifact_code_executed':False}
    try:
        raw=(HERE/'EXPECTATIONS.json').read_bytes();check(sha(raw)==EXPECTED_SHA,'pre-artifact scientific refusal expectations pin')
        expected=decode(raw)
        files,manifest=scientific_envelope(args.artifact,expected,args.out,check);sections.append('envelope')
        source,report['source_closure']=combined_source(args,files,expected,check);sections.append('combined_source')
        report['readiness']=readiness(files,manifest,source,expected,check);sections.append('readiness')
        report['screening_payload'],members=payload_checks(source,expected,check);sections.append('screening')
        (args.out/'SCREENING_PAYLOAD_INVENTORY.json').write_text(json.dumps(members,sort_keys=True,indent=2)+'\n')
        report['ci_api']=ci_api(args,expected,check);sections.append('ci_order')
        check(hash_file(args.artifact)==(expected['scientific_artifact_sha256'],expected['scientific_artifact_bytes'])
              and hash_file(args.earlier_artifact)==(expected['earlier_artifact_sha256'],expected['earlier_artifact_bytes']),
              'both source artifacts unchanged throughout offline audit')
        if not failures and set(sections)=={'envelope','combined_source','readiness','screening','ci_order'}:
            report['status']='PASS_EXPECTED_SCIENTIFIC_REFUSAL_EVIDENCE_AUDIT'
    except Exception as error:
        failures.append({'check':'all required evidence parsed without exception','exception':type(error).__name__,'detail':str(error)})
    finally:
        args.out.mkdir(parents=True,exist_ok=True)
        report['checks']=checks;report['seconds']=time.monotonic()-start
        report['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        report['auditor_source_sha256']={path.name:sha(path.read_bytes()) for path in (Path(__file__),HERE/'screening_checks.py',HERE/'EXPECTATIONS.json') if path.is_file()}
        report['limits']=[
            'The scientific artifact alone carries a filtered source pack. Complete c553 source closure is established only by combining both independently hashed artifact packs; no standalone-full-source claim is made.',
            'Readiness stopped before runtime bootstrap, external method-source checkouts, native search, baseline, ledger, coding-agent or comparator execution. Three missing original method object errors are expected and remain visible; this is a partial original-method artifact.',
            'Native/collection zeros describe retained controller-local refusal records and skipped CI stages, not a global operating-system/network access audit.',
            'The retained screening packet audit checks metadata/refusal/source/runtime consistency and raw member integrity; it does not establish admitted native task behavior, learning, comparative benefit or G2-G6.',
            'No original project/controller/selector or artifact code was imported or executed by this audit. No Git, network, native or collection experiment was run.']
        (args.out/'AUDIT.json').write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n')
        print(json.dumps({'status':report['status'],'checks':checks,'sections':sections,'failures':failures,'seconds':report['seconds']},sort_keys=True))
    raise SystemExit(0 if report['status']=='PASS_EXPECTED_SCIENTIFIC_REFUSAL_EVIDENCE_AUDIT' else 1)


if __name__=='__main__':main()
