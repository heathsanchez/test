"""Independent process transport for the committed once-only V44 screening pool."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import resource
import stat
import subprocess
import time

from research.unified_consequence_runtime.audit_index_v4 import snapshot_indexes, compare_indexes
from research.unified_consequence_runtime.qualify_experiment_interface_v43 import _tree, _git, _retain_indexes

root = Path(os.environ['UDM_REPO'])
records = Path(os.environ['UDM_RECORDS'])
out = Path(os.environ['UDM_OPERATOR'])
source_commit = '77c2ef539aed252e037c5c0a67dd62816d5306b4'
authority_pin = '8c1ae9852b4cc60fb8773863b790c18b0b9dc4c1733fddb96e4a577e5a0dc0b0'
prequery_commit = 'b112b69dcda962c9323cbcd13aefdcd580a5449a'
authority = records/'SCREENING_AUTHORITY.json'
sha = lambda raw: hashlib.sha256(raw).hexdigest()
write = lambda path, value: Path(path).write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')

def inventory(tree):
    rows = []
    for name, record in sorted(tree.items()):
        path = root/name
        if record['mode'] == '120000':
            if not path.is_symlink():raise ValueError('original source link changed')
            raw = os.readlink(path).encode()
        else:
            if path.is_symlink() or not path.is_file():raise ValueError('original source type changed')
            raw = path.read_bytes()
            if bool(path.stat().st_mode&0o111) != (record['mode']=='100755'):
                raise ValueError('original source executable mode changed')
        if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=record['oid']:
            raise ValueError('original source differs from committed Git object')
        rows.append({'path':name,'mode':record['mode'],'sha256':sha(raw)})
    return rows

if any((out/name).exists() for name in ('ORDERED_PROCESS_COSTS.json','SCREENING_ACTOR_ATTESTATION.json','SCREENING_SOURCE_BEFORE.json')):
    raise ValueError('refusing to overwrite original screening transport evidence')
before_indexes = snapshot_indexes(root)
_retain_indexes(before_indexes,out/'source-index-before-screening')
if _git(root,'rev-parse','HEAD').decode().strip()!=source_commit:
    raise ValueError('screening source differs from externally supplied commit')
tree = _tree(root,source_commit,allow_links=True)
source_snapshot = {'source_commit':source_commit,'files':inventory(tree)}
snapshot_path = out/'SCREENING_SOURCE_BEFORE.json'
write(snapshot_path,source_snapshot)
snapshot = {'path':str(snapshot_path),'sha256':sha(snapshot_path.read_bytes())}
if sha(authority.read_bytes())!=authority_pin:
    raise ValueError('committed screening authority differs from supplied pin')
if _git(root,'show',source_commit+':'+authority.relative_to(root).as_posix())!=authority.read_bytes():
    raise ValueError('screening authority not exact committed source')
ticket = json.loads(authority.read_text())
pool_path = root/ticket['pool']['path']
if sha(pool_path.read_bytes())!=ticket['pool']['sha256']:
    raise ValueError('frozen pool differs from committed authority')
pool = json.loads(pool_path.read_text())['pool']
requests = sorted((out/'requests').glob('request-*.json'))
if len(pool)!=2 or len(requests)!=len(pool):
    raise ValueError('externally frozen complete two-case pool required')
for i,path in enumerate(requests):
    if path.name!='request-'+format(i,'03d')+'.json' or json.loads(path.read_text())!={
            'pool_index':i,'spec':pool[i],'protocol_binding':authority_pin}:
        raise ValueError('exact frozen request/order differs')
rows=[]
started=time.monotonic()
completed=False
failure=None
try:
    for i,request in enumerate(requests):
        destination=Path(ticket['output_root'])/('case-'+format(i,'03d'))
        if destination.exists():raise ValueError('once-only case destination already exists')
        command=[os.environ['UDM_CONTROLLER_PYTHON'],'-B','-m',
                 'research.unified_consequence_runtime.qualify_native_frontier_v44',
                 '--screen-spec',str(request),'--authority',str(authority),
                 '--authority-sha256',authority_pin,'--runtimes',os.environ['UDM_RUNTIME_PATHS'],
                 '--out',str(destination)]
        beginning=datetime.datetime.now(datetime.timezone.utc).isoformat()
        case_started=time.monotonic()
        unix_started=time.time()
        cpu_before=resource.getrusage(resource.RUSAGE_CHILDREN)
        print(json.dumps({'event':'CASE_STARTED','index':i,'started_at_utc':beginning}),flush=True)
        with (out/('screen-'+format(i,'03d')+'.stdout')).open('xb') as stdout, (out/('screen-'+format(i,'03d')+'.stderr')).open('xb') as stderr:
            process=subprocess.run(command,cwd=root,stdout=stdout,stderr=stderr)
        cpu_after=resource.getrusage(resource.RUSAGE_CHILDREN)
        row={'index':i,'index_label':format(i,'03d'),'command':command,
             'request_sha256':sha(request.read_bytes()),'started_at_utc':beginning,
             'started_at_unix':unix_started,'returncode':process.returncode,
             'wall_seconds':time.monotonic()-case_started,
             'child_user_cpu_seconds':cpu_after.ru_utime-cpu_before.ru_utime,
             'child_system_cpu_seconds':cpu_after.ru_stime-cpu_before.ru_stime}
        rows.append(row)
        write(out/'ORDERED_PROCESS_COSTS.json',{'schema':'UDM_V44_SCREENING_OPERATOR_PROCESS_COSTS_V1',
            'authority_sha256':authority_pin,'source_commit':source_commit,'source_snapshot':snapshot,
            'cases':rows,'completed':len(rows)==len(requests),'retries_performed':False,
            'wall_seconds':time.monotonic()-started,'nested_intervals_not_additive':True,
            'no_retry_or_substitution':True})
        print(json.dumps({'event':'CASE_PROCESS_FINISHED','index':i,'returncode':process.returncode,
                          'wall_seconds':row['wall_seconds']}),flush=True)
        # Read only public transport/meter. Native reports, raw source and future
        # PASS-versus-FAIL status remain sealed to root and the learner.
        meter_path=Path(ticket['output_root'])/'SCREENING_METER.json'
        meter=json.loads(meter_path.read_text())
        if (process.returncode or meter.get('pending') is not None or not meter.get('accounting_complete')
                or len(meter.get('cases',[]))!=i+1 or not (destination/'SCREENING_ENVELOPE.json').is_file()):
            raise ValueError('original screening meter/process incomplete; no retry or resampling permitted')
    completed=True
except BaseException as error:
    failure=type(error).__name__+': '+str(error)
    raise
finally:
    after_source={'source_commit':source_commit,'files':inventory(tree)}
    write(out/'SCREENING_SOURCE_AFTER.json',after_source)
    after_indexes=snapshot_indexes(root)
    _retain_indexes(after_indexes,out/'source-index-after-screening')
    changes=compare_indexes(before_indexes,after_indexes)
    source_unchanged=after_source==source_snapshot
    write(out/'SOURCE_INDEX_SCREENING_AUDIT.json',{'status':'PASS_SOURCE_AND_INDEX_BYTES' if source_unchanged and not changes else 'UNKNOWN_SOURCE_OR_INDEX_CHANGED',
        'before_indexes':before_indexes,'after_indexes':after_indexes,'index_changes':changes,
        'source_unchanged':source_unchanged,'files':len(tree),'restored_any_index':False})
    manifest={'schema':'UDM_V44_SCREENING_OPERATOR_PROCESS_COSTS_V1',
        'authority_sha256':authority_pin,'source_commit':source_commit,'source_snapshot':snapshot,
        'cases':rows,'completed':completed,'retries_performed':False,
        'wall_seconds':time.monotonic()-started,'nested_intervals_not_additive':True,
        'no_retry_or_substitution':True,'failure':failure}
    write(out/'ORDERED_PROCESS_COSTS.json',manifest)
    attestation={'schema':'UDM_V44_SCREENING_ACTOR_ATTESTATION_V1',
        'actor_identity':'/root/qualify_native_bootstrap_v44 independent screening executor running the exact frozen q44 admission-only CLI',
        'source_commit':source_commit,'prequery_commit':prequery_commit,'authority_sha256':authority_pin,
        'independent_screener':True,'search_or_policy_outcomes_accessed':False,
        'learner_future_source_accessed':False,'native_test_reruns_or_case_retries_performed':False,
        'controller_manifest_sha256':sha((out/'ORDERED_PROCESS_COSTS.json').read_bytes()),
        'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'completed_fixed_pool':completed,'source_unchanged':source_unchanged,'index_changes':changes,
        'no_retry_scope':'Every fixed pool member attempted once in index order. Original mandatory independent recollection and native reexecution are included in the frozen protocol, not extra experiments. No task repair, search, constructor, method policy, coding agent or learner role release was invoked.',
        'exposure_boundary':'Raw source/native content is confined to the original screening executables and retained private dossiers. Executor reads only committed metadata, public envelopes/meter and mechanical process status; root and learner receive no raw native status or future trace.',
        'host_isolation_boundary':'Bounded actor/process attestation with retained evidence; no global absence-of-other-processes or non-bypassable containment proof.'}
    write(out/'SCREENING_ACTOR_ATTESTATION.json',attestation)
    pins={'source_commit':source_commit,'prequery_commit':prequery_commit,'screening_authority_sha256':authority_pin,
        'controller_manifest':{'path':str(out/'ORDERED_PROCESS_COSTS.json'),'sha256':sha((out/'ORDERED_PROCESS_COSTS.json').read_bytes())},
        'attestation':{'path':str(out/'SCREENING_ACTOR_ATTESTATION.json'),'sha256':sha((out/'SCREENING_ACTOR_ATTESTATION.json').read_bytes())}}
    write(out/'SCREENING_PARENT_PINS.json',pins)
    print(json.dumps({'event':'ORDERED_SCREENING_TRANSPORT_FINISHED','completed':completed,
                      'cases':len(rows),'wall_seconds':manifest['wall_seconds'],'source_unchanged':source_unchanged,
                      'index_changes':changes,'failure':failure,'pins':pins}),flush=True)
