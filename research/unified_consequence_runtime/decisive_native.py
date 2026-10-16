"""Frozen native evidence binding for one finite prospective meta-decision.

No upstream repair is an input. Original V104 constructs candidates; original
MSI V10 ranks them. Native profile authority is reconstructed from raw pytest
receipts, not from a proposed policy's numerical claims. No complete-language
inadequacy or universal intent is inferred from this bounded experiment.
"""
from __future__ import annotations

import ast
import base64
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
import xml.etree.ElementTree as ET

from .developmental_machine import canonical, digest
from . import generic_native_verify as verifier
from .qualify_recursive_frontier import original_candidates

POLICY_PIN = {'repository':'heathsanchez/Minimal-Sufficient-Interface',
    'commit':'56cfd7b523e3592cae4eafa5468f437ccb94dbe9',
    'path':'experiments/policy_language_genesis_cross_domain_v10.py',
    'sha256':'836b8f677f1f252fccad8bf1136f9a966a1f2b2330fa5057c616ee20ddb56608'}
METADATA_PATH = Path(__file__).parent/'archaeology/decisive-native/FRESH_TASK_METADATA.json'
PROTOCOL_PATH = METADATA_PATH.with_name('PROTOCOL.json')
AUTHOR_TEST_BLOBS_PATH = METADATA_PATH.with_name('AUTHOR_TEST_BLOBS.json')


def is_test(name):
    p = Path(name)
    return (p.suffix == '.py' and (p.name == 'conftest.py' or p.name.startswith('test_')
        or p.name.endswith('_test.py') or any(x in ('test','tests','testing') for x in p.parts)))


def overlay_author_tests(base, tests):
    if not tests or any(not is_test(name) for name in tests):
        raise ValueError('only original author Python test files may be overlaid')
    result = dict(base)
    for name, raw in tests.items():
        verifier._path(name)
        if not isinstance(raw, bytes): raise ValueError('exact test bytes required')
        result[name] = raw
    return result


def task_roles(rows):
    """Pre-outcome reassignment after the documented four-task shortfall."""
    return [dict(row,role='TRAINING' if i==0 else 'PROTECTED_FUTURE_'+str(i))
            for i,row in enumerate(rows)]


def passed(receipt):
    counts=receipt.get('junit',{})
    return (receipt.get('status')=='PASS_NATIVE' and receipt.get('exit_code')==0
        and counts.get('tests',0)>0 and counts.get('passed',0)==counts['tests']
        and all(counts.get(k)==0 for k in ('failures','errors','skipped')))


def changed_lines(before, after):
    lines=set()
    def walk(a,b):
        if isinstance(a,ast.AST) and isinstance(b,ast.AST):
            if type(a)!=type(b):
                if hasattr(a,'lineno'): lines.add(a.lineno)
                return
            for field in a._fields:
                left,right=getattr(a,field),getattr(b,field)
                if isinstance(left,(ast.AST,list)): walk(left,right)
                elif left!=right and hasattr(a,'lineno'): lines.add(a.lineno)
        elif isinstance(a,list) and isinstance(b,list):
            if len(a)!=len(b):
                lines.update(x.lineno for x in a if hasattr(x,'lineno'))
            else:
                for x,y in zip(a,b): walk(x,y)
    walk(ast.parse(before),ast.parse(after))
    return tuple(sorted(lines))


def policy_language(repo):
    raw=subprocess.check_output(['git','--no-replace-objects','-C',str(repo),'show',
        POLICY_PIN['commit']+':'+POLICY_PIN['path']],stderr=subprocess.PIPE)
    if digest(raw)!=POLICY_PIN['sha256']: raise ValueError('original MSI policy source changed')
    definitions=[n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef)
                 and n.name in ('policy_programs','pkey')]
    namespace={}
    exec(compile(ast.Module(body=definitions,type_ignores=[]),'<original-msi-v10>','exec'),namespace)
    return namespace['policy_programs'](),namespace['pkey'],dict(POLICY_PIN)


