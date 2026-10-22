"""Independent retained V44 screening audit; no target code or network runs.

The final V43 source/native/runtime auditor is reused byte-exactly. V44 changes
outer transport schemas, adds actual metadata-backend cost accounting and closes
metadata/selection premises using pinned data-only artifact predicates.
"""
from __future__ import annotations
import ast
import copy
import hashlib
import importlib.metadata
import importlib.util
import inspect
import json
import math
import os
from pathlib import Path
import re
import sys
from types import FunctionType, SimpleNamespace

HERE=Path(__file__).resolve().parent
OLD=Path('/workspace/qualification/experiment-interface-v43-screening-audit-preparation')
PROTOCOL=json.loads((HERE/'PREIMPLEMENTATION_PROTOCOL.json').read_text())
_REVISION=json.loads((HERE/'REUSE_REVISION001.json').read_text())
_PROOF_PATH='/workspace/qualification/native-bootstrap-v44-independent-audit/audit_v44.py'
if (_REVISION['schema']!='UDM_V44_SCREENING_PURE_PREDICATE_REUSE_REVISION001'
        or _REVISION['source_path']!=_PROOF_PATH
        or _REVISION['protocol_sha256']!=hashlib.sha256((HERE/'PREIMPLEMENTATION_PROTOCOL.json').read_bytes()).hexdigest()
        or _REVISION['old_sha256']!=PROTOCOL['trusted_reuse'][_PROOF_PATH]
        or hashlib.sha256(Path(_REVISION['correction']['path']).read_bytes()).hexdigest()!=_REVISION['correction']['sha256']):
    raise ValueError('explicit pure predicate revision lineage differs')
PROTOCOL=copy.deepcopy(PROTOCOL)
PROTOCOL['trusted_reuse'][_PROOF_PATH]=_REVISION['new_sha256']


def sha(raw):return hashlib.sha256(raw).hexdigest()


def _load(path,name):
    path=Path(path)
    if path.is_symlink() or sha(path.read_bytes())!=PROTOCOL['trusted_reuse'][str(path)]:
        raise ValueError('frozen trusted auditor dependency differs: '+str(path))
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


old=_load(OLD/'audit_retained.py','v44_reused_v43_screening')
proof=_load(Path('/workspace/qualification/native-bootstrap-v44-independent-audit/audit_v44.py'),'v44_metadata_data_proof')
canonical,fp,number,count,require=old.canonical,old.fp,old.number,old.count,old.require
MODE,COVERAGE=old.MODE,old.COVERAGE
BOOTSTRAP_COVERAGE=('Original-backend metadata observations and independent verification in this screening interval; '
    'native counters remain separate and parent wall time includes these nested operations.')
_SCHEMAS={'UDM_ADMISSION_ONLY_CASE_V43':'UDM_ADMISSION_ONLY_CASE_V44',
          'UDM_SEALED_ADMISSION_ENVELOPE_V43':'UDM_SEALED_ADMISSION_ENVELOPE_V44',
          'UDM_ORDERED_SCREENING_METER_V43':'UDM_ORDERED_SCREENING_METER_V44',
          'UDM_NATIVE_CLI_AUTHORITY_V43':'UDM_NATIVE_CLI_AUTHORITY_V44',
          'UDM_V43_OFFLINE_RETAINED_SCREENING_DOSSIER_V1':'UDM_V44_OFFLINE_RETAINED_SCREENING_DOSSIER_V1'}


def _code(code):
    return code.replace(co_consts=tuple(_code(v) if isinstance(v,type(code))
        else _SCHEMAS.get(v,v) if isinstance(v,str) else v for v in code.co_consts))


def _bind(function,namespace):
    value=FunctionType(_code(function.__code__),namespace,function.__name__,function.__defaults__,function.__closure__)
    value.__kwdefaults__=function.__kwdefaults__;return value


def verify_freeze():
    value=json.loads((HERE/'AUDITOR_FREEZE.json').read_text())
    for name,digest in value['source_files_sha256'].items():
        require(sha(Path(name).read_bytes())==digest,'frozen V44 auditor source differs: '+name)


