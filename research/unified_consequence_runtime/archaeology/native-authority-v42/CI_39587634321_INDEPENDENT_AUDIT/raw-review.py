"""Offline semantic audit of V42 readiness refusal and six committed screening cases.

The prior V41 byte/JSON helpers are reused unchanged. V42 schema, paths,
six-case expectations, and honest failed archival step are data adaptations.
Never invoke Git/network/native tests or execute artifact project code.
"""
import argparse, collections, datetime, hashlib, importlib.util, io, json
from pathlib import Path, PurePosixPath
import tarfile, time, xml.etree.ElementTree as ET, zipfile

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('raw_review_helpers',HERE/'raw-review-helpers.py')
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
PREFIX='research/unified_consequence_runtime/archaeology/native-authority-v42/'
ROOT='research/unified_consequence_runtime/'
EXPECTED_PIN='2dfbb63b80df669971ad37ae30608b702818fe974fcdf84406734ea94a33f942'

def safe(name):
    p=PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or str(p)!=name.rstrip('/') or '\\' in name:
        raise ValueError('noncanonical archive name '+name)
    return str(p)

def read_tar(stream,select):
    files={};inventory={}
    with tarfile.open(fileobj=stream,mode='r|gz') as t:
        for m in t:
            name=safe(m.name)
            if name in inventory:raise ValueError('duplicate tar name '+name)
            inventory[name]={'type':'file' if m.isfile() else 'directory' if m.isdir() else 'symlink' if m.issym() else 'unsupported','mode':m.mode,'size':m.size,'target':m.linkname if m.issym() else None}
            if m.isfile() and select(name):files[name]=t.extractfile(m).read()
    return files,inventory

