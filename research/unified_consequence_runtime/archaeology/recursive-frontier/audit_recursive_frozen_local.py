"""Offline evidence audit only. It never imports/executes native project code."""
from pathlib import Path, PurePosixPath
import argparse, datetime, hashlib, io, json, re, subprocess, tarfile, xml.etree.ElementTree as ET

def sha(raw): return hashlib.sha256(raw).hexdigest()
def canon(value, ascii=True): return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False,ensure_ascii=ascii).encode()
def fp(value): return sha(canon(value))
def load(p): return json.loads(Path(p).read_text())
def require(condition, reason):
    if not condition: raise AssertionError(reason)

def tar_source(path):
    rows=[]; files={}
    with tarfile.open(path) as packet:
        commit=packet.pax_headers.get('comment')
        for entry in packet.getmembers():
            p=PurePosixPath(entry.name)
            require(not p.is_absolute() and '..' not in p.parts,'unsafe source archive member')
            if entry.isdir():continue
            require(entry.isfile(),'nonregular source archive member')
            raw=packet.extractfile(entry).read();files[str(p)]=sha(raw)
            blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
            rows.append({'path':str(p),'mode':'100755' if entry.mode&0o111 else '100644','blob':blob,'sha256':sha(raw)})
    rows.sort(key=lambda r:r['path'])
    hierarchy={}
    for row in rows:
        parent=hierarchy;parts=row['path'].split('/')
        for part in parts[:-1]:parent=parent.setdefault(part,{})
        parent[parts[-1]]=row
    def tree(items):
        body=b''
        for name,value in sorted(items.items(),key=lambda row:row[0]+('/' if 'blob' not in row[1] else '')):
            directory='blob' not in value
            mode='40000' if directory else value['mode'];digest=tree(value) if directory else value['blob']
            body+=mode.encode()+b' '+name.encode()+b'\0'+bytes.fromhex(digest)
        return hashlib.sha1(b'tree '+str(len(body)).encode()+b'\0'+body).hexdigest()
    return {'commit':commit,'git_tree':tree(hierarchy),'tracked_tree_sha256':fp(rows),'file_count':len(rows),'file_hashes':files}

def parse_ledger(raw):
    rows=[];known=set()
    for line in raw.splitlines():
        record=json.loads(line); ident=record.pop('id');require(ident==sha(canon(record,False)),'node id hash mismatch')
        require(ident not in known,'duplicate canonical node');require(len(set(record['premises']))==len(record['premises']),'duplicate premises')
        require(set(record['premises'])<=known,'unknown or forward premise')
        if record['kind']=='revoke':require(record['payload']['target'] in known,'unknown revocation target')
        rows.append(dict(record,id=ident));known.add(ident)
    revoked={r['payload']['target'] for r in rows if r['kind']=='revoke'};live=set()
    for r in rows:
        if r['kind']!='revoke' and r['id'] not in revoked and set(r['premises'])<=live:live.add(r['id'])
    return rows,live

def junit(p):
    counts=dict(tests=0,passed=0,failures=0,errors=0,skipped=0)
    if not p.exists():return counts
    for case in ET.parse(p).getroot().iter('testcase'):
        counts['tests']+=1;kind=next((k for k,t in (('errors','error'),('failures','failure'),('skipped','skipped')) if case.find(t) is not None),'passed');counts[kind]+=1
    return counts