def trace_lines(receipt, source_files):
    text=receipt.get('evidence_text','')
    root=receipt.get('evidence_dir')
    if root:
        for name in ('stdout.log','stderr.log','native.xml'):
            path=Path(root)/name
            if path.is_file(): text+='\n'+path.read_text(errors='replace')
    result={}
    for name in source_files:
        found=re.findall(re.escape(name)+r'(?::|[\", ]+line[ ]+)(\d+)',text)
        result[name]=tuple(sorted({int(x) for x in found}))
    return result


def catalog(repo, commit, production_paths, triskelion, observation, cap=64, allowed=None):
    identity, files, _=verifier._snapshot(repo,commit)
    traces=trace_lines(observation,production_paths)
    rows=[]
    for name in sorted(production_paths):
        if name not in files or is_test(name) or not name.endswith('.py'):
            raise ValueError('metadata production scope unavailable or unsafe')
        before=files[name].decode()
        if allowed is None:
            emitted=original_candidates(triskelion,before,cap=cap)
        else:
            from .decisive_constructor import generate_candidates
            emitted=generate_candidates(triskelion,before,allowed=allowed,cap=cap)
        for selector,builder,text in emitted:
            locations=changed_lines(before,text)
            # New native numeric binding, frozen before targets. These fields
            # do not inherit the original scalar/orbital scientific semantics.
            distance=min((abs(x-y) for x in locations for y in traces[name]),default=1000000)
            mean=sum(locations)/len(locations) if locations else 0
            variance=sum((x-mean)**2 for x in locations)/len(locations) if locations else 0
            candidate={'replacements':[{'path':name,'original_sha256':digest(files[name]),'replacement':text}]}
            rows.append({'id':verifier.fingerprint(candidate),'candidate':candidate,
                'selector':selector,'builder':builder,'path':name,'changed_lines':locations,
                'features':{'K':distance,'c':max(1,len(locations)),'v':variance}})
    return rows


def checked_constructor_context(machine, context_id):
    """Reconstruct a source-native support context, never trusting its scores."""
    started=time.monotonic()
    try:
        context=machine.get(context_id)
        protocol=json.loads(PROTOCOL_PATH.read_text())
        if (digest(METADATA_PATH.read_bytes())!=protocol['frozen_metadata_sha256'] or
                digest(AUTHOR_TEST_BLOBS_PATH.read_bytes())!=protocol['frozen_author_test_blobs_sha256']):
            raise ValueError('constructor support source universe differs from frozen metadata')
        frozen={row['repo']:row for row in task_roles(json.loads(METADATA_PATH.read_text())['selected'])}
        future=context['contract']['repository']
        if (context['catalog_spec']['cap']!=protocol['candidate_cap_per_file'] or
                context.get('protocol_sha256')!=digest(PROTOCOL_PATH.read_bytes())):
            raise ValueError('constructor support differs from frozen source/grammar horizon')
        scope={'contexts':{future:context_id},'protocol_binding':context['contract']['protocol_binding'],
            'candidate_catalog_sha256':digest(canonical(context['catalog']).encode()),
            'author_test_blobs_sha256':digest(AUTHOR_TEST_BLOBS_PATH.read_bytes())}
        return _checked_context(machine,future,scope,frozen)
    finally:
        if hasattr(machine,'costs'):
            machine.costs.append({'phase':'independent_constructor_context_reconstruction',
                'seconds':time.monotonic()-started,'native_calls':0})


def orders(rows, msi):
    programs,key,pin=policy_language(msi)
    result={'COLD_V104_ORDER':[r['id'] for r in rows]}
    for program in programs:
        ident='MSI_V10:'+canonical(program)
        result[ident]=[r['id'] for r in sorted(rows,key=lambda r:(key(program,r['features']),r['id']))]
    return result