def bootstrap_costs(report):
    before,after=(report['bootstrap_attempts'][key] for key in ('before','after'))
    for row in (before,after):
        count(row['backend_calls']);require(number(row['backend_seconds']),'invalid bootstrap backend seconds')
    require(after['backend_calls']>=before['backend_calls'] and after['backend_seconds']>=before['backend_seconds'],
            'bootstrap counters rolled backward')
    require(isinstance(before['records'],list) and isinstance(after['records'],list)
            and after['records'][:len(before['records'])]==before['records'],'bootstrap attempt record prefix changed')
    require(number(report['total_wall_seconds']),'invalid bootstrap inclusive parent interval')
    return {'coverage':BOOTSTRAP_COVERAGE,'inclusive_parent_wall_seconds':report['total_wall_seconds'],
        'backend_calls':after['backend_calls']-before['backend_calls'],
        'backend_seconds':after['backend_seconds']-before['backend_seconds']}


_public=_bind(old.public_fields,dict(vars(old)))


def public_fields(report):
    return dict(_public(report),bootstrap_costs=bootstrap_costs(report))


validate_meter=_bind(old.validate_meter,dict(vars(old)))
validate_request=old.validate_request
validate_context_bytes=old.validate_context_bytes
audit_native=old.audit_native
audit_partial_packets=old.audit_partial_packets
require_closed_dossier=old.require_closed_dossier


def validate_exposure(plan,prior):
    require(set(prior['repositories'])<=set(plan['historically_touched_repository_exclusions']),
            'complete prior source exposure union omitted')
    require(not set(prior['repositories'])&set(plan['repository_universe_fixed_before_github_queries']),
            'exposed source reused as a new prospective frontier')


def audit_metadata(plan,pre,metadata,pool):
    prior=json.loads((_ARGS.records/'PRIOR_EXPOSURE.json').read_text())
    validate_exposure(plan,prior)
    return old.audit_metadata(plan,pre,metadata,pool)


def validate_binding(binding,context):
    keys=('capability_id','generation','consequence_id','request_sha256','observation_sha256')
    require(set(binding)==set(keys)|{'environment_selection_id'} and all(binding[k]==context[k] for k in keys),
            'bootstrap binding differs from exact instrument invocation')
    require({binding['capability_id'],binding['consequence_id'],binding['environment_selection_id']}<=context['live_ids'],
            'bootstrap causal ancestor is withdrawn')
    request,observation,selected=context['request'],context['observation'],context['selected']
    require(request['commit']==context['base_commit'] and request['protocol_binding']==context['protocol_binding']
            and observation['source_identity']==context['baseline_source'],'bootstrap source/protocol scope replay')
    require(selected['id']==binding['environment_selection_id'] and selected['kind']=='native_environment_selection_v44'
            and selected['premises']==[binding['capability_id'],binding['consequence_id']],
            'selected environment lacks exact bootstrap ancestors')
    payload=selected['payload']
    require(payload['binding']=={k:v for k,v in binding.items() if k!='environment_selection_id'}
            and all(payload[k]==context[k] for k in ('contract_sha256','authority_sha256','policy_sha256')),
            'selected native environment has another source or independent policy')


def validate_invocation_binding(binding,cap,witness,receipt,request):
    require(witness['kind']=='verified_consequence' and witness['premises']==[binding['capability_id']]
            and receipt['instrument']==binding['capability_id']
            and receipt['generation']==binding['generation']==cap['generation']
            and cap['scope']['request_sha256']==fp(request),
            'metadata witness belongs to another source/instrument/generation')


class LocalStore:
    """Read-only adapter for already retained bytes; links never become files."""
    def __init__(self,root,a):
        self.root,self.a=Path(root).absolute(),a;self.entries={}
        for path in self.root.rglob('*'):
            if path.is_symlink():self.entries[str(path)]={'kind':'symlink','target':os.readlink(path)}
            elif path.is_file():self.entries[str(path)]={'kind':'file'}
    def raw(self,name):
        require(name in self.entries and self.entries[name]['kind']=='file','nonregular/outside retained evidence: '+str(name))
        return self.a.read(name)
    def js(self,name):return json.loads(self.raw(name))
    def matching(self,suffix):return sorted(n for n in self.entries if n==suffix or n.endswith('/'+suffix))
    def path_for_absolute(self,path):
        require(str(path) in self.entries,'artifact outside retained source case: '+str(path));return str(path)


