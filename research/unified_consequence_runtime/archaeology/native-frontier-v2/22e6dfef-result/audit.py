"""Read-only archive audit: stdlib only; does not execute native task code."""
import argparse,base64,collections,gzip,hashlib,io,json,math,pathlib,re,subprocess,tarfile,time,zipfile
import xml.etree.ElementTree as ET


def digest(raw): return hashlib.sha256(raw).hexdigest()
def canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def fingerprint(value): return digest(canonical(value).encode())
def require(condition,description):
    if not condition: raise ValueError(description)
def safe_name(name):
    p=pathlib.PurePosixPath(name)
    require(not p.is_absolute() and '..' not in p.parts and '\\' not in name,'unsafe archive path: '+name)
    return name

def tar_files(raw):
    result={}
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:*') as archive:
        for member in archive.getmembers():
            safe_name(member.name)
            if member.isdir(): continue
            require(member.isfile(),'nonregular archive member: '+member.name)
            require(member.name not in result,'duplicate archive member: '+member.name)
            result[member.name]=archive.extractfile(member).read()
    return result

def junit(raw):
    root=ET.fromstring(raw)
    cases=list(root.iter('testcase'))
    counts={'tests':len(cases),'failures':0,'errors':0,'skipped':0,'passed':0}
    for case in cases:
        bad=False
        for kind in ('failure','error','skipped'):
            if case.find(kind) is not None:
                counts[{'failure':'failures','error':'errors','skipped':'skipped'}[kind]]+=1;bad=True
        if not bad:counts['passed']+=1
    return counts

def packet(value):
    raw={key:base64.b64decode(val,validate=True) for key,val in value['packet'].items()}
    require(value['packet_sha256']=={key:digest(val) for key,val in raw.items()},'packet digest differs')
    checked=json.loads(raw['checked-report.json']);producer=json.loads(raw['report.json'])
    controller={'process_exit_code','timeout','source_mutations','unexpected_imports','costs'}
    require(producer=={k:v for k,v in checked.items() if k not in controller},'raw producer and checked reports differ')
    return raw,checked