def checked_native_receipt(record, machine=None):
    """Read raw independent native evidence without executing project code."""
    receipt=record['receipt']
    if receipt.get('status','').startswith('UNKNOWN_ADMISSION_'):
        if receipt.get('costs',{}).get('native_calls')!=0:
            raise ValueError('invalid rejected-invocation cost')
        return receipt
    if machine is None or not record.get('packet'):
        raise ValueError('content-addressed native evidence packet required')
    packet=machine.get(record['packet'])
    if packet.get('schema')!='UDM_DECISIVE_NATIVE_PACKET_V1':
        raise ValueError('wrong native evidence packet')
    files={name:base64.b64decode(value,validate=True) for name,value in packet['files'].items()}
    for name in files: verifier._path(name)
    raw=json.loads(files['receipt.json'])
    if raw != receipt: raise ValueError('raw native receipt differs')
    if receipt['runner_sha256']!=digest(Path(verifier.__file__).read_bytes()):
        raise ValueError('wrong exact native worker')
    contract=record['contract'];candidate=record['candidate']
    if receipt['contract_sha256']!=verifier.fingerprint(contract) or receipt['candidate_sha256']!=verifier.fingerprint(candidate):
        raise ValueError('native source/program/contract mismatch')
    if receipt['protocol_binding']!=contract['protocol_binding']:
        raise ValueError('native task evidence replayed across protocols')
    authority=record.get('native_suite_authority')
    if authority is not None:
        authority_digest=verifier.validate_native_suite_authority(contract,authority)
        if (receipt.get('native_suite_authority_sha256')!=authority_digest or
                receipt.get('required_test_nodes')!=authority['required_test_nodes']):
            raise ValueError('native receipt protected assertion authority differs')
        if receipt.get('status') in ('PASS_NATIVE','FAIL_NATIVE') and not verifier.required_assertions_satisfied(
                authority,receipt.get('executed_test_nodes'),receipt.get('deselected_test_nodes'),
                receipt.get('executed_test_reports'),receipt.get('junit',{}),require_pass=receipt['status']=='PASS_NATIVE'):
            raise ValueError('native receipt did not execute every protected assertion')
    if (receipt.get('repository')!=contract['repository'] or receipt.get('commit')!=contract['commit'] or
            receipt.get('source')!={key:contract[key] for key in ('git_tree','tracked_tree_sha256','file_count')}):
        raise ValueError('native receipt source differs from the exact contract')
    manifest=json.loads(files['tracked-source-manifest.json'])
    if verifier.fingerprint(manifest)!=contract['tracked_tree_sha256']:
        raise ValueError('native source manifest differs')
    if 'native.xml' in files:
        counts=dict(tests=0,passed=0,failures=0,errors=0,skipped=0)
        try:xml=ET.fromstring(files['native.xml'])
        except ET.ParseError as error:raise ValueError('invalid native XML') from error
        for case in xml.iter('testcase'):
            counts['tests']+=1
            status=next((key for key,tag in (('errors','error'),('failures','failure'),('skipped','skipped'))
                if case.find(tag) is not None),'passed');counts[status]+=1
        if counts!=receipt['junit']:
            raise ValueError('native XML differs from claimed counts')
        if digest(files['native.xml'])!=receipt.get('junit_sha256'):
            raise ValueError('native XML digest differs')
    for stream in ('stdout','stderr'):
        if stream+'_sha256' in receipt and digest(files[stream+'.log'])!=receipt[stream+'_sha256']:
            raise ValueError('native stream digest mismatch')
    if receipt.get('status') in ('PASS_NATIVE','FAIL_NATIVE') and (receipt.get('environment_sha256')!=contract['environment_sha256']
            or verifier.fingerprint(receipt.get('environment'))!=contract['environment_sha256']
            or receipt.get('pytest_import')!=receipt['environment'].get('pytest_import')
            or not receipt.get('import_manifest') or receipt['costs']['native_calls']!=1
            or not all(name in files for name in ('native.xml','stdout.log','stderr.log'))):
        raise ValueError('no independently checked source imports/environment')
    if receipt.get('status')=='PASS_NATIVE' and not passed(receipt):
        raise ValueError('malformed native success')
    counts=receipt['junit']
    if receipt.get('status')=='FAIL_NATIVE' and (receipt.get('exit_code')!=1 or counts['failures']<1
            or counts['errors'] or counts['skipped']):
        raise ValueError('native failure is not a verified failing obligation')
    if receipt.get('generated_module_count'):
        raw=files.get('build-verification/build-receipt.json')
        if raw is None or digest(raw)!=receipt.get('build_verification_sha256'):
            raise ValueError('missing independent native build evidence')
    expected={row['path']:row['sha256'] for row in manifest}
    expected.update({row['path']:digest(row['replacement'].encode()) for row in candidate['replacements']})
    for row in receipt.get('import_manifest',[]):
        if row['path'] in expected and row['sha256']!=expected[row['path']]:
            raise ValueError('native imported bytes differ from exact source/program')
        if row['path'] not in expected and not receipt.get('generated_module_count'):
            raise ValueError('unwarranted generated native import')
    return receipt