class SourceStore:
    def __init__(self,root,a):self.root,self.a=Path(root),a
    def raw(self,name):
        require(proof.old.safe_name(name),'noncanonical installed source path')
        return self.a.read(self.root/name)
    def js(self,name):return json.loads(self.raw(name))


def runtime_bytes(a,path):
    """Only an independently bound runtime may resolve its original aliases."""
    return a.read(Path(path).resolve())


def _profile_environment(a,identity,observation,runtime_inventory,catalog):
    """Reconstruct build-interpreter/package/stdlib bytes, without running it."""
    interpreter=Path(observation['interpreter'])
    require(runtime_inventory['catalog_sha256']==fp(catalog)
            and set(runtime_inventory['runtimes'])=={p['id'] for p in catalog['profiles']},
            'metadata runtime inventory differs from the complete independent catalog')
    matches=[(ident,row) for ident,row in runtime_inventory['runtimes'].items() if row['interpreter']==str(interpreter)]
    require(len(matches)==1,'metadata interpreter not independently frozen before source access')
    ident,record=matches[0];profile=next(p for p in catalog['profiles'] if p['id']==ident)
    environment=observation['environment'];runtime=identity._runtime_helper()
    require(environment['executable']==str(interpreter) and sha(runtime_bytes(a,interpreter))==environment['executable_sha256']==record['identity']['executable_sha256'],
            'metadata interpreter bytes differ from independent runtime freeze')
    stdlib,_=runtime.source_walk(record['import_roots'])
    require(stdlib==record['stdlib_files'] and fp(stdlib)==record['identity']['stdlib_manifest_sha256'],
            'metadata interpreter standard library changed')
    version=record['identity']['version_info'];site=interpreter.parent.parent/'lib'/('python'+'.'.join(map(str,version[:2])))/'site-packages'
    rows=[];found={}
    for dist in sorted(importlib.metadata.distributions(path=[str(site)]),key=lambda d:(d.metadata['Name'] or '').lower()):
        files=[];name=dist.metadata['Name'];normalized=re.sub(r'[-_.]+','-',name or '').lower()
        require(normalized not in found,'duplicate installed build distribution')
        for entry in sorted(dist.files or [],key=str):
            path=Path(dist.locate_file(entry))
            if path.is_file():
                require(path.resolve().is_relative_to(interpreter.parent.parent.resolve()),'build distribution file escapes independently frozen venv')
                files.append([str(entry),sha(runtime_bytes(a,path))])
        rows.append([name,dist.version,files]);found[normalized]=dist.version
    pins={re.sub(r'[-_.]+','-',p.split('==')[0]).lower():p.split('==')[1] for p in profile['packages']}
    require(found==pins and fp(rows)==environment['distributions_sha256'] and len(rows)==environment['distribution_count'],
            'metadata build package closure or actual bytes differ')
    require(environment['prefix']==str(interpreter.parent.parent)
            and environment['base_prefix']==record['identity']['base_prefix']
            and environment['pytest_version']==profile['pytest_version'], 'metadata retained environment/profile context differs')
    pytest=site/'pytest/__init__.py'
    require(environment['pytest_import']=={'path':str(pytest.resolve()),'sha256':sha(a.read(pytest.resolve()))},
            'metadata build pytest import identity differs')
    return {'environment':environment}