def audit(root,source_repo,expected):
    root=Path(root);source_repo=Path(source_repo);r=load(root/'RESULT.json');checks=[];details={}
    def gate(name,fn):
        try:value=fn();checks.append({'gate':name,'status':'PASS','details':value})
        except Exception as e:checks.append({'gate':name,'status':'FAIL','error':type(e).__name__+': '+str(e)})
    frozen=r['freeze'];binding=sha(canon(frozen)+b'\n')
    def freeze_check():
        require(r['source_commit']==expected==frozen['source_commit'],'wrong exact source')
        require(binding==r['freeze_sha256'],'freeze binding mismatch')
        for path,digest in frozen['files'].items():
            raw=subprocess.check_output(['git','--no-replace-objects','-C',str(source_repo),'show',expected+':'+path],stderr=subprocess.PIPE)
            require(sha(raw)==digest,'frozen source mismatch: '+path)
        require(frozen['frozen_at_utc']<=r['started_at_utc'],'native qualification started before freeze')
        return {'source_commit':expected,'files':len(frozen['files']),'freeze_sha256':binding,'chronology':'COMMITTED_CONTROL_FLOW_PLUS_DECLARED_PROCESS; NOT_ENFORCED_INFORMATION_FLOW'}
    gate('exact_frozen_source_and_chronology',freeze_check)
    sources={}
    def archive_check():
        for name in ('control','target'):
            if not (root/name/'contract.json').exists():continue
            contract=load(root/name/'contract.json');info=tar_source(root/name/'pinned-source.tar.gz');sources[name]=(contract,info)
            for key in ('commit','git_tree','tracked_tree_sha256','file_count'):require(contract[key]==info[key],'native source identity mismatch '+name+':'+key)
            require(contract['protocol_binding']==binding,'contract freeze mismatch')
            archive=r[name+'_setup']['pinned_source_archive'];raw=(root/name/'pinned-source.tar.gz').read_bytes()
            require(archive['sha256']==sha(raw) and archive['bytes']==len(raw),'native source archive digest mismatch')
        return {name:{key:info[key] for key in ('commit','git_tree','tracked_tree_sha256','file_count')} for name,(_,info) in sources.items()}
    gate('hash_only_pinned_native_source_archives',archive_check)
    receipts=[]
    def native_check():
        paths=sorted(root.glob('*-evidence/native-runs/*/receipt.json'))+sorted(root.glob('restart-native/native-runs/*/receipt.json'))
        for path in paths:
            rec=load(path);name='target' if path.parts[-4]=='target-evidence' else 'control';contract,info=sources[name]
            require(rec['schema']=='UDM_GENERIC_NATIVE_PYTEST_V1','wrong native schema')
            require(rec['repository']==contract['repository'] and rec['commit']==contract['commit'],'wrong native source scope')
            require(rec['contract_sha256']==fp(contract) and rec['protocol_binding']==binding,'wrong native contract binding')
            require(rec['runner_sha256']==frozen['files']['research/unified_consequence_runtime/generic_native_verify.py'],'wrong verifier source')
            require(rec['environment_sha256']==contract['environment_sha256']==fp(rec['environment']),'wrong native environment')
            require(rec['pytest_import']==rec['environment']['pytest_import'],'pytest distribution import mismatch')
            for stream in ('stdout','stderr'):require(sha((path.parent/(stream+'.log')).read_bytes())==rec[stream+'_sha256'],'native stream digest mismatch')
            counts=junit(path.parent/'native.xml');require(counts==rec['junit'],'actual JUnit differs from receipt')
            if 'junit_sha256' in rec:require(sha((path.parent/'native.xml').read_bytes())==rec['junit_sha256'],'JUnit digest mismatch')
            for imported in rec['import_manifest']:require(info['file_hashes'].get(imported['path'])==imported['sha256'],'native imported bytes mismatch')
            require(rec['costs']['native_calls']==1 and rec['costs']['horizon_seconds']==7,'native call/horizon mismatch')
            if rec['status']=='PASS_NATIVE':require(counts['passed']==346 and counts==dict(tests=346,passed=346,failures=0,errors=0,skipped=0) and rec['exit_code']==0,'not real full control PASS')
            else:require(name=='target' and rec['status']=='UNKNOWN_NATIVE_ERROR' and counts['tests']==0 and rec['exit_code']==4,'unexpected negative native boundary')
            receipts.append({'path':str(path.relative_to(root)),'sha256':sha(path.read_bytes()),'receipt':rec})
        require(len(receipts)>=8,'missing native receipt evidence')
        return {'receipts':len(receipts),'control_passes':sum(x['receipt']['status']=='PASS_NATIVE' for x in receipts),'target_unknowns':sum(x['receipt']['status']=='UNKNOWN_NATIVE_ERROR' for x in receipts),'actual_junit_verified':True,'native_seconds':sum(x['receipt']['costs']['native_seconds'] for x in receipts)}
    gate('actual_native_JUnit_logs_imports_environment_and_costs',native_check)
    raw=(root/'state/metatron-ledger.jsonl').read_bytes();rows,live=parse_ledger(raw);nodes={x['id']:x for x in rows};original_raw=None
    def state_check():
        nonlocal original_raw
        archive=subprocess.check_output(['git','--no-replace-objects','-C',str(source_repo),'show',expected+':research/unified_consequence_runtime/archaeology/programme-closure/QUALIFIED_NATIVE_STATE.tar.gz'])
        require(sha(archive)=='5086b999e3f11b08524ea201cb8c2ac24842e6e288a56d17ef3c06c2c281a09d','wrong original state snapshot')
        with tarfile.open(fileobj=io.BytesIO(archive)) as t:original_raw=t.extractfile('state/metatron-ledger.jsonl').read()
        original,old_live=parse_ledger(original_raw);require(len(original)==224 and raw.startswith(original_raw),'historical224 record bytes changed');require(old_live<=live,'unrelated historical warrants lost')
        objects=list((root/'state/objects').iterdir())
        for obj in objects:require(re.fullmatch('[0-9a-f]{64}',obj.name) and sha(obj.read_bytes())==obj.name,'corrupt CAS object');json.loads(obj.read_bytes())
        require(r['retention']['ledger_sha256']==sha(raw),'reported final ledger hash differs')
        closure=load(root/'state/native-frontiers.json');require(closure['ledger_sha256']==sha(raw),'stale FLASH frontier projection')
        return {'ledger_records':len(rows),'original_prefix_records':len(original),'CAS_objects':len(objects),'live_records':len(live),'ledger_sha256':sha(raw)}
    gate('all_ledger_hashes_premises_CAS_and_exact224prefix',state_check)
    def cap_check():
        caps=[x for x in rows if x['kind']=='executable_capability' and x['payload'].get('operation')=='native.pytest_suite'];require(len(caps)==2,'expected original and freshly restored native capability')
        old,new=sorted(caps,key=lambda x:x['payload']['generation']);require(old['payload']['generation']==1 and new['payload']['generation']==2,'wrong fresh generations');require(new['payload']['supersedes']==old['id'],'restoration does not supersede oldcap')
        require(old['id'] not in live and new['id'] in live,'wrong restored capability liveness')
        require(old['payload']['program']==new['payload']['program']==fp({'replacements':[]}),'control was not empty original activation')
        require(old['payload']['transition']==new['payload']['transition']=='ACTIVATION','supplied control relabeled developmental acquisition')
        nonces=[]
        for cap in (old,new):
            p=cap['payload'];support=nodes[p['dependencies'][0]];verified=nodes[p['evidence'][0]];bundle=load(root/'state/objects'/verified['payload']['receipt']);nonces.append(bundle['nonce'])
            require(bundle['generation']==p['generation'] and bundle['program']==p['program'] and len(bundle['runs'])==2,'bad native evidence bundle')
            require(verified['premises']==[support['id']],'wrong native verification lineage')
            for rec in bundle['runs']:require(any(x['receipt']==rec for x in receipts),'native admission has no matching raw verification')
        require(nonces[0]!=nonces[1],'restoration reused nonce')
        require(r['ancestor_withdrawal']['blocked'] and r['ancestor_withdrawal']['route']['status']=='UNKNOWN_SEARCH','ancestor withdrawal failed')
        require(r['wrong_authority_control']['status']=='UNKNOWN_SEARCH','wrong authority route admitted')
        require(r['unrelated_withdrawal_native']['status']=='PASS_NATIVE','unrelated withdrawal damaged native route')
        require(load(root/'restart-spec.json')['capability']==new['id'],'restart does not use freshly restored capability')
        return {'old_capability':old['id'],'restored_capability':new['id'],'new_generation':2,'fresh_nonce':True}
    gate('exact_withdrawal_fresh_restoration_unrelated_survival',cap_check)
    def restart_check():
        cold=load(root/'cold-restart.json');require(cold==r['cold_restart'],'restart report mismatch');require(cold['status']=='PASS' and cold['process_id']!=r['process_id'],'not separate-process restart')
        require(any(x['receipt']==cold['native'] for x in receipts),'no matching raw native restart JUnit')
        require(cold['native']['status']=='PASS_NATIVE','restart native execution not PASS')
        return {'native_passed':cold['native']['junit']['passed'],'restart_process_id':cold['process_id'],'coordinator_process_id':r['process_id'],'consequence':cold['consequence']}
    gate('real_separate_process_native_restart_execution',restart_check)
    def retention_check():
        ident=r['cold_restart']['consequence'];require(ident in nodes,'fresh child restart consequence absent from final canonical ledger: '+ident);require(ident in live,'fresh child restart consequence not live');return {'consequence':ident,'live':True}
    gate('append_only_retention_after_parent_continuation',retention_check)
    def boundary_check():
        require(r['verdicts']['O1_O2_O3_RECURSIVE_CAUSALITY']=='UNKNOWN' and r['verdicts']['PROSPECTIVE_NATIVE_DISCOVERY']=='UNKNOWN' and r['verdicts']['EXTERNAL_ENFORCEMENT']=='UNKNOWN','overpromoted scientific or security result')
        if 'cold' in r['conditions'] and 'native' in r['conditions']['cold']:
            for condition in ('cold','sham','equally_informed_executable_ledger'):
                rec=r['conditions'][condition]['native'];require(rec['status']=='UNKNOWN_NATIVE_ERROR' and rec['junit']['tests']==0,'target environmental UNKNOWN not preserved')
            require(all('NOT_RUN' in r['conditions'][c]['status'] for c in ('O1_only','O1_O2','O1_O2_O3')),'missing acquisitions falsely run')
        return {'recursive_growth':'UNKNOWN','prospective_growth':'UNKNOWN','comparative_developmental_advantage':'UNKNOWN','raw_comparative_label':r['verdicts']['COMPARATIVE_ADVANTAGE'],'raw_label_scope':'Native UNKNOWN-status parity only; no protected-outcome or developmental-cost advantage comparison.'}
    gate('honest_recursive_prospective_comparator_authority_boundaries',boundary_check)
    missing=r['cold_restart']['consequence'];orphan=root/'state/flash-events'/missing/'evidence.json'
    finding={'status':'FAILED_APPEND_ONLY_RESTART_RETENTION' if missing not in nodes else 'PASS','consequence':missing,'in_final_ledger':missing in nodes,'raw_orphan_event_retained':orphan.exists(),'orphan_evidence_sha256':sha(orphan.read_bytes()) if orphan.exists() else None,'source_cause':'Controller continues using stale parent Machine.log after child commits its consequence; later parent flush overwrites the fresh child entry.','minimal_fix':'Reload canonical Machine immediately after child returns, preserve already charged parent costs, require child entry before and after subsequent parent write.'}
    return {'schema':'udm.recursive.offline-independent-local-review.v1','reviewed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'mode':'OFFLINE_ONLY_NO_NATIVE_SCIENCE_RERUN','source_commit':expected,'packet':str(root),'status':'FAIL_COMPLETE_RESTART_RETENTION_WITH_NATIVE_COMPONENT_PASSES' if any(x['status']=='FAIL' for x in checks) else 'PASS_BOUNDED_PACKET','checks':checks,'retention_finding':finding,'native_target_source_semantics_inspected':False,'native_source_hash_verification_only':True,'new_experiments_executed':False}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--packet',required=True);p.add_argument('--source-repo',required=True);p.add_argument('--expected-commit',required=True);p.add_argument('--out',required=True);a=p.parse_args();r=audit(a.packet,a.source_repo,a.expected_commit);Path(a.out).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'status':r['status'],'checks':[(x['gate'],x['status']) for x in r['checks']],'out':a.out}))