def _checked_context(machine, future, scope, frozen):
    context=machine.get(scope['contexts'][future]);contract=context['contract'];spec=frozen[future]
    bounds=context['source_boundaries'];repo=contract['repo_path']
    authority=context.get('native_suite_authority')
    if not authority or authority.get('baseline_commit')!=spec['base_commit']:
        raise ValueError('frozen independent native suite authority required')
    verifier.validate_native_suite_authority(contract,authority)
    if (contract['repository']!=future or contract['protocol_binding']!=scope['protocol_binding']
            or bounds['repository']!=future or bounds['base_commit']!=spec['base_commit']
            or bounds['author_test_head_commit']!=spec['head_commit']
            or bounds['augmented_commit']!=contract['commit']):
        raise ValueError('context task identity differs from frozen frontier')
    identity,files,manifest=verifier._snapshot(repo,contract['commit'])
    if any(contract[key]!=value for key,value in identity.items()):raise ValueError('changed task source')
    _,base,_=verifier._snapshot(repo,spec['base_commit'])
    expected_paths={row['filename']:row for row in spec['files'] if is_test(row['filename'])}
    raw=AUTHOR_TEST_BLOBS_PATH.read_bytes()
    if digest(raw)!=scope['author_test_blobs_sha256']:raise ValueError('frozen author-test authority changed')
    author=json.loads(raw)['subjects'][future]
    if author['head_commit']!=spec['head_commit'] or set(author['test_blobs'])!=set(expected_paths):
        raise ValueError('wrong frozen author-test authority')
    if set(expected_paths)!={row['path'] for row in bounds['author_tests']}:
        raise ValueError('wrong independent author-test channel')
    for row in bounds['author_tests']:
        name=row['path'];raw=files[name]
        blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        if (digest(raw)!=row['sha256'] or blob!=row['git_blob'] or blob!=author['test_blobs'][name]
                or ('sha' in expected_paths[name] and blob!=expected_paths[name]['sha'])):
            raise ValueError('author-test bytes differ from frozen contract')
    if any(name not in expected_paths or digest(files[name])!=value
            for name,value in authority['test_source_sha256'].items()):
        raise ValueError('protected native assertions differ from independent author tests')
    if files!=overlay_author_tests(base,{name:files[name] for name in expected_paths}):
        raise ValueError('author overlay changed production')
    baseline=machine.get(context['baseline_record'])
    if (baseline['contract']!=contract or baseline['candidate']!={'replacements':[]}
            or baseline.get('native_suite_authority')!=authority):
        raise ValueError('wrong native residual source')
    native=checked_native_receipt(baseline,machine)
    if native['status']!='FAIL_NATIVE':raise ValueError('no independently verified native failure')
    spec_catalog=context['catalog_spec']
    paths=[row['filename'] for row in spec['files'] if row['filename'].endswith('.py') and not is_test(row['filename'])]
    if (spec_catalog['repo']!=repo or spec_catalog['commit']!=contract['commit']
            or spec_catalog['production_paths']!=paths):raise ValueError('wrong constructor source scope')
    # Pure source-native regeneration; no additional protected test execution.
    observation=dict(native,evidence_text='\n'.join(base64.b64decode(value).decode(errors='replace')
        for name,value in machine.get(baseline['packet'])['files'].items()
        if name in ('stdout.log','stderr.log','native.xml')))
    rows=catalog(repo,contract['commit'],paths,spec_catalog['triskelion'],observation,cap=spec_catalog['cap'])
    if canonical(rows)!=canonical(context['catalog']):raise ValueError('constructor catalogue differs')
    msi=spec_catalog.get('msi',str(Path(spec_catalog['triskelion']).parent/'msi'))
    if orders(rows,msi)!=context['orders']:raise ValueError('original MSI policy order differs')
    if digest(canonical(rows).encode())!=scope['candidate_catalog_sha256']:
        raise ValueError('native profile catalogue binding differs')
    return context