def abs_payload(path):
    for old,new in [('/workspace/qualification/native-authority-v42-screening-sealed/','sealed/'),('/workspace/qualification/native-authority-v42-screening-controller/','controller/'),('/workspace/qualification/native-authority-v42-screening-requests/','requests/')]:
        if path.startswith(old):return new+path[len(old):]
    raise ValueError('unsupported absolute payload descriptor '+path)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifact',required=True,type=Path);p.add_argument('--metadata',required=True,type=Path);p.add_argument('--log',required=True,type=Path)
    a=p.parse_args();start=time.monotonic();checks=[];failures=[];sections={}
    def check(ok,label,**details):
        row={'check':label,'passed':bool(ok),**details};checks.append(row)
        if not ok:failures.append(row)
    def J(mapping,name):return h._read(mapping,name)
    expectation_raw=(HERE/'raw-review-expectations.json').read_bytes();expected=h._json(expectation_raw,'pre-artifact expectations')
    report={'schema':'UDM_V42_SCIENTIFIC_RAW_REFUSAL_REVIEW','status':'INCOMPLETE','source_commit':expected['source_commit'],'run_id':expected['run_id'],'checks':checks,'failures':failures,'sections':sections,'auditor_git_calls':0,'auditor_network_calls':0,'auditor_native_calls':0,'auditor_collection_calls':0,'artifact_project_code_executed':False,'fixture_symlinks_extracted_or_executed':False,'scientific_verdicts':{f'G{i}':'UNKNOWN' for i in range(2,7)}}
    try:
        check(h._sha(expectation_raw)==EXPECTED_PIN,'pre-artifact expectations exact pin')
        check(h._sha((HERE/'raw-review-helpers.py').read_bytes())==expected['copied_helper_sha256'],'unchanged reused prior V41 generic helpers')
        wanted_source=set(expected['source_record_sha256'])|{ROOT+n for n in ['native_source_v42.py','native_admission_v42.py','native_execution_v42.py','native_environment_v42.py','native_environment_selection_v41.py']}
        with zipfile.ZipFile(a.artifact) as z:
            manifest=J({n:z.read(n) for n in z.namelist() if n=='MANIFEST.json'},'MANIFEST.json')
            evidence,inv=read_tar(z.open('NATIVE_SELECTION_V42_EVIDENCE.tar.gz'),lambda n:True)
        check(manifest['source_commit']==expected['source_commit'] and int(manifest['run_id'])==expected['run_id'] and str(manifest['run_attempt'])=='1','evidence exact scientific source/run/attempt')
        source_raw=evidence.pop('source-packs/UDM_SOURCE.tar.gz')
        source,source_inv=read_tar(io.BytesIO(source_raw),lambda n:n in wanted_source or n.startswith(PREFIX+'SCREENING_EVIDENCE/') and n.endswith('.tar.gz'))
        del source_raw
        for name,digest in expected['source_record_sha256'].items():check(h._sha(source[name])==digest,'pre-artifact committed source record pin',path=name)
        # Source closure, archive inventories/modes, API artifact hash and raw CI indexes
        # are independently owned by the enclosing parent audit.
        ready=J(evidence,'READINESS.json');assessment=J(evidence,'CI_ASSESSMENT.json');boundary=J(evidence,'CI_BOUNDARY.json');objects=J(evidence,'ORIGINAL_METHOD_OBJECTS.json')
        protocol=J(source,PREFIX+'FRONTIER_PROTOCOL.json')
        check(protocol['schema']=='UDM_NATIVE_FRONTIER_PROTOCOL_V42' and protocol['state']=='PREPARED_NOT_FROZEN' and protocol['screening'] is None,'committed frontier remains unready with no outcome-selected finalization')
        check(ready=={'schema':'UDM_COMMITTED_FRONTIER_CI_READINESS_V42','status':expected['readiness_status'],'target_source_accessed':False,'new_admission_screening_performed':False,'smallest_obstruction':expected['readiness_obstruction']},'exact actual readiness refusal')
        check(assessment=={'schema':'UDM_NATIVE_SELECTION_CI_ASSESSMENT_V42','mode':'REPRODUCTION_OF_COMMITTED_PREOUTCOME_PROTOCOL','status':expected['scientific_assessment'],**{f'G{i}':'UNKNOWN' for i in range(2,7)},'actual_coding_agent_in_CI':False,'agent_status':'PENDING_ACTUAL_EXECUTION'},'scientific assessment exact UNKNOWN and pending arms with no manufactured result')
        check(boundary['schema']=='UDM_NATIVE_SELECTION_CI_BOUNDARY_V42' and boundary['source_commit']==expected['source_commit'] and int(boundary['run_id'])==expected['run_id'] and str(boundary['run_attempt'])=='1','CI boundary exact source/run')
        check(boundary['mode']=='REPRODUCTION_OF_COMMITTED_PREOUTCOME_PROTOCOL' and boundary['new_metadata_selection'] is False and boundary['raw_independent_screening_future_reports_required'] is False and boundary['actual_coding_agent_in_CI'] is False and boundary['G4']=='UNKNOWN','CI boundary reproduction and no new selection or coding agent')
        check(objects['objects']==[] and len(objects['errors'])==3 and {x['source'] for x in objects['errors']}==set(expected['method_source_errors']) and all(x['error']=='ValueError: original source object not available or hash differs' for x in objects['errors']),'three unavailable original method objects honestly retained')
        check(manifest['archive_errors']==objects['errors'],'manifest preserves original method-source archival errors')
        check({n for n in inv if n.startswith('source-packs/')}=={'source-packs/UDM_SOURCE.tar.gz'},'only owned source pack available after pre-bootstrap readiness refusal')
        check(not any(n.startswith(('run/','runtime-bootstrap/','declared-modern-profile/')) or n in ['FREEZE.json','NATIVE_EXIT_CODE.txt','native-selection.log','BARE_RUNTIME_PATHS.json','RUNTIME_PATHS.json','RUNTIME_PROFILE_VALIDATION.json','COMPONENT_COMMITS.json'] for n in inv),'no runtime-bootstrap/native/comparator/agent result fabricated after refusal')
        final=J(source,PREFIX+'FINALIZATION_REFUSAL_RECEIPT.json');final_log=source[PREFIX+'FINALIZATION_REFUSAL.log'].decode()
        check(final['returncode']==1 and final['status']=='UNKNOWN_SCREENING_SHORTFALL' and final['protocol_bytes_unchanged'] is True and final['learner_or_comparator_executed'] is False,'actual frozen finalizer refuses screening shortfall without executing learner or comparator')
        check(h._sha(source[PREFIX+'FINALIZATION_REFUSAL.log'])==final['log_sha256'] and 'screening shortfall; no outcome-selected replacement permitted' in final_log and 'Traceback' in final_log,'finalizer raw refusal log and digest retained')
        scientific=J(source,PREFIX+'SCIENTIFIC_RESULT.json')
        check(all(str(scientific['verdicts'][f'G{i}']).startswith('UNKNOWN') for i in range(2,7)) and all(x['status']=='NOT_EXECUTED' for x in scientific['comparisons'].values()),'committed scientific result leaves every G2-G6 and three unexecuted comparison arms honest')
        check(scientific['controller_historical_full_file_identity']=='UNKNOWN_NOT_SUPPLIED_IN_BOUNDED_EVIDENCE','historical full controller file identity remains explicitly unknown')
        check(scientific['prospective_frontier']['admitted']==scientific['prospective_frontier']['eligible_count']==scientific['prospective_frontier']['native_calls']==0 and scientific['prospective_frontier']['collection_calls']==1 and scientific['prospective_frontier']['replacements_or_retries'] is False,'committed scientific result preserves zero admissions and charged single collection')
        sections['readiness']={'readiness':ready,'assessment':assessment,'method_objects':objects,'scientific_comparisons':scientific['comparisons'],'scientific_verdicts':scientific['verdicts'],'historical_controller_full_file_identity':scientific['controller_historical_full_file_identity']}
        # Read retained raw screening data as regular members only. The enclosing
        # audit separately verifies every shard member against exact committed manifests.
        descriptor=J(source,PREFIX+'SCREENING_EVIDENCE/native-authority-v42-screening-raw-evidence.descriptor.json')
        payload={};payload_inv={}
        for shard in descriptor['shards']:
            name=PREFIX+'SCREENING_EVIDENCE/'+Path(shard['path']).name
            raw=source.pop(name);check(h._sha(raw)==shard['sha256'] and len(raw)==shard['size_bytes'],'raw scientific screening shard exact digest/size',path=name)
            files,rows=read_tar(io.BytesIO(raw),lambda n:'/.git/' not in n)
            check(not (set(payload_inv)&set(rows)),'screening shards contain disjoint exact members')
            payload.update(files);payload_inv.update(rows)
        authority=J(source,PREFIX+'SCREENING_AUTHORITY.json');authority_sha=h._sha(source[PREFIX+'SCREENING_AUTHORITY.json'])
        pool=J(source,PREFIX+'FROZEN_POOL.json');meter=J(source,PREFIX+'SCREENING_METER.json');public=J(source,PREFIX+'PUBLIC_SCREENING_SUMMARY.json');envelopes=J(source,PREFIX+'SCREENING_ENVELOPES.json');audit=J(source,PREFIX+'SCREENING_AUDIT.json')
        check(len(pool['pool'])==len(meter['cases'])==len(public['cases'])==len(envelopes)==6,'exact six committed cases with no replacement')
        check(public==J(payload,'controller/PUBLIC_SCREENING_SUMMARY.json') and public['global_screening_meter']==meter and meter==J(payload,'sealed/SCREENING_METER.json'),'committed public summary and meter equal retained originals')
        check(meter['pending'] is None and meter['accounting_complete'] is True and meter['native_calls']==0 and meter['collection_calls']==1 and meter['authority_sha256']==authority_sha,'complete global meter charges one collection and zero native calls')
        check(public['all_cases_completed_once_in_order'] is True and public['all_cli_returncodes_zero'] is True and public['eligible_count']==0 and public['retries_performed'] is False and public['source_and_native_test_changes_performed'] is False,'public zero-admission once-only summary without retries or source repair')
        controller=J(payload,'controller/CONTROLLER_RECEIPT.json');cases=[];all_costs=[]
        typed_expected={key:h._sha(source[ROOT+name]) for key,name in [('source_sha256','native_source_v42.py'),('admission_sha256','native_admission_v42.py'),('execution_sha256','native_execution_v42.py'),('environment_sha256','native_environment_v42.py'),('inherited_selection_sha256','native_environment_selection_v41.py')]}
        for exp in expected['expected_cases']:
            i=exp['index'];base=f'sealed/case-{i:03d}';report_raw=payload[base+'/SCREENING_CASE.json'];case=J(payload,base+'/SCREENING_CASE.json');request=J(payload,f'requests/request-{i:03d}.json');envelope=J(payload,base+'/SCREENING_ENVELOPE.json');setup=J(payload,base+'/source-environment/admission-v42.json');old=J(payload,base+'/source-environment/admission-v3.json')
            check(h._sha(report_raw)==exp['report']['sha256'] and case['spec_sha256']==exp['spec_sha256'] and case['repository']==exp['repository'],'exact pre-artifact report/spec/repository',case=i)
            check(request['pool_index']==i and request['spec']==pool['pool'][i] and request['protocol_binding']==authority_sha and h._fp(request['spec'])==case['spec_sha256'],'ordered request binds exact committed pool spec and authority',case=i)
            check(envelope==envelopes[i]==public['cases'][i]['envelope'] and envelope['sealed_report']==exp['report'],'sealed/public/committed envelope is exact',case=i)
            check(envelope['eligible'] is False and envelope['status']=='UNKNOWN_ADMISSION_SCREENING' and envelope['costs']==exp['costs'] and envelope['screening_mode']=='ADMISSION_ONLY_NO_CATALOG_OR_CANDIDATE_SEARCH','public envelope remains admission-only refusal with exact costs',case=i)
            check(case['eligible'] is False and case['accounting_complete'] is True and case['screening_mode']=='ADMISSION_ONLY_NO_CATALOG_OR_CANDIDATE_SEARCH' and case['costs']==[],'sealed case cannot assert candidate/native/scientific success',case=i)
            check(case['setup']==setup and setup==dict(old,schema='UDM_SOURCE_ENVIRONMENT_ADMISSION_V42',typed_source_operation=typed_expected),'V42 admission receipt is exact preserved V3 result plus typed source wrapper',case=i)
            reason=case.get('reason',setup.get('reason'))
            check(reason==exp['refusal_category'],'raw sealed refusal matches declared category',case=i,reason=reason)
            check(case['controller_attempts']==meter['cases'][i]['costs']=={'native_calls':0,'collection_calls':int(i==0),'subprocess_attempts':int(i==0)},'raw per-case attempted launch counts match global meter',case=i)
            check(meter['cases'][i]['report']==exp['report'] and meter['cases'][i]['spec_sha256']==exp['spec_sha256'] and meter['cases'][i]['accounting_complete'] is True,'meter exact report binding and accounting closure',case=i)
            receipt=J(payload,f'controller/case-{i:03d}.CONTROLLER_RECEIPT.json');attempted=J(payload,f'controller/case-{i:03d}.ATTEMPTED.json')
            check(receipt==controller['cases'][i] and receipt['index']==i and receipt['returncode']==0 and all(receipt[k]==v for k,v in attempted.items()),'once-only original launch receipt and successful CLI return',case=i)
            check('--screen-spec' in receipt['command'] and '--repo' not in receipt['command'] and '--freeze' not in receipt['command'] and receipt['command'].count('--screen-spec')==1,'original command only admission screening entrypoint',case=i)
            check(h._finite(case['total_wall_seconds']) and case['total_wall_seconds']>=setup['total_wall_seconds'] and receipt['wall_seconds']>=case['total_wall_seconds'],'retained nonnegative case/setup/controller timing',case=i)
            for cost in setup['costs']:
                check(h._finite(cost['seconds']) and cost.get('native_calls',0)==0,'setup costs nonnegative and no native execution imputed',case=i,phase=cost['phase'])
                if 'log' in cost:check(h._sha(payload[abs_payload(cost['log'])])==cost['log_sha256'],'every original setup command log digest retained',case=i,phase=cost['phase'])
            all_costs.extend(setup['costs'])
            if i:
                check(case['status']=='UNKNOWN_ENVIRONMENT_SELECTION' and not case['partial_native_reports'] and setup['runtime'] is None and setup['setup'] is None and setup['selection']['selected_profile'] is None,'environment refusal precedes provisioning and all native/collection work',case=i)
            else:
                check(case['status']=='UNKNOWN_ADMISSION_SCREENING' and setup['status']=='PREPARED' and len(case['partial_native_reports'])==1,'case000 attempted original native collection once after setup')
            cases.append({'index':i,'repository':case['repository'],'reason':reason,'controller_attempts':case['controller_attempts'],'wall_seconds':case['total_wall_seconds'],'setup_status':setup['status']})
        check([r['index'] for r in controller['cases']]==list(range(6)) and sum(c['controller_attempts']['collection_calls'] for c in cases)==1 and sum(c['controller_attempts']['native_calls'] for c in cases)==0,'complete ordered six-case launch accounting')
        check(abs(sum(c['wall_seconds'] for c in cases)-public['screening_case_wall_seconds_sum'])<1e-9,'independently summed case wall equals public cost summary')
        check(abs(sum(x['seconds'] for x in all_costs)-audit['costs']['sum_setup_phase_seconds'])<1e-9,'independently summed setup phase costs equal committed audit')
        case0=J(payload,'sealed/case-000/SCREENING_CASE.json');setup=case0['setup'];raw=J(payload,'sealed/case-000/collection/report.json');checked=J(payload,'sealed/case-000/collection/checked-report.json');xml=ET.fromstring(payload['sealed/case-000/collection/native.xml']);tests=list(xml.iter('testcase'));errors=[x.find('error') for x in tests if x.find('error') is not None]
        controller_fields={'process_exit_code','timeout','source_mutations','unexpected_imports','costs'}
        check(raw=={k:v for k,v in checked.items() if k not in controller_fields},'raw/checked collection producer bytes agree')
        check(checked['mode']=='collect' and checked['exit_code']==checked['process_exit_code']==2 and checked['timeout'] is False and checked['costs']['collection_calls']==1 and checked['costs']['native_calls']==0,'actual single collection exited2 and ran no native test')
        check(len(checked['collected_test_nodes'])==61 and len(checked['collection_errors'])==34 and len(tests)==len(errors)==34 and not checked['reports'],'raw collection and JUnit independently show61collected and34collection errors with no executed call reports')
        exact_exception="ModuleNotFoundError: No module named 'chardet._version'"
        check(all(exact_exception in (x.text or '') for x in errors),'every retained JUnit collection error is missing original chardet generated version module')
        check(exact_exception.encode() in payload['sealed/case-000/collection/stdout.log'] and payload['sealed/case-000/collection/stderr.log']==b'','raw stdout retains actual missing-generated-module traceback')
        manifest=J(payload,'sealed/case-000/collection/tracked-source-manifest.json');version='src/chardet/_version.py';native='sealed/case-000/source-environment/native/'
        check(version not in {r['path'] for r in manifest} and native+'source/'+version not in payload_inv and native+'source/'+version not in payload,'generated version absent from exact tracked source world')
        build=payload[native+'base-build/'+version];installed=payload[native+'venv/lib/python3.12/site-packages/chardet/_version.py'];wheel_desc=audit['first_obstruction']['evidence']['native_wheel'];wheel=payload[abs_payload(wheel_desc['path'])]
        with zipfile.ZipFile(io.BytesIO(wheel)) as w:generated=w.read('chardet/_version.py')
        check(build==installed==generated and h._sha(build)=='65de830ef24719bc053dfe3334f40eef851fd7aa25e4a29f27b618c2ffd68a08' and len(build)==558,'original baseline build wheel and installed generated version bytes identical')
        check(h._sha(wheel)==wheel_desc['sha256'] and len(wheel)==wheel_desc['bytes'] and wheel_desc['synthetic_version'] is False,'original baseline wheel retained without synthetic version')
        pyproject=payload[native+'source/pyproject.toml'].decode();init=payload[native+'source/src/chardet/__init__.py'].decode();gitignore=payload[native+'source/.gitignore'].decode()
        check('from chardet._version import __version__' in init and 'src/chardet/_version.py' in pyproject and 'hatch' in pyproject and '_version.py' in gitignore,'original source import and Hatch VCS generated-artifact configuration explain refusal')
        check('[tool.pytest]' in pyproject and '[dependency-groups]' in pyproject and 'pytest>=9.0.2' in pyproject,'additional frozen config/dependency grammar scope limits retained honestly')
        check(all(not n.endswith('/receipt.json') and not n.endswith('/admission-certificate.json') for n in payload_inv),'no certificate or native PASS/FAIL receipt fabricated from failed admission collection')
        attestation=J(source,PREFIX+'ORIGINAL_SCREENING_ACTOR_BOUNDARY_ATTESTATION.json')
        check(attestation==J(payload,'controller/ORIGINAL_SCREENING_ACTOR_BOUNDARY_ATTESTATION.json') and attestation['independent_screener'] is True and attestation['global_access_proof'] is False,'original screener actor attestation retained with bounded non-global access scope')
        check(all(attestation[k] is False for k in ['learner_future_source_accessed','search_or_policy_outcomes_accessed','native_test_reruns_or_case_retries_performed','native_tests_rewritten','new_task_search_performed','source_repairs_performed','candidate_or_catalog_generation_invoked','coding_agent_comparator_role_performed']),'bounded actor attestation excludes learner exposure, rescreening, repair or comparator work')
        sections['screening']={'cases':cases,'collection_calls':1,'native_calls':0,'eligible':0,'raw_collection_errors':len(errors),'collected_test_nodes':len(checked['collected_test_nodes']),'first_exception':exact_exception,'generated_build_sha256':h._sha(build),'generated_build_bytes':len(build),'historical_controller_full_file_identity':scientific['controller_historical_full_file_identity'],'retained_helper_corrections':audit['audit_helper_negatives']}
        # Retained provider API and raw CI logs establish the actual failed and
        # skipped workflow stages; no API request occurs in this audit.
        paths={k:sorted(a.metadata.glob('*-'+k+'.json'))[-1] for k in ['run','jobs','artifacts']};api={k:h._json(v.read_bytes(),str(v)) for k,v in paths.items()};run=api['run'];job=api['jobs']['jobs'][0]
        check(run['id']==expected['run_id'] and run['head_sha']==expected['source_commit'] and run['run_attempt']==1 and run['status']=='completed' and run['conclusion']=='failure' and run['path']=='.github/workflows/udm-prospective-native-selection-v42.yml','retained CI API exact scientific RED')
        check(job['run_id']==expected['run_id'] and job['head_sha']==expected['source_commit'] and job['conclusion']=='failure','retained job exact source/run and failure')
        def step(name):
            rows=[s for s in job['steps'] if s['name']==name]
            if len(rows)!=1:raise ValueError('expected unique CI step '+name)
            return rows[0]
        ready_step=step('Require committed ready frontier and sealed public admission evidence');assess_step=step('Assess actual scientific result without promoting UNKNOWN or pending agent arms');archive_step=step('Archive exact source, original methods, native packets, states and all costs');upload_step=step('Run actions/upload-artifact@v4')
        check(ready_step['conclusion']==assess_step['conclusion']==archive_step['conclusion']=='failure' and upload_step['conclusion']=='success','readiness/assessment/partial archival genuinely RED, upload successful')
        check(ready_step['number']<assess_step['number']<archive_step['number']<upload_step['number'],'scientific refusal precedes assessment, honest partial archival and upload')
        skipped=[s for s in job['steps'] if ready_step['number']<s['number']<assess_step['number']]
        check(len(skipped)==11 and all(s['conclusion']=='skipped' for s in skipped) and sum(s['name']=='Run actions/checkout@v4' for s in skipped)==6,'all11runtime/component/freeze/native stages skipped after readiness RED')
        log=a.log.read_bytes()
        for text in [expected['readiness_obstruction'],'UNKNOWN_NO_COMPLETE_NATIVE_RESULT','Source or index archival authority incomplete; retained failure evidence']:
            check(text.encode() in log,'raw CI job log preserves actual refusal/error',text=text)
        sections['ci']={'readiness_step':ready_step,'assessment_step':assess_step,'archive_step':archive_step,'upload_step':upload_step,'skipped_stage_count':len(skipped),'retained_api_paths':{k:str(v) for k,v in paths.items()},'raw_job_log':{'path':str(a.log),'sha256':h._sha(log),'bytes':len(log)}}
        report['status']='PASS_EXPECTED_SCIENTIFIC_REFUSAL_RAW_REVIEW' if not failures else 'OBSTRUCTED'
    except Exception as error:
        failures.append({'check':'semantic audit completed without parser/helper exception','passed':False,'exception':type(error).__name__,'detail':str(error)})
        report['status']='OBSTRUCTED'
    finally:
        report['check_count']=len(checks);report['seconds']=time.monotonic()-start;report['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['limits']=expected['limits']
        report['auditor_files_sha256']={n:h._sha((HERE/n).read_bytes()) for n in ['raw-review.py','raw-review-helpers.py','raw-review-expectations.json']}
        (HERE/'raw-review.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
        text=f"{report['status']}: {len(checks)} checks; {len(failures)} issues. CI readiness RED before bootstrap; three original method objects unavailable and honest archival RED. Original six committed admission screenings: zero admitted, one collection, zero native executions; missing Hatch VCS generated chardet/_version.py caused 34 JUnit collection errors. No learner, baseline, ledger or coding-agent arm executed; G2-G6 UNKNOWN.\n"
        (HERE/'raw-review.txt').write_text(text);print(text)
        if failures:print(json.dumps(failures,indent=2))
    return 0 if not failures else 1

if __name__=='__main__':raise SystemExit(main())