def _replay_selection(files,catalog,observation):
    """Trusted pure selector replay after independent artifact checks; no minting."""
    from research.unified_consequence_runtime import native_environment_selection_v44 as selector
    digest=fp(observation)
    def verified(value):
        require(fp(value)==digest,'selection replay receives another independently checked observation');return value
    proxy=SimpleNamespace(**dict(vars(selector.metadata),require_verified=verified,
        validate_observation=lambda *args,**kwargs: observation['metadata']))
    context=dict(vars(selector),metadata=proxy)
    view=FunctionType(selector._view.__code__,context,'_view',selector._view.__defaults__,selector._view.__closure__)
    context['_view']=view
    derive=FunctionType(selector.derive_constraints.__code__,context,'derive_constraints',selector.derive_constraints.__defaults__)
    context['derive_constraints']=derive
    select=FunctionType(selector.select_profile.__code__,context,'select_profile',selector.select_profile.__defaults__)
    return select(files,catalog,observation)


def _bootstrap_attempts(a,case,report):
    before,after=(report['bootstrap_attempts'][key] for key in ('before','after'))
    rows=after['records'][len(before['records']):];calls=0;seconds=0.0;seen=set()
    for row in rows:
        require(row['schema']=='UDM_SOURCE_NATIVE_METADATA_BUILD_ATTEMPT_V44'
                and row['phase'] in ('observe','verify') and number(row['seconds']), 'invalid original metadata attempt record')
        output=Path(row['output']);require(output.is_relative_to(case) and str(output) not in seen,'metadata build attempt outside case or duplicated')
        seen.add(str(output));path=output/'build-attempt.json'
        if row['build_calls']:
            original=a.js(path)
            require(row['build_calls']==1 and original==row['original_attempt'] and original['schema']=='udm.generic-build-attempt.v1'
                    and original['build_calls']==1 and original['build_seconds']==row['build_seconds']
                    and original['status']==row['status'],'actual original metadata launch accounting differs')
        else:require(row['build_calls']==0 and row['original_attempt'] is None and not path.exists(),'missing/forged metadata native launch')
        require(number(row['build_seconds']),'invalid metadata build time');calls+=row['build_calls'];seconds+=row['build_seconds']
    costs=bootstrap_costs(report)
    require(calls==costs['backend_calls'] and math.isclose(seconds,costs['backend_seconds'],abs_tol=1e-7),
            'all refused and successful metadata backend launches must be charged')
    return costs