def _reconstruct_profiles(machine,candidates,futures,evidence_ids):
    nodes={n.id:n for n in machine.log}; profiles={c:{} for c in candidates};scope=None
    frozen_rows=task_roles(json.loads(METADATA_PATH.read_text())['selected'])
    protocol_raw=PROTOCOL_PATH.read_bytes();protocol=json.loads(protocol_raw)
    frozen={row['repo']:row for row in frozen_rows};contexts={}
    for evidence_id in evidence_ids:
        node=nodes[evidence_id]
        if node.kind!='native_acquisition_profile': raise ValueError('wrong profile evidence kind')
        report=machine.get(node.payload['report'])
        if report['candidate'] not in candidates or report['future'] not in futures:
            raise ValueError('wrong candidate/future evidence')
        if scope is None: scope=report['scope']
        if scope!=report['scope']: raise ValueError('mixed source/protocol scopes')
        if scope.get('protocol_sha256')!=digest(protocol_raw):raise ValueError('frozen protocol bytes changed')
        if scope['source_binding']!=digest(canonical(frozen_rows).encode()):raise ValueError('wrong frozen source universe')
        if scope['budget']!=protocol['search_budget']:raise ValueError('wrong frozen acquisition horizon')
        future=report['future']
        if future not in contexts:contexts[future]=_checked_context(machine,future,scope,frozen)
        context=contexts[future];order=context['orders'][report['candidate']]
        if context['catalog_spec']['cap']!=protocol['candidate_cap_per_file']:
            raise ValueError('wrong frozen constructor horizon')
        if report['order']!=order:raise ValueError('reported policy order differs')
        records=[machine.get(key) for key in report['attempts']]
        baseline=machine.get(context['baseline_record'])
        objects={scope['contexts'][future],context['baseline_record'],baseline['packet'],*report['attempts']}
        objects.update(record['packet'] for record in records if record.get('packet'))
        if not objects.issubset(set(scope.get('receipt_objects',()))):
            raise ValueError('native profile transitive evidence is not retained')
        receipts=[]
        for index,record in enumerate(records):
            if (index>=len(order) or record['contract']!=context['contract'] or
                    record.get('native_suite_authority')!=context.get('native_suite_authority') or
                    verifier.fingerprint(record['candidate'])!=order[index]):
                raise ValueError('receipt replayed from another task or policy order')
            if any(passed(row) for row in receipts):raise ValueError('search continued past verified winner')
            receipts.append(checked_native_receipt(record,machine))
        if len(receipts)>scope['budget']: raise ValueError('native acquisition budget exceeded')
        if not any(passed(row) for row in receipts) and len(receipts)!=min(scope['budget'],len(order)):
            raise ValueError('UNKNOWN_SEARCH: declared policy horizon was not fully observed')
        score=[0 if any(passed(r) for r in receipts) else 1,
               sum(r['costs']['native_calls'] for r in receipts)]
        if report['future'] in profiles[report['candidate']]: raise ValueError('duplicate profile')
        profiles[report['candidate']][report['future']]=score
    if any(set(row)!=set(futures) for row in profiles.values()):
        raise ValueError('incomplete profile carrier')
    return {'schema':'UDM_NATIVE_META_PROFILE_EVIDENCE_V1','profiles':profiles,
        'evidence_ids':list(evidence_ids),'scope':scope}


def reconstruct_profiles(machine,candidates,futures,evidence_ids):
    started=time.monotonic()
    try:return _reconstruct_profiles(machine,candidates,futures,evidence_ids)
    finally:
        if hasattr(machine,'costs'):
            machine.costs.append({'phase':'independent_native_profile_reconstruction','seconds':time.monotonic()-started,
                'native_calls':0,'pure_catalogue_regeneration':True})
