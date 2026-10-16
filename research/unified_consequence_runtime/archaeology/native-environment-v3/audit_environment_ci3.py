"""Read-only CI evidence audit. Never import or execute retained project code."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
import xml.etree.ElementTree as ET
import zipfile

REPO = Path('/workspace/udm-v54')
COMMIT = '9b05faab72fa36f4304965b65b2564c626314b89'
BASE = 'fa6bb190eff9b374ab7a95aaf9c618ad2db31419'
RUN = '38872399668'
HERE = 'research/unified_consequence_runtime/'
RECORDS = HERE + 'archaeology/native-environment-v3/'
PREFIX = 'environment-v3/'


def sha(raw): return hashlib.sha256(raw).hexdigest()
def canonical(value): return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()
def fp(value): return sha(canonical(value))
def require(condition, message):
    if not condition: raise ValueError(message)
def safe(name):
    p = PurePosixPath(name)
    require(name and not p.is_absolute() and '..' not in p.parts and str(p) == name,
            'unsafe or noncanonical member: ' + name)
    return name
def git(*args):
    return subprocess.check_output(['git', '--no-replace-objects', '-C', str(REPO), *args])
def blob(name): return git('show', COMMIT + ':' + name)
def git_tree(commit):
    rows = {}
    for row in git('ls-tree', '-rz', '--full-tree', commit).split(b'\0'):
        if not row: continue
        meta, name = row.split(b'\t', 1)
        mode, kind, oid = meta.decode().split()
        rows[name.decode()] = (mode, kind, oid)
    return rows
def tar_bytes(raw):
    result = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:*') as packet:
        seen = set()
        for member in packet:
            name = member.name.rstrip('/')
            safe(name); require(name not in seen, 'duplicate tar member: ' + name); seen.add(name)
            if member.isdir(): continue
            require(member.isfile(), 'nonregular tar member: ' + name)
            result[name] = (packet.extractfile(member).read(), member.mode)
    return result
def junit(raw):
    counts = dict(tests=0, passed=0, failures=0, errors=0, skipped=0)
    for case in ET.fromstring(raw).iter('testcase'):
        counts['tests'] += 1
        key = next((key for key, tag in [('errors','error'), ('failures','failure'),
                    ('skipped','skipped')] if case.find(tag) is not None), 'passed')
        counts[key] += 1
    return counts
def norm(name): return re.sub(r'[-_.]+', '-', name).lower()
def manifest_git_tree(manifest):
    root={}
    for row in manifest:
        branch=root;parts=PurePosixPath(row['path']).parts
        for part in parts[:-1]:branch=branch.setdefault(part,{})
        require(parts[-1] not in branch,'duplicate manifest Git path')
        branch[parts[-1]]=(row['mode'],row['blob'])
    def encode(branch):
        raw=b''
        for name,value in sorted(branch.items(),key=lambda item:(item[0]+('/' if isinstance(item[1],dict) else '')).encode()):
            mode,oid=('40000',encode(value)) if isinstance(value,dict) else value
            raw+=mode.encode()+b' '+name.encode()+b'\0'+bytes.fromhex(oid)
        return hashlib.sha1(b'tree '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    return encode(root)


class Audit:
    def __init__(self, artifact):
        self.artifact = Path(artifact)
        self.evidence = {}
        self.sections = {}
        self.report = {'schema':'UDM_CI3_INDEPENDENT_ARTIFACT_AUDIT_V1',
            'source_commit':COMMIT, 'baseline_commit':BASE, 'run_id':RUN,
            'execution_boundary':{'artifact_code_executed':False,'target_queries':0,
                'network_queries':0,'native_reexecutions':0,'repository_edits':False},
            'verdicts':{f'G{i}':'UNKNOWN' for i in range(2,7)}}

    def load(self):
        if self.artifact.is_dir():
            candidates = list(self.artifact.rglob('MANIFEST.json'))
            require(len(candidates)==1, 'one outer MANIFEST.json required')
            parent = candidates[0].parent
            outer = {p.name:p.read_bytes() for p in parent.iterdir() if p.is_file()}
            self.report['artifact']={'path':str(self.artifact),'kind':'directory'}
        else:
            self.report['artifact']={'path':str(self.artifact),'sha256':sha(self.artifact.read_bytes()),
                                     'bytes':self.artifact.stat().st_size,'kind':'zip'}
            with zipfile.ZipFile(self.artifact) as packet:
                names = [safe(n) for n in packet.namelist() if not n.endswith('/')]
                require(len(names)==len(set(names)), 'duplicate ZIP members')
                manifests=[n for n in names if PurePosixPath(n).name=='MANIFEST.json']
                require(len(manifests)==1, 'one outer MANIFEST.json required')
                parent=PurePosixPath(manifests[0]).parent
                outer={str(PurePosixPath(n).relative_to(parent)):packet.read(n) for n in names
                       if PurePosixPath(n).parent==parent}
        self.outer=outer
        provenance=self.artifact.parent
        run_path=provenance/('CI_'+RUN+'_RUN.json')
        artifact_path=provenance/('CI_'+RUN+'_ARTIFACTS.json')
        run=json.loads(run_path.read_bytes());records=json.loads(artifact_path.read_bytes())['artifacts']
        require(run['id']==int(RUN) and run['head_sha']==COMMIT and run['status']=='completed' and
                run['conclusion']=='success' and run['run_attempt']==1,'external run provenance')
        records=[row for row in records if row['id']==12034946936]
        require(len(records)==1,'one expected genuine artifact ID')
        record=records[0]
        require(record['workflow_run']['id']==int(RUN) and record['workflow_run']['head_sha']==COMMIT and
                record['expired'] is False and record['name']=='native-environment-selection-v3-'+COMMIT+'-1',
                'external artifact source/run identity')
        if self.artifact.is_file():
            require(record['digest']=='sha256:'+self.report['artifact']['sha256'] and
                    record['size_in_bytes']==self.report['artifact']['bytes'],'external artifact digest/size')
        self.sections['github_provenance']={'status':'PASS','artifact_id':record['id'],
            'run_url':run['html_url'],'run_conclusion':run['conclusion'],
            'github_artifact_digest':record['digest'],'run_provenance_sha256':sha(run_path.read_bytes()),
            'artifact_provenance_sha256':sha(artifact_path.read_bytes()),
            'transport_boundary':'Provenance JSON and ZIP independently obtained by root; auditor made no network query.'}
        manifest=json.loads(outer['MANIFEST.json'])
        require(manifest['source_commit']==COMMIT and str(manifest['run_id'])==RUN,
                'outer manifest source or run mismatch')
        raw=outer['ENVIRONMENT_V3_EVIDENCE.tar.gz']
        require(sha(raw)==manifest['files']['ENVIRONMENT_V3_EVIDENCE.tar.gz'], 'evidence tar digest')
        hashes={}
        with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as packet:
            seen=set()
            for member in packet:
                name=safe(member.name)
                require(name not in seen and member.isfile(), 'duplicate/nonregular evidence member '+name)
                seen.add(name)
                stream=packet.extractfile(member);digest=hashlib.sha256();parts=[]
                retain=(member.size<1024*1024 or name.endswith(('.json','.xml','.log','.txt','.tar.gz')))
                while True:
                    data=stream.read(1024*1024)
                    if not data:break
                    digest.update(data)
                    if retain:parts.append(data)
                hashes[name]=digest.hexdigest()
                if retain:self.evidence[name]=b''.join(parts)
        expected=dict(manifest['files']);expected.pop('ENVIRONMENT_V3_EVIDENCE.tar.gz')
        require(hashes==expected, 'exact evidence member/hash coverage differs from manifest')
        for name,raw in outer.items():
            if name in manifest['files']:
                require(sha(raw)==manifest['files'][name], 'outer duplicate digest '+name)
        self.manifest=manifest
        self.sections['manifest']={'status':'PASS','members':len(hashes),'all_bytes_sha256':True,
            'manifest_sha256':sha(outer['MANIFEST.json']),'evidence_tar_sha256':sha(outer['ENVIRONMENT_V3_EVIDENCE.tar.gz'])}

    def raw(self,name): return self.evidence[name]
    def doc(self,name): return json.loads(self.raw(name))
    def same_git(self,path,raw): require(raw==blob(path),'committed source bytes '+path)

    def sources(self):
        tree=git_tree(COMMIT);old=git_tree(BASE)
        require(all(tree.get(name)==value for name,value in old.items()), 'original baseline mode/blob changed')
        self.freeze=self.doc('FREEZE.json');f=self.freeze
        require(f['schema']=='UDM_NATIVE_ENVIRONMENT_QUALIFICATION_FREEZE_V3' and
                f['source_commit']==COMMIT and f['baseline_commit']==BASE and
                f['all_baseline_files_preserved'] is True and
                f['diagnostic_source_access_started'] is False, 'freeze authority fields')
        paths={name for name in tree if name.startswith((HERE,'.github/workflows/'))}
        require(set(f['files'])==paths, 'freeze complete source membership')
        for name,digest in f['files'].items(): require(sha(blob(name))==digest,'freeze source digest '+name)
        source=tar_bytes(self.raw('SOURCE.tar.gz'))
        for name,(raw,mode) in source.items():
            require(name in tree and tree[name][1]=='blob','source tar unexpected member '+name)
            expected_mode,_,oid=tree[name]
            require(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==oid,
                    'source tar Git bytes '+name)
            # Git archive applies its tar.umask (default0002), so a Git0644
            # blob is carried as0664. Git's executable bit remains exact.
            require(mode&~0o022==int(expected_mode,8)&0o777,'source tar executable/mode '+name)
        expected_source={name for name in tree if name.startswith(HERE)}|{
            '.github/workflows/udm-native-environment-selection-v3.yml',
            '.github/workflows/udm-native-admission-v2.yml','.github/workflows/udm-decisive-native.yml'}
        require(set(source)==expected_source,'source archive exact membership')
        self.protocol=json.loads(blob(RECORDS+'PROTOCOL.json'))
        self.catalog=json.loads(blob(RECORDS+'ENVIRONMENT_CATALOG.json'))
        require(f['protocol_sha256']==sha(blob(RECORDS+'PROTOCOL.json')) and
                f['catalog_sha256']==fp(self.catalog),'freeze protocol/catalog binding')
        for name in ['PROTOCOL.json','ENVIRONMENT_CATALOG.json','PACKAGE_METADATA.json']:
            self.same_git(RECORDS+name,self.raw(PREFIX+name))
        require(self.raw(PREFIX+'FREEZE.json')==self.raw('FREEZE.json'),'freeze copies differ')
        require(self.raw('source-commit.txt').decode().strip()==COMMIT,'source-commit.txt')
        self.binding=sha(self.raw('FREEZE.json'))
        self.sections['sources']={'status':'PASS','source_members':len(source),
            'frozen_files':len(paths),'preserved_original_git_files':len(old),'protocol_binding':self.binding}

    def result_and_runtime(self):
        self.result=self.doc(PREFIX+'RESULT.json');r=self.result
        require(r['status']=='ADMISSION_ONLY_QUALIFIED' and r['source_commit']==COMMIT and
                r['mode']=='DEVELOPMENT_DIAGNOSTICS_ONLY' and r['acquisitions']==r['candidates']==0,
                'admission-only result')
        require(r['verdicts']==self.protocol['verdicts'] and
                all(r['verdicts'][f'G{i}']=='UNKNOWN' for i in range(2,7)),'scientific verdict boundary')
        require(r['freeze']==self.freeze and r['runtime_inventory']==self.freeze['runtimes'] and
                r['protocol_binding']==self.binding,'result frozen binding')
        require(r['first_task_gate']['status']=='PASS' and len(r['tasks'])==2,'two-task first gate')
        require(r['attempt_costs']=={'native_calls':4,'collection_calls':6,'subprocess_attempts':10},
                'inclusive diagnostic attempt costs')
        require(not any(name.endswith('/ERROR.json') or name=='ERROR.json' for name in self.evidence),
                'ERROR.json retained')
        profiles={p['id']:p for p in self.catalog['profiles']}
        require(set(self.freeze['runtimes'])==set(profiles),'complete external runtime profiles')
        for ident,record in self.freeze['runtimes'].items():
            identity=record['identity'];profile=profiles[ident]
            require(fp(record['stdlib_files'])==identity['stdlib_manifest_sha256'],'frozen stdlib digest '+ident)
            require('.'.join(map(str,identity['version_info'][:3]))==profile['python_version'] and
                    identity['implementation'].lower()==profile['python_implementation'].lower(),
                    'frozen interpreter exact version '+ident)
        post=self.doc('POST_FIXTURE_RUNTIME_AUDIT.json')
        require(post['status']=='PASS_FROZEN_RUNTIME_BYTES' and post['frozen_authority_modified'] is False,
                'postfixture runtime status')
        require(set(post['runtimes'])==set(profiles),'postfixture complete runtimes')
        for row in post['runtimes'].values():
            require(not any(row[k] for k in ['added','removed','changed','executable_changed','changes']),
                    'postfixture runtime bytes differ')
        cache_receipts=[]
        for name in self.evidence:
            if name.startswith('runtime-bootstrap/') and name.endswith('.json'):
                doc=self.doc(name)
                if isinstance(doc,dict) and doc.get('schema')=='UDM_ORIGINAL_STDLIB_CACHE_PREPARATION_V3':
                    require(doc['status']=='PREPARED_STDLIB_BYTECODE' and
                            doc['source_manifest_before']==doc['source_manifest_after'] and
                            doc['compiler_error'] is None and doc['compilation'] and doc['bytecode_manifest'],
                            'original stdlib cache preparation '+name)
                    cache_receipts.append(name)
        require(len(cache_receipts)==2,'both original stdlib cache preparations retained')
        self.sections['admission_and_runtime']={'status':'PASS','G2_G6':'UNKNOWN',
            'diagnostic_attempts':r['attempt_costs'],'postfixture_exact_runtime_bytes':True,
            'original_stdlib_cache_receipts':cache_receipts}

    def source_archive(self,raw,manifest,identity):
        data=tar_bytes(raw);require(set(data)=={row['path'] for row in manifest},'tracked archive membership')
        require(identity['file_count']==len(manifest) and fp(manifest)==identity['tracked_tree_sha256'],
                'tracked manifest identity')
        require(manifest_git_tree(manifest)==identity['git_tree'],'reconstructed original Git tree')
        for row in manifest:
            content,mode=data[row['path']]
            require(sha(content)==row['sha256'] and mode==int(row['mode'],8)&0o777,'tracked blob/mode')
            require(hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest()==row['blob'],
                    'tracked Git blob identity')
        return {name:raw_mode[0] for name,raw_mode in data.items()}

    def packet(self,document,directory,manifest):
        files={name:base64.b64decode(value,validate=True) for name,value in document['packet'].items()}
        require(set(files)=={'stdout.log','stderr.log','report.json','checked-report.json',
                'tracked-source-manifest.json','native.xml'},'complete native packet')
        require({name:sha(raw) for name,raw in files.items()}==document['packet_sha256'],'packet digests')
        for name,raw in files.items():require(raw==self.raw(directory+'/'+name),'packet/file copy '+directory+'/'+name)
        checked=json.loads(files['checked-report.json']);producer=json.loads(files['report.json'])
        exclude={'process_exit_code','timeout','source_mutations','unexpected_imports','costs'}
        require(producer=={k:v for k,v in checked.items() if k not in exclude},'producer/controller report relation')
        require(json.loads(files['tracked-source-manifest.json'])==manifest,'packet exact tracked manifest')
        return checked,files

    def native_data(self,data,counts,nodes,authority,files):
        require(data['mode']=='run' and data['collected_test_nodes']==data['selected_test_nodes']==nodes and
                not data['deselected_test_nodes'],'complete native node order')
        require(data['process_exit_code']==data['exit_code']==1 and data['timeout'] is False,'protected native exit')
        for key in ['collection_errors','source_mutations','unexpected_imports','external_project_imports',
                    'changed_test_code','plugin_violations']:
            require(not data[key],'native violation '+key)
        reports=data['reports'];require(len(reports)==3*len(nodes),'exact phase report count')
        for phase in ['setup','call','teardown']:
            rows=[row for row in reports if row['when']==phase]
            require([row['nodeid'] for row in rows]==nodes,'exact '+phase+' sequence')
            require(all(row['outcome'] in ('passed','failed') and not row['wasxfail'] for row in rows),
                    'skip/xfail or invalid outcome')
            if phase!='call':require(all(row['outcome']=='passed' for row in rows),'setup/teardown failure')
        calls=[row for row in reports if row['when']=='call']
        require(counts==dict(tests=len(nodes),passed=sum(row['outcome']=='passed' for row in calls),
            failures=sum(row['outcome']=='failed' for row in calls),errors=0,skipped=0) and counts['failures']>0,
            'complete JUnit phase/count equality')
        protected=[row['nodeid'] for row in calls if row['outcome']=='failed' and any(
            row['nodeid']==prefix or row['nodeid'].startswith(prefix+'[') or row['nodeid'].startswith(prefix+'::')
            for prefix in authority['required_test_nodes'])]
        require(protected,'no protected actual call failure')
        for row in data['import_manifest']+data['test_items']:
            require(row['path'] in files and sha(files[row['path']])==row['sha256'],'import/test source byte identity')
        return protected

    def task(self,index,expected_count):
        prefix=PREFIX+'task-'+str(index)+'/';item=self.result['tasks'][index];spec=self.protocol['diagnostics'][index]
        admission=self.doc(prefix+'admission-v3.json');setup=admission['setup']
        require(item['setup']==admission and admission['status']==setup['status']=='PREPARED','prepared setup identity')
        require(item['repository']==spec['repo'] and item['role']==spec['role'] and item['status']=='FAIL_NATIVE',
                'diagnostic role/status')
        require(item['attempt_costs']=={'native_calls':2,'collection_calls':3,'subprocess_attempts':5},'task attempt costs')
        selected=admission['selection'];profile=selected['selected_profile'];ident=profile['id']
        require(selected['status']=='CANDIDATE_SOURCE_ENVIRONMENT' and
                profile in self.catalog['profiles'] and admission['runtime']==self.freeze['runtimes'][ident],
                'source candidate and external frozen runtime')
        contract=admission['contract'];authority=admission['authority'];policy=admission['policy'];boundaries=admission['source_boundaries']
        for name,value in [('contract',contract),('native-suite-authority',authority),('policy',policy),('source-boundaries',boundaries)]:
            require(self.doc(prefix+'native/'+name+'.json')==value,'setup field file '+name)
        require(boundaries['base_commit']==spec['base_commit'] and boundaries['author_test_head_commit']==spec['head_commit'] and
                boundaries['production_preserved'] is True and boundaries['head_production_fetched'] is False,
                'original source overlay boundary')
        require(admission['source_metadata_identity']==boundaries['base_identity'],'metadata/base exact source')
        base=self.source_archive(self.raw(prefix+'native/base-source.tar.gz'),boundaries['base_manifest'],boundaries['base_identity'])
        augmented=self.source_archive(self.raw(prefix+'native/contract-source.tar.gz'),boundaries['augmented_manifest'],boundaries['augmented_identity'])
        require(self.raw(prefix+'metadata-source.tar.gz')==self.raw(prefix+'native/base-source.tar.gz'),'metadata/base archive equality')
        author={}
        for row in boundaries['author_tests']:
            raw=augmented[row['path']];require(sha(raw)==row['sha256'] and len(raw)==row['bytes'],'author test digest')
            require(row['endpoint'].endswith('?ref='+spec['head_commit']),'author exact head endpoint')
            transport=self.raw(prefix+'native/'+PurePosixPath(row['transport_json']).name)
            require(sha(transport)==row['transport_sha256'],'exact author transport JSON')
            response=json.loads(transport)
            require(response['path']==row['path'] and response['type']=='file' and response['encoding']=='base64' and
                    base64.b64decode(response['content'])==raw and response['sha']==row['git_blob'] and
                    response['size']==len(raw),'author transport exact bytes/blob')
            author[row['path']]=raw
        require(augmented==dict(base,**author),'author tests only overlay')
        for key in ['git_tree','tracked_tree_sha256','file_count']:
            require(contract[key]==boundaries['augmented_identity'][key],'contract source identity '+key)
        require(authority['baseline_source']==boundaries['base_identity'] and authority['source']==boundaries['augmented_identity'] and
                authority['baseline_commit']==spec['base_commit'] and authority['source_commit']==contract['commit'],
                'authority source binding')
        require(contract['protocol_binding']==authority['protocol_binding']==self.binding,'task protocol binding')
        require(policy['pytest_version']==profile['pytest_version'] and policy['plugins']==profile['plugins'], 'external execution policy')
        environment=self.doc(prefix+'native/environment.json');plugins=self.doc(prefix+'native/plugin-identity.json')
        require(fp(environment)==contract['environment_sha256'],'full environment fingerprint including raw import roots')
        require(environment['runtime_identity']==admission['runtime']['identity'] and
                environment['executable_sha256']==admission['runtime']['identity']['executable_sha256'] and
                environment['pytest_version']==profile['pytest_version'] and
                isinstance(environment['runtime_import_roots'],list) and len(environment['runtime_import_roots'])==3,
                'child executable/stdlib/runtime import roots')
        packages=self.doc(prefix+'pinned-package-files.json')
        require(fp(packages)==admission['pinned_packages_sha256'],'pinned package file inventory digest')
        require({row[0]:row[1] for row in packages}=={norm(pin.split('==')[0]):pin.split('==')[1] for pin in profile['packages']},
                'all exact package pins')
        require(all(row[2] and all(re.fullmatch('[0-9a-f]{64}',entry[1]) for entry in row[2]) for row in packages),'pinned file authority')
        requirement=''.join(pin+' --hash=sha256:'+profile['package_artifacts'][norm(pin.split('==')[0])]['sha256']+'\n' for pin in profile['packages'])
        require(self.raw(prefix+'pinned-requirements.txt').decode()==requirement,'exact wheel artifact hash requirements')
        cert=self.doc(prefix+'collection/admission-certificate.json');collection=cert['collection'];nodes=collection['selected_test_nodes']
        require(len(nodes)==expected_count and len(set(nodes))==expected_count and
                collection['collected_test_nodes']==nodes and not collection['deselected_test_nodes'],'expected full original collection')
        require(cert['status']=='ADMITTED_NATIVE_COLLECTION','collection admission status')
        require(cert['schema']=='UDM_NATIVE_ADMISSION_CERTIFICATE_V3' and cert['admission_revision']=='3.1' and
                cert['contract_sha256']==fp(contract) and cert['authority_sha256']==fp(authority) and
                cert['policy_sha256']==fp(policy) and cert['runner_sha256']==self.freeze['files'][HERE+'native_execution_v3.py'] and
                cert['environment']==environment and cert['plugins']==plugins,'collection source/runtime bindings')
        checked,_=self.packet(cert,prefix+'collection',boundaries['augmented_manifest'])
        require(checked['mode']=='collect' and checked['process_exit_code']==checked['exit_code']==0 and not checked['collection_errors'],
                'collection completion')
        require(all(checked[k]==v for k,v in collection.items()),'certificate raw collection')
        collection_reports=[]
        for name in self.evidence:
            if not name.startswith(prefix) or not name.endswith('/checked-report.json'):continue
            data=self.doc(name)
            if data.get('mode')!='collect':continue
            require(data['process_exit_code']==data['exit_code']==0 and data['timeout'] is False and
                    data['costs']['collection_calls']==1 and data['costs']['native_calls']==0,
                    'independent collection completion '+name)
            require(all(data[k]==v for k,v in collection.items()),'independent exact collection '+name)
            require(not any(data[k] for k in ['collection_errors','source_mutations','unexpected_imports',
                    'external_project_imports','plugin_violations']),'independent collection violation '+name)
            for row in data['test_items']+data['import_manifest']:
                require(row['path'] in augmented and sha(augmented[row['path']])==row['sha256'],
                        'independent collection source identity '+name)
            collection_reports.append(name)
        require(len(collection_reports)==3,'exactly three diagnostic collection calls')
        primary=self.doc(prefix+'native-execution/receipt.json');fresh=self.doc(prefix+'independent-native-execution/receipt.json')
        validated=self.doc(prefix+'independently-validated-receipt.json')
        require(validated==dict(primary,independent_reexecution=validated['independent_reexecution']),'validated original receipt copy')
        require(validated['independent_reexecution']['costs']==fresh['costs'],'independent receipt native costs')
        protections=[]
        for receipt,directory in [(primary,prefix+'native-execution/execution'),(fresh,prefix+'independent-native-execution/execution')]:
            for key,value in [('contract_sha256',fp(contract)),('authority_sha256',fp(authority)),('policy_sha256',fp(policy)),
                              ('certificate_sha256',fp(cert)),('candidate_sha256',fp({'replacements':[]})),
                              ('runner_sha256',self.freeze['files'][HERE+'native_execution_v3.py'])]:
                require(receipt[key]==value,'receipt binding '+key)
            require(receipt['schema']=='UDM_GENERIC_NATIVE_PYTEST_V3' and receipt['admission_revision']=='3.1' and
                    receipt['status']=='FAIL_NATIVE' and receipt['protocol_binding']==self.binding and
                    receipt['environment']==environment and receipt['plugins']==plugins and
                    receipt['external_enforcement']=='UNKNOWN_NONBYPASSABILITY','native receipt scope')
            data,packet=self.packet(receipt,directory,boundaries['augmented_manifest'])
            require(data==receipt['execution'] and junit(packet['native.xml'])==receipt['junit'],'execution/JUnit packet binding')
            protections.append(self.native_data(data,receipt['junit'],nodes,authority,augmented))
            require(data['plugin_manifest']==collection['plugin_manifest'] and data['test_items']==collection['test_items'],
                    'collection/execution plugin and test identity')
            require(receipt['costs']['native_calls']==receipt['costs']['collection_calls']==1 and
                    data['costs']['native_calls']==1 and data['costs']['collection_calls']==0,'one receipt native run')
        require(primary['junit']==fresh['junit'] and {k:v for k,v in primary['execution'].items() if k!='costs'}==
                {k:v for k,v in fresh['execution'].items() if k!='costs'},'complete independent replay equality')
        run_reports=[name for name in self.evidence if name.startswith(prefix) and name.endswith('/checked-report.json') and
                     self.doc(name).get('mode')=='run']
        require(len(run_reports)==2,'exactly two retained native diagnostic runs')
        require(item['gate']['status']=='PASS' and item['gate']['selected_nodes']==expected_count and
                item['gate']['protected_failed_nodes']==protections[0],'task gate independently reconstructed')
        self.sections['task-'+str(index)]={'status':'PASS','repository':spec['repo'],'profile':ident,
            'suite_tests':expected_count,'native_runs':2,'junit':primary['junit'],
            'protected_failed_nodes':protections,'source_metadata_base_equal':True,
            'original_production_preserved':True,'packet_and_replay_equal':True,'pinned_distributions':len(packages),
            'collection_runs':3}

    def retention_and_logs(self):
        r=self.result['retention'];pins=self.protocol['preserved_authority']
        require(all(r[k]==pins[k] for k in ['records','CAS_objects','inventory_rows','ledger_sha256']), 'preserved authority counts')
        require(all(r[k] is True for k in ['ledger_exact','CAS_exact','inventory_exact','source_pins_exact','original_FLASH_agrees']),
                'preserved authority checks')
        prior=json.loads(blob(HERE+'RECURSIVE_QUALIFICATION_RECEIPT.json'))['state_snapshot']
        original_raw=blob(HERE+prior['path']);require(sha(original_raw)==prior['sha256'],'prior qualified state archive')
        original=tar_bytes(original_raw)
        ledger=self.raw(PREFIX+'state/metatron-ledger.jsonl')
        require(ledger==original['state/metatron-ledger.jsonl'][0] and sha(ledger)==pins['ledger_sha256'] and
                len(ledger.splitlines())==246,'raw exact original ledger')
        actual={name.removeprefix(PREFIX):raw for name,raw in self.evidence.items() if name.startswith(PREFIX+'state/objects/')}
        expected={name:raw_mode[0] for name,raw_mode in original.items() if name.startswith('state/objects/')}
        require(actual==expected and len(actual)==76 and all(sha(raw)==PurePosixPath(name).name for name,raw in actual.items()),
                'raw exact original CAS objects')
        reuse=self.doc('REGRESSION_REUSE.json');self.same_git(RECORDS+'REGRESSION_REUSE.json',self.raw('REGRESSION_REUSE.json'))
        for group in ['source_pins','retained_logs']:
            for name,digest in reuse[group].items(): require(sha(blob(name))==digest,'reused exact committed bytes '+name)
        old_contract_name=next(name for name in reuse['retained_logs'] if name.endswith('_contracts.log'))
        old_contract_log=blob(old_contract_name).decode()
        original_core=re.findall(r'\((research\.unified_consequence_runtime\.test_[A-Za-z0-9_]+)\.',old_contract_log)
        original_core=[name for name in original_core if not name.endswith('_v3')]
        require(len(original_core)==193 and reuse['original_workflow_conclusion']=='failure',
                'exact original193 core reuse and RED workflow boundary')
        for name,digest in reuse['source_pins'].items():
            require(sha(git('show',reuse['original_source_commit']+':'+name))==digest,
                    'reused original commit source bytes '+name)
        logs={}
        for name,expected_count in [('contracts.log',178),('legacy-contracts.log',18)]:
            raw=self.raw(name).decode();matches=re.findall(r'Ran (\d+) tests? in ([0-9.]+)s\s+OK\s*$',raw)
            require(len(matches)==1 and int(matches[0][0])==expected_count,'complete affected contracts '+name)
            logs[name]={'tests':expected_count,'seconds':float(matches[0][1]),'sha256':sha(self.raw(name))}
        self.sections['retention_and_regressions']={'status':'PASS','records':246,'CAS_objects':76,
            'inventory_rows':70,'original_raw_state_equal':True,'reused_source_pins':len(reuse['source_pins']),
            'reused_original_core_contracts':len(original_core),'original_workflow_conclusion':'failure',
            'reuse_promotes_no_red_or_unknown':True,'logs':logs}

    def run(self):
        self.load();self.sources();self.result_and_runtime();self.task(0,338);self.task(1,768);self.retention_and_logs()
        self.report.update(status='PASS_ADMISSION_ONLY_CI3_ARTIFACT_AUDIT',sections=self.sections,
            evidence_limits=[
                'Structural/hash/XML audit only; no artifact code or original suite executed by auditor.',
                'Actual host executable, stdlib and installed package bytes are not all archived; retained manifests/child claims are linked under exact reviewed frozen controller source.',
                'Pinned package pre-build baseline exists in controller memory; final file inventory and successful source-enforced comparison are retained.',
                'Original_FLASH_agrees is the frozen controller result; raw prior ledger/CAS bytes are independently equal.',
                'Admission-only exposed diagnostics do not establish prospective G2, executed coding-agent comparison, G3-G6 or nonbypassability.'])
        return self.report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--artifact',required=True);parser.add_argument('--out',required=True)
    args=parser.parse_args();audit=Audit(args.artifact)
    try: report=audit.run()
    except Exception as error:
        report=dict(audit.report,status='FAIL_ARTIFACT_AUDIT',sections=audit.sections,
                    error=type(error).__name__+': '+str(error))
    destination=Path(args.out);destination.parent.mkdir(parents=True,exist_ok=True)
    if report['status'].startswith('PASS_'):
        raw_destination=destination.parent/('CI_'+RUN+'_RESULT_RAW.json')
        raw_destination.write_bytes(audit.raw(PREFIX+'RESULT.json'))
        report['raw_result']={'path':str(raw_destination),'archive_member':PREFIX+'RESULT.json',
            'sha256':sha(raw_destination.read_bytes()),'bytes':raw_destination.stat().st_size,
            'exact_raw_bytes':True}
        report['audit_script_sha256']=sha(Path(__file__).read_bytes())
    destination.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':report['status'],'out':str(destination),'sha256':sha(destination.read_bytes()),'error':report.get('error')}))
    raise SystemExit(0 if report['status'].startswith('PASS_') else 1)