def source_identity(files,manifest):
    require(set(files)=={row['path'] for row in manifest},'source archive file universe differs')
    tree={}
    for row in manifest:
        name=row['path'];raw=files[name]
        blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        require(blob==row['blob'] and digest(raw)==row['sha256'],'source blob identity differs: '+name)
        branch=tree
        parts=name.split('/')
        for part in parts[:-1]:branch=branch.setdefault(part,{})
        branch[parts[-1]]=(row['mode'],blob)
    def git_tree(branch):
        raw=b''
        for name,value in sorted(branch.items(),key=lambda row:row[0]+('/' if isinstance(row[1],dict) else '')):
            mode,blob=('40000',git_tree(value)) if isinstance(value,dict) else value
            raw+=mode.encode()+b' '+name.encode()+b'\0'+bytes.fromhex(blob)
        return hashlib.sha1(b'tree '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    return {'git_tree':git_tree(tree),'tracked_tree_sha256':fingerprint(manifest),'file_count':len(files)}

def check_native_packet(value, contract, authority, certificate, policy, candidate, source, tracked, files):
    raw,data=packet(value)
    require(value['execution']==data,'native receipt differs from raw checked report')
    require(json.loads(raw['tracked-source-manifest.json'])==tracked,'native source manifest differs')
    expected=dict(files)
    for row in candidate['replacements']:
        require(digest(files[row['path']])==row['original_sha256'],'candidate original bytes differ')
        expected[row['path']]=row['replacement'].encode()
    for row in data['test_items']+data['import_manifest']:
        require(row['path'] in expected and digest(expected[row['path']])==row['sha256'],'native protected/imported source bytes differ')
    for key,obj in [('contract',contract),('authority',authority),('certificate',certificate),('policy',policy),('candidate',candidate)]:
        require(value[key+'_sha256']==fingerprint(obj),'native '+key+' binding differs')
    require(value['runner_sha256']==digest(source['research/unified_consequence_runtime/native_execution_v2.py']),'native verifier differs from qualified source')
    require(value['admission_revision']=='2.1','native receipt revision differs')
    require(value['environment']==certificate['environment'] and fingerprint(value['environment'])==contract['environment_sha256'],'native executable environment differs')
    require(value['plugins']==certificate['plugins'] and data['pytest_import']==value['environment']['pytest_import'],'native plugin/pytest identity differs')
    counts=junit(raw['native.xml']);require(counts==value['junit'],'native JUnit count differs')
    events=certificate['collection']['collected_test_nodes'];selected=certificate['collection']['selected_test_nodes']
    exact=(data['collected_test_nodes']==events and data['selected_test_nodes']==selected
        and data['test_items']==certificate['collection']['test_items']
        and data['plugin_manifest']==certificate['collection']['plugin_manifest'])
    calls=[row for row in data['reports'] if row['when']=='call'];failed=[row['nodeid'] for row in calls if row['outcome']=='failed']
    violations={key:len(data.get(key,[])) for key in ('deselected_test_nodes','collection_errors','source_mutations','unexpected_imports','external_project_imports','changed_test_code','plugin_violations')}
    if value['status'] in ('PASS_NATIVE','FAIL_NATIVE'):
        require(exact and not any(violations.values()),'closed native result lacks exact source/collection')
        require([row['nodeid'] for row in calls]==selected and counts['tests']==len(selected),'closed native result omits original assertions')
        require(not any(row.get('wasxfail') or row['outcome']=='skipped' for row in data['reports']),'closed native result contains xfail/skip')
        for phase in ('setup','teardown'):
            rows=[row for row in data['reports'] if row['when']==phase]
            require([row['nodeid'] for row in rows]==selected and all(row['outcome']=='passed' for row in rows),'closed native phase incomplete')
    return {'status':value['status'],'selected':len(selected),'calls':len(calls),'junit':counts,
        'exact_original_orders_and_code':exact,'negative_violations':violations,'failed_nodes':failed,
        'protected_failed_nodes':[node for node in failed if any(node==p or node.startswith(p+'[') or node.startswith(p+'::') for p in authority['required_test_nodes'])],
        'costs':value['costs'],'native_horizon_seconds':data['costs']['horizon_seconds']}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zip',required=True);parser.add_argument('--provider',required=True)
    parser.add_argument('--run',required=True);parser.add_argument('--repo',default='/workspace/udm-v54');parser.add_argument('--out',required=True)
    args=parser.parse_args();started=time.monotonic();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    provider=json.loads(pathlib.Path(args.provider).read_text());run=json.loads(pathlib.Path(args.run).read_text());raw_zip=pathlib.Path(args.zip).read_bytes()
    require(digest(raw_zip)==provider['digest'].removeprefix('sha256:') and len(raw_zip)==provider['size_in_bytes'],'provider ZIP digest/size differs')
    zipped={}
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as archive:
        for info in archive.infolist():
            if info.is_dir():continue
            name=safe_name(info.filename);require(name not in zipped,'duplicate ZIP member');zipped[name]=archive.read(info)
    manifest_name=next(name for name in zipped if name.endswith('MANIFEST.json'));zip_prefix=manifest_name[:-len('MANIFEST.json')]
    zipped={name.removeprefix(zip_prefix):value for name,value in zipped.items()}
    manifest=json.loads(zipped['MANIFEST.json']);commit=manifest['source_commit'];run_id=str(manifest['run_id'])
    require(str(provider['workflow_run']['id'])==run_id==str(run['id']),'run identity differs')
    require(provider['workflow_run']['head_sha']==run['head_sha']==commit,'source commit differs')
    require(run['status']=='completed','provider run is incomplete')
    source={name.removeprefix('source/'):value for name,value in zipped.items() if name.startswith('source/')}
    evidence=tar_files(zipped['NATIVE_EVIDENCE.tar.gz']);allfiles={**evidence,**zipped}
    for name,expected in manifest['files'].items():
        require(name in allfiles and digest(allfiles[name])==expected,'manifest member absent/changed: '+name)
    require(set(evidence)<=set(manifest['files']),'unmanifested native evidence member')
    unmanifested=set(zipped)-{'MANIFEST.json','NATIVE_EVIDENCE.tar.gz'}-set(manifest['files'])
    require(all(name.startswith('source/') for name in unmanifested),'unexpected unmanifested top-level evidence')
    frozen=json.loads(zipped['FREEZE.json']);prefix='native-frontier-v2/';result=json.loads(evidence[prefix+'RESULT.json'])
    require(frozen['schema']=='UDM_NATIVE_FRONTIER_FREEZE_V2' and frozen['source_commit']==result['source_commit']==commit,'source freeze mismatch')
    require(result['freeze']==frozen and result['freeze_sha256']==digest(zipped['FREEZE.json']),'result freeze binding differs')
    require(not any(name.endswith('/ERROR.json') for name in evidence),'controller error artifact present')
    for name,expected in frozen['files'].items():
        require(name in source and digest(source[name])==expected,'missing/changed frozen archived source: '+name)
        actual=subprocess.check_output(['git','--no-replace-objects','-C',args.repo,'show',commit+':'+name])
        require(actual==source[name],'Git and frozen archive source differ: '+name)
    require(set(source)==set(frozen['files']),'source archive and frozen universe differ')
    for workflow in ('.github/workflows/udm-native-frontier-v2.yml','.github/workflows/udm-native-admission-v2.yml'):
        require(workflow in source,'frozen source archive omits authority workflow')
    record_prefix='research/unified_consequence_runtime/archaeology/native-frontier-v2/'
    protocol=json.loads(source[record_prefix+'PROTOCOL.json']);metadata=json.loads(source[record_prefix+'FRESH_TASK_METADATA.json'])
    require(digest(source[record_prefix+'PROTOCOL.json'])==frozen['protocol_sha256'],'prospective protocol differs')
    require(digest(source[record_prefix+'FRESH_TASK_METADATA.json'])==protocol['metadata_sha256'],'frozen metadata differs')
    gate=protocol['admission_gate'];require(gate==frozen['admission_gate'] and gate['status']=='ADMISSION_ONLY_QUALIFIED','independent admission gate absent/changed')
    gate_result=json.loads(source[gate['result_path']]);require(digest(source[gate['result_path']])==gate['qualification_result_sha256'],'gate result digest differs')
    require(gate_result['status']=='ADMISSION_ONLY_QUALIFIED' and gate_result['first_task_gate']['status']=='PASS' and gate_result['source_commit']==gate['source_commit'],'wrong prior admission qualification')
    require(gate['source_commit']=='f8c0b06da1bbaddfd67229ca87cb53a0dab67ae0' and gate['run_id']==38856738333
        and gate['artifact_id']==12027916982 and gate['artifact_sha256']=='de8534883c760c2129b592a665c3cb735a4af360794409debe23660366853510','gate is not independently audited revision 2.1 authority')
    for basename in ('native_admission_v2','native_environment_v2','native_execution_v2','native_runtime_v2','qualify_native_admission_v2'):
        name='research/unified_consequence_runtime/'+basename+'.py'
        require(digest(source[name])==gate_result['freeze']['files'][name],'qualified admission core changed: '+name)
    admission_workflow='.github/workflows/udm-native-admission-v2.yml'
    require(digest(source[admission_workflow])==gate_result['freeze']['files'][admission_workflow],'qualified admission workflow changed')
    for key in ('policy','packages'):
        row=protocol[key];require(digest(source[row['path']])==row['sha256'],'frozen '+key+' differs')
    policy=json.loads(source[protocol['policy']['path']])
    old=tar_files(source['research/unified_consequence_runtime/archaeology/recursive-frontier/QUALIFIED_MAINTENANCE_STATE.tar.gz'])
    ledger=evidence[prefix+'state/metatron-ledger.jsonl'];oldledger=old['state/metatron-ledger.jsonl']
    require(len(oldledger.splitlines())==246 and ledger.startswith(oldledger),'original ledger prefix changed')
    require(result['original_records']==246 and result['retention']['original_prefix_preserved'] is True,'retained original prefix not acknowledged')
    require(result['retention']['ledger_sha256']==digest(ledger) and result['retention']['records']==len(ledger.splitlines()),'retained ledger digest/count differs')
    oldobjects={name.removeprefix('state/objects/'):value for name,value in old.items() if name.startswith('state/objects/')}
    objects={name.removeprefix(prefix+'state/objects/'):value for name,value in evidence.items() if name.startswith(prefix+'state/objects/')}
    require(len(oldobjects)==76 and all(name in objects and objects[name]==value for name,value in oldobjects.items()),'original CAS bytes changed')
    require(all(digest(value)==name for name,value in objects.items()),'CAS address/content differs')
    for name,expected in gate_result['freeze']['files'].items():
        if name.endswith(('generic_native_verify.py','native_frontier.py','decisive_native_verify.py','decisive_native_frontier.py','capability_index.json')):
            require(digest(source[name])==expected,'previous warrant source/index changed')
    require(len(json.loads(source['research/unified_consequence_runtime/capability_index.json'])['capabilities'])==70,'old inventory differs')
    contracts=zipped['contracts.log'].decode();matched=re.search(r'Ran (\d+) tests in ([0-9.]+)s',contracts)
    require(matched is not None and re.search(r'\nOK\s*$',contracts),'frontier controller contract tests not green')
    test_blocks=re.findall(r'^(test_\S+) \(([^\n]+)\) \.\.\.(.*?)(?=^test_|\n-+\nRan|\Z)',contracts,re.M|re.S)
    require(len(test_blocks)==int(matched[1]) and all(tail.strip().endswith('ok') for _,_,tail in test_blocks),'individual frontier controller contracts differ')
    for name in ('test_qualified_admission_receipt_cannot_license_changed_or_missing_core',
                 'test_incomplete_or_unknown_native_prefix_is_never_closed_failure',
                 'test_unknown_native_search_stops_without_promotion_or_hidden_calls',
                 'test_post_call_wall_overrun_retains_attempt_without_winner',
                 'test_future_gate_refuses_missing_cold_success_or_incomplete_warm',
                 'test_profile_receipt_requires_exact_producer_and_actual_independent_reexecution',
                 'test_same_budget_charges_separate_baseline_execution',
                 'test_partial_probe_costs_are_counted_once_without_final_receipt'):
        require(name in contracts,'required frontier authority control absent: '+name)
    prepared=[];native_packets=[]
    selected=metadata['selected'];require(len(selected)==len(result['tasks']),'frozen task carrier differs')
    for index,(spec,item) in enumerate(zip(selected,result['tasks'])):
        require(spec['repo']==item['repository'] and spec['pr']==item['pr'],'task identity differs from metadata')
        folder=prefix+'task-'+str(index)+'/'
        detail={'repository':item['repository'],'pr':item['pr'],'role':item['role'],'source_opened':item['source_opened'],'status':item.get('status'),'reason':item.get('reason')}
        setup=item.get('setup',{});detail['setup_status']=setup.get('status');detail['setup_seconds']=setup.get('total_wall_seconds');detail['setup_costs']=setup.get('costs',[])
        boundary=setup.get('source_boundaries',{});detail['source_boundary_present']=bool(boundary)
        if not item['source_opened']:
            require(not any(name.startswith(folder) for name in evidence),'unopened future has source/output artifact')
        if boundary:
            require(boundary['repository']==spec['repo'] and boundary['base_commit']==spec['base_commit']
                and boundary['author_test_head_commit']==spec['head_commit'] and boundary['head_production_fetched'] is False,'untouched source information boundary differs')
            for label,archive_name,identity_key,manifest_key in [('base_source_archive','base-source.tar.gz','base_identity','base_manifest'),('contract_source_archive','contract-source.tar.gz','augmented_identity','augmented_manifest')]:
                if label not in boundary:continue
                raw_archive=evidence[folder+archive_name];require(digest(raw_archive)==boundary[label]['sha256'],'native raw source archive digest differs')
                files=tar_files(raw_archive);require(source_identity(files,boundary[manifest_key])==boundary[identity_key],'source Git object identity differs')
                if label=='base_source_archive':basefiles=files
                else:augmented=files
            if boundary.get('production_preserved'):
                tests={row['path'] for row in boundary['author_tests']};changed={name for name in basefiles.keys()|augmented.keys() if basefiles.get(name)!=augmented.get(name)}
                require(changed==tests and augmented=={**basefiles,**{name:augmented[name] for name in tests}},'author overlay changed original production')
                frozen_tests={row['filename']:row for row in spec['files'] if row['filename'] in tests}
                require(set(frozen_tests)==tests,'frozen author test scope differs')
                for row in boundary['author_tests']:
                    file=augmented[row['path']];blob=hashlib.sha1(b'blob '+str(len(file)).encode()+b'\0'+file).hexdigest()
                    require(blob==row['git_blob']==frozen_tests[row['path']]['sha'] and digest(file)==row['sha256'],'author test blob differs from pre-outcome metadata')
                detail['source_bytes_preserved']=True
        if folder+'contract.json' in evidence:
            contract=json.loads(evidence[folder+'contract.json']);require(contract['protocol_binding']==result['freeze_sha256'],'native context wrong freeze')
            detail['environment_sha256']=contract['environment_sha256']
            environment=json.loads(evidence[folder+'environment.json'])
            require(fingerprint(environment)==contract['environment_sha256'],'prepared environment identity differs')
            require(environment['pytest_version']==policy['pytest_version'],'prepared pytest version differs from authority')
            require(all(contract[key]==boundary['augmented_identity'][key] for key in ('git_tree','tracked_tree_sha256','file_count')),'prepared contract source identity differs')
            detail['pytest_version']=environment['pytest_version'];detail['python_version']=environment['version']
        if folder+'collection/admission-certificate.json' in evidence:
            contract=json.loads(evidence[folder+'contract.json']);authority=json.loads(evidence[folder+'native-suite-authority.json'])
            certificate=json.loads(evidence[folder+'collection/admission-certificate.json']);certpacket,certdata=packet(certificate)
            require(json.loads(certpacket['tracked-source-manifest.json'])==boundary['augmented_manifest'],'original collection source manifest differs')
            require({key:certdata[key] for key in certificate['collection']}==certificate['collection'],'exact original collection projection differs')
            require(certificate['admission_revision']=='2.1' and certificate['status']=='ADMITTED_NATIVE_COLLECTION','unqualified native admission certificate')
            detail['collected']=len(certificate['collection']['collected_test_nodes']);detail['collection_costs']=certificate['costs']
            for name,data in evidence.items():
                if name.startswith(folder) and name.endswith('/receipt.json'):
                    receipt_value=json.loads(data)
                    if receipt_value.get('schema')!='UDM_GENERIC_NATIVE_PYTEST_V2':continue
                    candidate=None
                    # Native profile records in content-addressed state retain the executed source program.
                    for value in objects.values():
                        try:record=json.loads(value)
                        except (ValueError,UnicodeDecodeError):continue
                        if isinstance(record,dict) and record.get('schema')=='UDM_NATIVE_PROFILE_RECORD_V2' and record.get('receipt')==receipt_value:
                            candidate=record['candidate'];break
                    if candidate is None and receipt_value['candidate_sha256']==fingerprint({'replacements':[]}):candidate={'replacements':[]}
                    require(candidate is not None,'native candidate source not retained')
                    check=check_native_packet(receipt_value,contract,authority,certificate,policy,candidate,source,boundary['augmented_manifest'],augmented)
                    native_packets.append({'path':name,**check})
        collection_path=folder+'collection/checked-report.json'
        if collection_path in evidence:
            collected=json.loads(evidence[collection_path]);producer=json.loads(evidence[folder+'collection/report.json'])
            controller={'process_exit_code','timeout','source_mutations','unexpected_imports','costs'}
            require(producer=={key:value for key,value in collected.items() if key not in controller},'partial original collection raw report differs')
            require(json.loads(evidence[folder+'collection/tracked-source-manifest.json'])==boundary['augmented_manifest'],'partial collection source manifest differs')
            require(collected['pytest_import']==environment['pytest_import'],'partial collection executable pytest import differs')
            stderr=evidence.get(folder+'collection/stderr.log',b'').decode(errors='replace')
            detail['collection_result']={'process_exit_code':collected['process_exit_code'],'pytest_exit_code':collected['exit_code'],
                'collected':len(collected['collected_test_nodes']),'selected':len(collected['selected_test_nodes']),
                'collection_errors':collected['collection_errors'],'costs':collected['costs'],
                'timeout':collected['timeout'],'stderr':stderr,
                'negative_violations':{key:len(collected.get(key,[])) for key in ('plugin_violations','source_mutations','unexpected_imports','external_project_imports')}}
        prepared.append(detail)
    actual=[]
    for name,value in evidence.items():
        if name.endswith('/checked-report.json'):
            report=json.loads(value)
            if 'mode' in report and 'costs' in report:actual.append({'path':name,'mode':report['mode'],'costs':report['costs']})
    native_count=sum(row['costs'].get('native_calls',0) for row in actual);collection_count=sum(row['costs'].get('collection_calls',0) for row in actual)
    if native_count==0:
        require(result['verdicts']['G2'].startswith('UNKNOWN') and result['verdicts']['G3'].startswith('UNKNOWN') and result['verdicts']['G4'].startswith('UNKNOWN'),'zero-native refusal promoted to development/comparison')
        comparison='UNKNOWN_SHARED_ADMISSION_OR_RESIDUAL_OBSTRUCTION; NOT_AN_EXECUTED_COMPARATIVE_TIE'
    else:comparison='Assess only actually retained separately executed conditions; shared observations or matching registry entries do not establish comparison.'
    require(result['verdicts']['G5']==result['verdicts']['G6']=='UNKNOWN','native result promoted to formal proof/containment')
    for name in ('RESULT.json','FREEZE.json','contracts.log'):
        value=evidence[prefix+name] if name=='RESULT.json' else zipped[name];(out/name).write_bytes(value)
    report={'schema':'UDM_NATIVE_FRONTIER_V2_INDEPENDENT_ARCHIVE_AUDIT','status':'PASS_ARCHIVE_INTEGRITY_AUDIT',
        'source_commit':commit,'run_id':run_id,'run_conclusion':run['conclusion'],'artifact_id':provider['id'],'artifact_sha256':digest(raw_zip),'artifact_bytes':len(raw_zip),
        'manifest_files_checked':len(manifest['files']),'frozen_source_files_checked':len(frozen['files']),'admission_gate':gate,
        'original_authority':{'ledger_prefix_records':246,'CAS_objects':76,'inventory_rows':70,'byte_preserved':True},
        'retained_records':len(ledger.splitlines()),'retained_CAS_objects':len(objects),
        'contracts':{'count':int(matched[1]),'seconds':float(matched[2]),'all_individual_entries_ok':True},
        'result_status':result['status'],'claimed_verdicts':result['verdicts'],'smallest_obstruction':result.get('smallest_obstruction'),
        'prospective_boundary':'Pre-outcome code/source identities are frozen; prior nonexposure is an explicit research declaration, not a cryptographic absence proof. Unopened future source has no artifact.',
        'tasks':prepared,'actual_native_packets':native_packets,'actual_native_subprocesses':actual,
        'actual_native_calls':native_count,'actual_collection_calls':collection_count,'controller_wall_seconds':result['total_wall_seconds'],
        'conditions':result['conditions'],'agent_comparator_status':result['agent_comparator']['status'],
        'comparison_classification':comparison,'cost_boundary':result['cost_boundary'],
        'remaining_residual':result.get('smallest_obstruction','No runtime residual recorded; additional scientific causal review required.'),
        'exact_collection_obstruction':next((row['collection_result']['stderr'] for row in prepared
            if row.get('collection_result',{}).get('process_exit_code')),None),
        'scope':'Read-only archive/source/provenance/native-evidence parsing. No native rerun, source fetch, task repository access, repair, or prospective retargeting.',
        'audit_seconds':time.monotonic()-started}
    (out/'AUDIT.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    summary={key:value for key,value in report.items() if key not in ('tasks','conditions','actual_native_subprocesses','actual_native_packets')}
    summary['tasks']=[{key:value for key,value in row.items() if key!='setup_costs'} for row in prepared]
    summary['native_packets']=native_packets
    (out/'SUMMARY.json').write_text(json.dumps(summary,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'result_status':result['status'],'native_calls':native_count,'comparison':comparison,'verdicts':result['verdicts']},sort_keys=True))

if __name__=='__main__':main()