def audit_ledger(a,case,spec,report,authority_sha):
    base=old.audit_ledger(a,case,spec,report,authority_sha)
    _bootstrap_attempts(a,case,report)
    store=LocalStore(case,a);source=SourceStore(_ARGS.repo,a)
    rows,objects,root=proof.old.audit_ledger(str(case/'machine-state/metatron-ledger.jsonl'),store,
        lambda name,ok,detail=None: (require(ok,name),a.check(name,ok,detail))[1])
    observations=[value for value in objects.values() if isinstance(value,dict)
                  and value.get('schema')=='UDM_SOURCE_NATIVE_METADATA_OBSERVATION_V44']
    runtime=old.load_helper('raw_identity.py')
    inventory=a.js(case.with_name(case.name+'.RUNTIME_INVENTORY.json'))
    catalog=a.bound(_CONTEXT_PROTOCOL['catalog'],_ARGS.repo)
    known={str(i):_profile_environment(a,runtime,o,inventory,catalog) for i,o in enumerate(observations)}
    # Screening neither learns native candidates nor withdraws/restores them.
    # Those causal experiments remain an independent prerequisite gate.
    require(not any(r['kind']=='revoke' or r['kind']=='native_frontier_v2_probe'
            or r['kind']=='executable_capability' and r['payload'].get('operation')=='native.pytest_suite' for r in rows),
            'candidate search/revocation occurred inside admission-only screening')
    text=inspect.getsource(proof.audit_causal)
    original="check('metadata_causality_nonvacuous',bool(metadata_caps) and bool(native_caps) and bool(withdrawals))"
    replacement="check('screening_metadata_scope_closed',not native_caps and not withdrawals)"
    require(text.count(original)==1,'pinned metadata audit scope binding changed')
    namespace=dict(vars(proof));exec(compile(text.replace(original,replacement),str(HERE/'audit_retained_v44.py')+':screening-only-proof','exec'),namespace)
    checked=namespace['audit_causal'](source,store,{'profile_identities':known},{'receipts':[],'certificates':[]},
        lambda name,ok,detail=None: (require(ok,name),a.check(name,ok,detail))[1])
    setup=report.get('setup',{});binding=setup.get('bootstrap_binding')
    if binding is not None:
        nodes={r['id']:r for r in rows};witness=nodes[binding['consequence_id']]
        receipt=objects[witness['payload']['receipt']];invocation=objects[receipt['invocation']]
        request=objects[invocation['request']];observation=objects[invocation['observation']]
        cap=nodes[binding['capability_id']]['payload'];selected=nodes[binding['environment_selection_id']]
        validate_invocation_binding(binding,cap,witness,receipt,request)
        contract,authority,policy=[setup[k] for k in ('contract','authority','policy')]
        validate_binding(binding,dict(capability_id=nodes[binding['capability_id']]['id'],generation=cap['generation'],
            consequence_id=witness['id'],request_sha256=fp(request),observation_sha256=fp(observation),
            request=request,observation=observation,live_ids=proof.live_nodes(rows),selected=selected,
            contract_sha256=fp(contract),authority_sha256=fp(authority),policy_sha256=fp(policy),
            base_commit=spec['base_commit'],protocol_binding=authority_sha,baseline_source=authority['baseline_source']))
        record=selected['payload'];require(record['environment_operation_sha256']==sha(source.raw(proof.PREFIX+'native_environment_v44.py')),
            'selected environment was produced by another operation')
        selected_catalog=objects[record['catalog']];choice=objects[record['selection']]
        require(selected_catalog==catalog and choice==setup['selection'] and choice['selected_profile']==record['profile'],
                'selected metadata environment/catalog differs from source setup')
        raw=runtime.raw_snapshot(request['repo_path'],request['commit'])
        require(_replay_selection(raw['files'],catalog,observation)==choice,
                'original pure finite profile selection does not follow independently checked source-native observation')
    return dict(base,metadata_capabilities=checked['metadata_capabilities'],
                metadata_observations=list(checked['observations']),selected_environment_binding=binding,
                bootstrap_costs=bootstrap_costs(report))


def main():
    global _ARGS,_CONTEXT_PROTOCOL
    import argparse
    parser=argparse.ArgumentParser(add_help=False)
    for name in ('repo','records'):parser.add_argument('--'+name,type=Path,required=True)
    _ARGS,_=parser.parse_known_args()
    _CONTEXT_PROTOCOL=json.loads((_ARGS.records/'FRONTIER_PROTOCOL.json').read_text())
    verify_freeze()
    sys.path.insert(0,str(_ARGS.repo.resolve()))
    from research.unified_consequence_runtime import qualify_native_frontier_v44 as controller
    controller.require_environment_gate(_CONTEXT_PROTOCOL)
    namespace=dict(vars(old),public_fields=public_fields,validate_meter=validate_meter,audit_metadata=audit_metadata,audit_ledger=audit_ledger,
                   verify_freeze=verify_freeze,bootstrap_costs=bootstrap_costs)
    text=inspect.getsource(old.main)
    changes=[('a=Audit();result=None','verify_freeze();a=Audit();result=None'),
        ("for key in ('environment_gate','interface_gate','interface_archive_audit'):",
         "for key in ('environment_gate','interface_gate','interface_archive_audit','bootstrap_gate','bootstrap_archive_audit'):"),
        ("'verification_attempts':sum(e['build_costs']['verification_attempts'] for e in envelopes),",
         "'verification_attempts':sum(e['build_costs']['verification_attempts'] for e in envelopes),\n                'metadata_backend_calls':sum(e['bootstrap_costs']['backend_calls'] for e in envelopes),\n                'metadata_backend_seconds':sum(e['bootstrap_costs']['backend_seconds'] for e in envelopes),")]
    for before,after in changes:
        require(text.count(before)==1,'original main binding site differs: '+before);text=text.replace(before,after)
    exec(compile(text,str(HERE/'audit_retained_v44.py')+':original-supplied-run-binding','exec'),namespace)
    bound=_bind(namespace['main'],namespace)
    return bound()


if __name__=='__main__':main()
