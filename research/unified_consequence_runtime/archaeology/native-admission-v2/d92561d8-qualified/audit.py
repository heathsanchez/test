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

def receipt(value,certificate,contract,authority,policy,source_files,tracked_manifest,tracked_files):
    raw,data=packet(value);require(data==value['execution'],'receipt execution differs from packet')
    require(json.loads(raw['tracked-source-manifest.json'])==tracked_manifest,'native packet tracked manifest differs from authenticated raw source')
    for row in data['test_items']+data['import_manifest']:
        require(row['path'] in tracked_files and digest(tracked_files[row['path']])==row['sha256'],'native protected/imported source digest differs')
    require(data['pytest_import']==value['environment']['pytest_import'],'actual pytest import identity differs')
    for key,obj in [('contract',contract),('authority',authority),('certificate',certificate),('policy',policy)]:
        require(value[key+'_sha256']==fingerprint(obj),'wrong '+key+' fingerprint')
    require(value['candidate_sha256']==fingerprint({'replacements':[]}),'diagnostic edited production')
    require(value['runner_sha256']==digest(source_files['research/unified_consequence_runtime/native_execution_v2.py']),'wrong runner source')
    require(value['environment']==certificate['environment'],'receipt environment differs')
    require(value['plugins']==certificate['plugins'],'receipt plugin identity differs')
    require(value['protocol_binding']==contract['protocol_binding'],'wrong receipt protocol')
    require(value['costs']['native_calls']==1 and value['costs']['collection_calls']==1,'wrong actual native invocation cost')
    require(data['costs']['native_calls']==1 and data['costs']['horizon_seconds']==policy['execution_seconds'],'wrong native execution horizon')
    require(value['costs']['native_seconds']==data['costs']['seconds'],'wrong native wall cost')
    require(all(isinstance(v,(int,float)) and math.isfinite(v) and v>=0 for v in value['costs'].values()),'invalid cost scalar')
    counts=junit(raw['native.xml']);require(counts==value['junit'],'JUnit receipt counts differ')
    nodes=certificate['collection']['collected_test_nodes'];calls=[r for r in data['reports'] if r['when']=='call']
    failed=[r['nodeid'] for r in calls if r['outcome']=='failed']
    protected=[node for node in failed if any(node==p or node.startswith(p+'[') or node.startswith(p+'::') for p in authority['required_test_nodes'])]
    negative={key:len(data.get(key,[])) for key in ('deselected_test_nodes','collection_errors','source_mutations','unexpected_imports','external_project_imports','changed_test_code','plugin_violations')}
    return {'status':value['status'],'collected':len(data['collected_test_nodes']),'selected':len(data['selected_test_nodes']),
        'calls':len(calls),'junit':counts,'protected_failed_nodes':protected,'failed_nodes':failed,
        'skip_or_xfail_reports':sum(bool(r.get('wasxfail')) or r['outcome']=='skipped' for r in data['reports']),
        'negative_violations':negative,'costs':value['costs'],'native_horizon_seconds':data['costs']['horizon_seconds'],
        'all_exact_nodes':data['collected_test_nodes']==data['selected_test_nodes']==nodes,
        'all_exact_calls':[r['nodeid'] for r in calls]==nodes,
        'all_test_items':data['test_items']==certificate['collection']['test_items'],
        'all_plugins':data['plugin_manifest']==certificate['collection']['plugin_manifest']}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--zip',required=True);parser.add_argument('--provider',required=True)
    parser.add_argument('--repo',default='/workspace/udm-v54');parser.add_argument('--out',required=True)
    args=parser.parse_args();started=time.monotonic();out=pathlib.Path(args.out);out.mkdir(parents=True,exist_ok=True)
    provider=json.loads(pathlib.Path(args.provider).read_text());raw=pathlib.Path(args.zip).read_bytes()
    expected=provider.get('digest','').removeprefix('sha256:')
    require(len(expected)==64 and digest(raw)==expected,'provider ZIP digest differs')
    require(len(raw)==provider['size_in_bytes'],'provider ZIP size differs')
    files={}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for info in archive.infolist():
            name=safe_name(info.filename)
            if info.is_dir():continue
            require(name not in files,'duplicate ZIP file')
            files[name]=archive.read(info)
    manifest_name=next(n for n in files if n.endswith('MANIFEST.json'))
    prefix=manifest_name[:-len('MANIFEST.json')]
    files={name.removeprefix(prefix):val for name,val in files.items()}
    manifest=json.loads(files['MANIFEST.json']);commit=manifest['source_commit']
    evidence=tar_files(files['ADMISSION_V2_EVIDENCE.tar.gz']);source=tar_files(files['SOURCE.tar.gz'])
    allfiles={**evidence,**files}
    for name,expected in manifest['files'].items():
        require(name in allfiles,'manifest member missing: '+name)
        require(digest(allfiles[name])==expected,'manifest digest differs: '+name)
    require(set(evidence)<=set(manifest['files']),'unmanifested evidence member')
    require(set(files)-{'MANIFEST.json'}<=set(manifest['files']),'unmanifested ZIP member')
    frozen=json.loads(files['FREEZE.json']);result=json.loads(evidence['admission-v2/RESULT.json'])
    protocol=json.loads(evidence['admission-v2/PROTOCOL.json']);policy=json.loads(evidence['admission-v2/EXECUTION_POLICY.json'])
    require(commit==frozen['source_commit']==result['source_commit'],'source commit mismatch')
    require(str(manifest['run_id'])==str(provider['workflow_run']['id']),'provider run differs')
    require(provider['workflow_run']['head_sha']==commit,'provider source commit differs')
    require(frozen==result['freeze'],'embedded source freeze differs')
    require(set(frozen['files'])==set(protocol['freeze_files']),'freeze file universe differs')
    missing_source={}
    for name,expected in frozen['files'].items():
        native=subprocess.check_output(['git','--no-replace-objects','-C',args.repo,'show',commit+':'+name])
        require(digest(native)==expected,'Git source differs from freeze: '+name)
        if name in source:
            require(native==source[name],'Git and source archive differ: '+name)
        else:
            missing_source[name]=digest(native)
            supplement=out/'git-source-supplement'/name
            supplement.parent.mkdir(parents=True,exist_ok=True);supplement.write_bytes(native)
    require(digest(evidence['admission-v2/PROTOCOL.json'])==frozen['protocol_sha256'],'protocol digest differs')
    for name,expected in protocol['preserved_authority']['files'].items():
        require(digest(source[name])==expected,'prior authority source differs: '+name)
    inventory=json.loads(source['research/unified_consequence_runtime/capability_index.json'])
    require(len(inventory['capabilities'])==70,'inventory row count differs')
    for label in ('ledger_exact','CAS_exact','inventory_exact','source_pins_exact','original_FLASH_agrees'):
        require(result['retention'][label] is True,'retention claim false: '+label)
    old=tar_files(source['research/unified_consequence_runtime/archaeology/recursive-frontier/QUALIFIED_MAINTENANCE_STATE.tar.gz'])
    ledger='state/metatron-ledger.jsonl';require(evidence['admission-v2/'+ledger]==old[ledger],'prior ledger bytes changed')
    require(len(old[ledger].splitlines())==246,'prior ledger records differ')
    objects={n.removeprefix('state/objects/'):v for n,v in old.items() if n.startswith('state/objects/')}
    require(len(objects)==76,'prior CAS count differs')
    for name,value in objects.items():
        require(digest(value)==name and evidence['admission-v2/state/objects/'+name]==value,'prior CAS object differs')
    tests=files['contracts.log'].decode();match=re.search(r'Ran (\d+) tests in ([0-9.]+)s',tests)
    require(match is not None and int(match[1])==189 and re.search(r'\nOK\s*$',tests),'189 contract suite not green')
    test_blocks=re.findall(r'^(test_\S+) \(([^\n]+)\) \.\.\.(.*?)(?=^test_|\n-+\nRan|\Z)',tests,re.M|re.S)
    test_rows=[(name,scope) for name,scope,tail in test_blocks]
    require(len(test_rows)==189 and len(set(test_rows))==189 and all(tail.strip().endswith('ok') for _,_,tail in test_blocks),'contract entries/count differ')
    require('test_cached_static_authority_cannot_claim_changed_source_bytes' in tests,'static cached-source regression absent')
    require('test_unmapped_nested_class_assertions_are_refused' in tests,'nested-class mapping refusal absent')
    tasks=[]
    for index,item in enumerate(result['tasks']):
        prefix='admission-v2/task-'+str(index)+'/'
        detail={'repository':item['repository'],'status':item['status'],'total_wall_seconds':item['total_wall_seconds']}
        setup=item.get('setup',{});detail['setup_status']=setup.get('status')
        detail['setup_costs']=setup.get('costs',[])
        detail['source_information_boundary']=setup.get('source_boundaries',{})
        boundary=detail['source_information_boundary']
        if boundary.get('production_preserved'):
            base=tar_files(evidence[prefix+'base-source.tar.gz']);augmented=tar_files(evidence[prefix+'contract-source.tar.gz'])
            require(source_identity(base,boundary['base_manifest'])==boundary['base_identity'],'base Git tree differs')
            require(source_identity(augmented,boundary['augmented_manifest'])==boundary['augmented_identity'],'augmented Git tree differs')
            changed={name for name in base.keys()|augmented.keys() if base.get(name)!=augmented.get(name)}
            require(changed=={row['path'] for row in boundary['author_tests']},'production or unlicensed files changed')
            for row in boundary['author_tests']:
                require(digest(augmented[row['path']])==row['sha256'],'author test byte digest differs')
            require(boundary['head_production_fetched'] is False,'future production transport authorized')
            for label in ('base_source_archive','contract_source_archive'):
                raw_archive=evidence[prefix+pathlib.PurePosixPath(boundary[label]['path']).name]
                require(digest(raw_archive)==boundary[label]['sha256'] and len(raw_archive)==boundary[label]['bytes'],'raw source archive receipt differs')
            detail['raw_git_source_identity_independently_reconstructed']=True
        if prefix+'native/receipt.json' in evidence:
            contract=json.loads(evidence[prefix+'contract.json']);authority=json.loads(evidence[prefix+'native-suite-authority.json'])
            certificate=json.loads(evidence[prefix+'collection/admission-certificate.json'])
            certpacket,certdata=packet(certificate)
            require(certdata['mode']=='collect' and certdata['process_exit_code']==0,'certificate lacks actual successful collection')
            require(json.loads(certpacket['tracked-source-manifest.json'])==boundary['augmented_manifest'],'certificate source manifest differs')
            require({key:certdata[key] for key in certificate['collection']}==certificate['collection'],'certificate collection projection differs')
            require(all(contract[key]==boundary['augmented_identity'][key] for key in ('git_tree','tracked_tree_sha256','file_count')),'contract raw source identity differs')
            require(authority['source']==boundary['augmented_identity'] and authority['baseline_source']==boundary['base_identity'],'static authority raw source identity differs')
            for row in certificate['collection']['test_items']+certificate['collection']['import_manifest']:
                require(row['path'] in augmented and digest(augmented[row['path']])==row['sha256'],'certificate protected/imported source digest differs')
            require(certificate['status']=='ADMITTED_NATIVE_COLLECTION','wrong certificate status')
            require(digest(evidence[prefix+'collection/admission-certificate.json'])==item['collection']['certificate_sha256'] or
                fingerprint(certificate)==item['collection']['certificate_sha256'],'wrong controller certificate digest')
            environment=json.loads(evidence[prefix+'environment.json'])
            require(fingerprint(environment)==contract['environment_sha256']==fingerprint(certificate['environment']),'executable environment identity differs')
            require(contract['horizon_seconds']==policy['execution_seconds'],'contract execution budget differs')
            native=json.loads(evidence[prefix+'native/receipt.json'])
            detail['native']=receipt(native,certificate,contract,authority,policy,source,boundary['augmented_manifest'],augmented)
            require(detail['native']['status']==item['status'],'controller status differs from raw native receipt')
            if index==0:
                independent=json.loads(evidence[prefix+'receipt-recheck/receipt.json'])
                detail['independent_native']=receipt(independent,certificate,contract,authority,policy,source,boundary['augmented_manifest'],augmented)
                summary=json.loads(evidence[prefix+'independently-validated-receipt.json'])
                require(summary['independent_reexecution']['costs']==independent['costs'],'independent cost summary differs')
                for label in ('native','independent_native'):
                    checked=detail[label]
                    require(checked['status']=='FAIL_NATIVE' and checked['collected']==checked['selected']==checked['calls']==768,'first-gate native count/status differs')
                    require(checked['junit']=={'tests':768,'passed':767,'failures':1,'errors':0,'skipped':0},'first-gate JUnit differs')
                    require(not checked['skip_or_xfail_reports'] and not any(checked['negative_violations'].values()),'first-gate bypass control triggered')
                    require(checked['all_exact_nodes'] and checked['all_exact_calls'] and checked['all_test_items'] and checked['all_plugins'],'first-gate original suite changed')
                    require(checked['protected_failed_nodes']==['tests/test_more.py::BucketTests::test_falsey_validator_is_honoured'],'wrong protected failing assertion')
                require({k:v for k,v in independent['execution'].items() if k!='costs'}==
                    {k:v for k,v in native['execution'].items() if k!='costs'},'independent second native execution differs')
        collection_path=prefix+'collection/checked-report.json'
        if collection_path in evidence:
            collection=json.loads(evidence[collection_path]);observed=collection['collected_test_nodes'];selected=collection['selected_test_nodes']
            detail['raw_collection']={'process_exit_code':collection['process_exit_code'],'collected':len(observed),
                'selected':len(selected),'node_sets_equal':set(observed)==set(selected),
                'duplicate_collected':len(observed)-len(set(observed)),'duplicate_selected':len(selected)-len(set(selected)),
                'order_mismatch_positions':sum(a!=b for a,b in zip(observed,selected)),
                'deselected':len(collection['deselected_test_nodes']),'costs':collection['costs'],
                'violations':{key:len(collection.get(key,[])) for key in ('collection_errors','source_mutations','unexpected_imports','external_project_imports','changed_test_code','plugin_violations')},
                'native_execution_archived':prefix+'native/receipt.json' in evidence,
                'controller_error':item.get('error'),
                'interpretation':'Strict ordered identity rejects any lawful pytest reordering even when exact node sets agree; no relaxation or native promotion in this audit.' if observed!=selected else 'Exact ordered node identity observed.'}
        tasks.append(detail)
    require(result['status']=='ADMISSION_ONLY_QUALIFIED' and result['first_task_gate']['status']=='PASS','admission gate not qualified')
    require(all(result['verdicts'][gate]=='UNKNOWN' for gate in ('G2','G3','G4','G5','G6')),'admission promoted to developmental/formal/security claim')
    subprocesses=[]
    for name,raw_checked in evidence.items():
        if name.endswith('/checked-report.json'):
            checked=json.loads(raw_checked)
            subprocesses.append({'path':name,'mode':checked['mode'],'costs':checked['costs']})
    for name,raw_value in [('RESULT.json',evidence['admission-v2/RESULT.json']),('FREEZE.json',files['FREEZE.json']),('contracts.log',files['contracts.log'])]:
        (out/name).write_bytes(raw_value)
    if missing_source:
        buffer=io.BytesIO()
        with tarfile.open(fileobj=buffer,mode='w',format=tarfile.PAX_FORMAT) as supplement:
            for name in sorted(missing_source):
                raw_source=(out/'git-source-supplement'/name).read_bytes()
                info=tarfile.TarInfo(name);info.size=len(raw_source);info.mode=0o644
                info.uid=info.gid=info.mtime=0;info.uname=info.gname=''
                supplement.addfile(info,io.BytesIO(raw_source))
        supplement_path=out/'SOURCE_ARCHIVE_SUPPLEMENT.tar.gz'
        supplement_path.write_bytes(gzip.compress(buffer.getvalue(),mtime=0))
        supplemental_files=tar_files(supplement_path.read_bytes())
        require({name:digest(raw) for name,raw in supplemental_files.items()}==missing_source,'supplement archive differs')
        supplemental_manifest={'schema':'UDM_FROZEN_SOURCE_ARCHIVE_SUPPLEMENT','source_commit':commit,'run_id':manifest['run_id'],
            'original_artifact_id':provider['id'],'original_zip_sha256':digest(raw),'original_provider_archive_unchanged':True,
            'reason':'Original source TAR omitted one frozen predecessor workflow; independently reconstructed from exact frozen Git commit.',
            'files':missing_source,'archive_sha256':digest(supplement_path.read_bytes()),'archive_bytes':supplement_path.stat().st_size}
        (out/'SOURCE_ARCHIVE_SUPPLEMENT.json').write_text(json.dumps(supplemental_manifest,sort_keys=True,indent=2)+'\n')
    report={'schema':'UDM_NATIVE_ADMISSION_V2_INDEPENDENT_ARCHIVE_AUDIT','status':'PASS_NATIVE_ADMISSION_AUDIT_WITH_SOURCE_SUPPLEMENT' if missing_source else 'PASS_ARCHIVE_AUDIT',
        'source_commit':commit,'run_id':manifest['run_id'],'artifact_id':provider['id'],'provider_zip_sha256':digest(raw),
        'provider_zip_bytes':len(raw),'manifest_files_checked':len(manifest['files']),'source_files_frozen':len(frozen['files']),
        'source_files_archived':len(source),'missing_frozen_source_from_original_archive':missing_source,'source_supplement':'Exact frozen Git bytes independently fetched locally into git-source-supplement; original provider artifact remains unmodified.','contracts':{'count':189,'seconds':float(match[2]),'all_individual_entries_ok':True},
        'retention':{'records':246,'CAS_objects':76,'inventory_rows':70,'exact_bytes':True},
        'tasks':tasks,'controller_wall_seconds':result['total_wall_seconds'],'actual_native_subprocesses':subprocesses,'actual_native_call_count':sum(r['costs']['native_calls'] for r in subprocesses),'actual_collection_call_count':sum(r['costs']['collection_calls'] for r in subprocesses),
        'verdicts':{'admission':'WARRANTED_BOUNDED','G0_G1':'PRESERVED','G2':'UNKNOWN','G3':'UNKNOWN','G4':'UNKNOWN','G5':'UNKNOWN','G6':'UNKNOWN'},
        'scope':'Read-only independent parsing of provider/source/raw collection/native/JUnit/cost evidence; no native rerun or fresh task exposure.',
        'runtime_fixtures':'Actual existing Machine/Metatron/FLASH contract fixtures include native execution, fresh restoration, and separate-process restart. Supplied fixture repair is not a developmental scientific result; raw per-fixture subprocess outputs are not separately archived.',
        'remaining_residual':'Freeze untouched source-distinct tasks after this bounded admission gate; execute existing UDM and matched ledger/coding-agent comparisons. Attrs/cattrs are UNKNOWN here before native execution because collection order changes (sets agree); earlier exposed diagnostics independently retain skip/xfail limitations.',
        'audit_seconds':time.monotonic()-started}
    (out/'AUDIT.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n')
    compact={k:v for k,v in report.items() if k!='tasks'}
    compact['tasks']=[{k:v for k,v in row.items() if k not in ('setup_costs','source_information_boundary')} for row in tasks]
    (out/'SUMMARY.json').write_text(json.dumps(compact,sort_keys=True,indent=2)+'\n')
    print(json.dumps({'status':report['status'],'source_commit':commit,'run_id':manifest['run_id'],
        'manifest_files_checked':len(manifest['files']),'tasks':[{k:v for k,v in row.items() if k not in ('setup_costs','source_information_boundary')} for row in tasks]},sort_keys=True))

if __name__=='__main__':main()
