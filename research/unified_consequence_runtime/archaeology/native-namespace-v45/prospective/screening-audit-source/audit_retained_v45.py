"""V45 independent screening transport over exact original V44 predicates.

Source/native/build/metadata checks remain the original algorithms. Added
namespace authority reuses the independently frozen V45 AST/C3 source checker
and pure compiler; compiled original test code is never executed by this audit.
"""
from __future__ import annotations
import argparse
import base64
import copy
import hashlib
import importlib.util
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from types import CodeType, FunctionType, SimpleNamespace

HERE=Path(__file__).resolve().parent
ORIGINAL=Path('/workspace/qualification/native-bootstrap-v44-screening-audit-preparation')
SOURCE_PINS=json.loads((ORIGINAL/'AUDITOR_FREEZE.json').read_text())['source_files_sha256']


def sha(raw):return hashlib.sha256(raw).hexdigest()


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[name]=module
    spec.loader.exec_module(module);return module


for _path,_pin in SOURCE_PINS.items():
    if sha(Path(_path).read_bytes())!=_pin:raise ValueError('original auditor dependency differs: '+_path)
previous=load(ORIGINAL/'audit_retained_v44.py','_original_v44_screening_authority')
authority_checker=load(HERE/'source_authority.py','_v45_screening_independent_source')
declaration_audit=load(HERE/'audit_artifact.py','_v45_screening_independent_declaration')
canonical,fp,require=previous.canonical,previous.fp,previous.require
_OUTER={
    'UDM_ADMISSION_ONLY_CASE_V43':'UDM_ADMISSION_ONLY_CASE_V45',
    'UDM_ADMISSION_ONLY_CASE_V44':'UDM_ADMISSION_ONLY_CASE_V45',
    'UDM_SEALED_ADMISSION_ENVELOPE_V43':'UDM_SEALED_ADMISSION_ENVELOPE_V45',
    'UDM_SEALED_ADMISSION_ENVELOPE_V44':'UDM_SEALED_ADMISSION_ENVELOPE_V45',
    'UDM_ORDERED_SCREENING_METER_V43':'UDM_ORDERED_SCREENING_METER_V45',
    'UDM_ORDERED_SCREENING_METER_V44':'UDM_ORDERED_SCREENING_METER_V45',
    'UDM_NATIVE_CLI_AUTHORITY_V43':'UDM_NATIVE_CLI_AUTHORITY_V45',
    'UDM_NATIVE_CLI_AUTHORITY_V44':'UDM_NATIVE_CLI_AUTHORITY_V45',
    'UDM_V43_OFFLINE_RETAINED_SCREENING_DOSSIER_V1':'UDM_V45_OFFLINE_RETAINED_SCREENING_DOSSIER_V1',
    'UDM_V44_OFFLINE_RETAINED_SCREENING_DOSSIER_V1':'UDM_V45_OFFLINE_RETAINED_SCREENING_DOSSIER_V1',
    'UDM_NATIVE_ADMISSION_CERTIFICATE_V43':'UDM_NATIVE_ADMISSION_CERTIFICATE_V45',
    'UDM_GENERIC_NATIVE_PYTEST_V43':'UDM_GENERIC_NATIVE_PYTEST_V45',
    'research/unified_consequence_runtime/native_execution_v43.py':'research/unified_consequence_runtime/native_execution_v45.py',
    'native_environment_v44.py':'native_environment_v45.py',
}


def transport_literal(value):return _OUTER.get(value,value)


def code(value,extra=None):
    substitutions=dict(_OUTER,**(extra or {}))
    return value.replace(co_consts=tuple(code(v,extra) if isinstance(v,CodeType) else
        substitutions.get(v,v) if isinstance(v,str) else v for v in value.co_consts),
        co_names=tuple('native_execution_v45' if v=='native_execution_v43' else v for v in value.co_names))


def bind(function,namespace,extra=None):
    f=FunctionType(code(function.__code__,extra),namespace,function.__name__,function.__defaults__,function.__closure__)
    f.__kwdefaults__=function.__kwdefaults__;return f


_raw=previous.old
_old_globals=dict(vars(_raw))
for _name,_value in vars(_raw).items():
    if isinstance(_value,FunctionType) and _value.__module__==_raw.__name__:
        _old_globals[_name]=bind(_value,_old_globals,{'4.3':'4.5'} if _name=='audit_native' else None)
old=SimpleNamespace(**_old_globals)
archive=load(Path(_raw.HERE)/'original/archive_audit_v43.py','_v45_screening_original_archive')
archive.receipt_identity_matches=bind(archive.receipt_identity_matches,dict(vars(archive)),{'43':'45'})
_identity=load(Path(_raw.HERE)/'raw_identity.py','_v45_screening_original_identity')
_identity_globals=dict(vars(_identity))
for _name,_value in vars(_identity).items():
    if isinstance(_value,FunctionType) and _value.__module__==_identity.__name__:
        _identity_globals[_name]=FunctionType(_value.__code__,_identity_globals,_name,_value.__defaults__,_value.__closure__)
        _identity_globals[_name].__kwdefaults__=_value.__kwdefaults__


def derive_authority(before,after,base,augmented,binding,repository):
    identity={'repository':repository,'source_commit':augmented,'baseline_commit':base,'protocol_binding':binding,
              'source':after['identity'],'baseline_source':before['identity']}
    modes={row['path']:row['mode'] for row in after['manifest']}
    base_modes={row['path']:row['mode'] for row in before['manifest']}
    expected=authority_checker.derive(after['files'],before['files'],modes,base_modes,identity)
    return dict(expected,**identity)


_identity_globals['derive_authority']=derive_authority
identity=SimpleNamespace(**_identity_globals)


def load_helper(name):
    if name=='raw_identity.py':return identity
    if name=='original/archive_audit_v43.py':return archive
    return _raw.load_helper(name)


_old_globals['load_helper']=load_helper
old=SimpleNamespace(**_old_globals)
for _name,_value in vars(previous).items():
    if not _name.startswith('__'):globals().setdefault(_name,_value)
for _name,_value in vars(previous).items():
    if isinstance(_value,FunctionType) and _value.__module__==previous.__name__ and _name not in ('main','verify_freeze','audit_metadata'):
        globals()[_name]=bind(_value,globals())
_public=bind(previous._public,_old_globals)
validate_meter=bind(previous.validate_meter,_old_globals)
validate_context_bytes=old.validate_context_bytes
audit_partial_packets=old.audit_partial_packets
_COMPILE_EVENTS=[]
_NAMESPACE_CASES=[]
_ARGS=None
_CONTEXT_PROTOCOL=None


def verify_freeze():
    previous.verify_freeze()
    frozen=json.loads((HERE/'AUDITOR_FREEZE.json').read_text())
    for name,digest in frozen['source_files_sha256'].items():
        require(sha(Path(name).read_bytes())==digest,'frozen V45 auditor source differs: '+name)


def validate_supplemental_exposure(plan,prior,addendum):
    previous.validate_exposure(plan,prior)
    names=addendum['repositories']
    require(names==sorted(set(names)) and addendum['repository_count']==len(names)
            and set(prior['repositories'])<=set(names),'supplemental prior union omits or duplicates identities')
    require(not set(names)&set(plan['repository_universe_fixed_before_github_queries']),
            'supplemental documented exposure reused as prospective source')


def audit_metadata(plan,pre,metadata,pool):
    prior=json.loads((_ARGS.records/'PRIOR_EXPOSURE.json').read_text())
    raw=(HERE/'PRIOR_EXPOSURE_ROS_ADDENDUM.json').read_bytes()
    require(sha(raw)=='941fce7f840fac5855bfe27029a833c3dda08729a5d40e9004f702740ee4af9d',
            'prequery supplemental ROS exposure bytes differ')
    validate_supplemental_exposure(plan,prior,json.loads(raw))
    return _raw.audit_metadata(plan,pre,metadata,pool)


def audit_source_index_interval(a,operator,controller,*,current):
    """Authenticate original retained interval bytes; never restore an index."""
    from research.unified_consequence_runtime.audit_index_v4 import compare_indexes
    operator=Path(operator)
    report=a.js(operator/'SOURCE_INDEX_SCREENING_AUDIT.json')
    require(report.get('status')=='PASS_SOURCE_AND_INDEX_BYTES' and report.get('source_unchanged') is True
        and report.get('index_changes')==[] and report.get('restored_any_index') is False,
        'original screening source/index interval is unclosed or restored')
    source=a.bound(controller['source_snapshot'])
    require(a.js(operator/'SCREENING_SOURCE_AFTER.json')==source,'original after-source snapshot differs')
    snapshots=[]
    for phase in ('before','after'):
        folder=operator/('source-index-'+phase+'-screening');snapshot=a.js(folder/'SNAPSHOT.json')
        require(snapshot==report[phase+'_indexes'],'retained index snapshot differs from original interval')
        require(snapshot.get('schema')=='UDM_GIT_INDEX_SNAPSHOT_V4'
            and len({r['path'] for r in snapshot['indexes']})==len(snapshot['indexes']),
            'original index inventory is invalid or duplicates paths')
        expected=set()
        for number,row in enumerate(snapshot['indexes']):
            if row['exists'] is True:
                path=folder/('index-'+str(number)+'.bytes');raw=a.read(path);expected.add(path.name)
                require(type(row['size_bytes']) is int and len(raw)==row['size_bytes'] and sha(raw)==row['sha256'],
                        'retained original pre/post index bytes differ')
            else:require(row['exists'] is False and row['size_bytes'] is None and row['sha256'] is None,
                         'absent original index has forged byte identity')
        require({p.name for p in folder.glob('index-*.bytes')}==expected,'retained index byte inventory differs')
        snapshots.append(snapshot)
    require(not compare_indexes(*snapshots) and not compare_indexes(snapshots[1],current),
            'original source index bytes changed before, during or after screening')
    a.check('authenticated_original_source_index_interval',True)
    return {'status':'PASS_AUTHENTICATED_ORIGINAL_SOURCE_INDEX_INTERVAL','source_files':len(source['files']),
            'index_paths':len(snapshots[0]['indexes']),'restored_any_index':False}


def _audit_original_source_index(a,controller,path):
    from research.unified_consequence_runtime.audit_index_v4 import snapshot_indexes
    return audit_source_index_interval(a,Path(path).parent,controller,current=snapshot_indexes(_ARGS.repo))


def select_compiler_profile(setup,env,runtimes):
    """Select the actual case venv after original raw-runtime/package closure.

    The frozen host profile supplies the interpreter image. Provisioning creates
    a distinct case venv and package root; its exact certificate-bound paths are
    the compiler environment, without claiming path equality to the host profile.
    """
    profile=setup['selection']['selected_profile']
    require(profile['id'] in runtimes,'selected host compiler profile is missing')
    host=Path(runtimes[profile['id']]).absolute()
    interpreter=Path(setup['contract']['interpreter']).absolute()
    require(str(interpreter)==setup['contract']['interpreter']==env['executable']
            and interpreter.is_file() and host.is_file()
            and sha(interpreter.read_bytes())==env['executable_sha256']==sha(host.read_bytes()),
            'selected original case compiler image or environment binding differs')
    site=interpreter.parent.parent/'lib'/('python'+'.'.join(profile['python_version'].split('.')[:2]))/'site-packages'
    package_code={p.relative_to(site).as_posix():sha(p.read_bytes()) for p in (site/'_pytest').rglob('*.py')}
    package=site/'pytest'
    if package.is_dir():package_code.update({p.relative_to(site).as_posix():sha(p.read_bytes()) for p in package.rglob('*.py')})
    else:package_code['pytest.py']=sha((site/'pytest.py').read_bytes())
    return {'profile':profile,'interpreter':str(interpreter),'site':str(site),'environment':env,
            'authenticated_python_source':package_code}


def _namespace(a,case,setup,source,certificates,receipts):
    authority=setup['authority'];expected=source['rederived_authority']
    require(authority_checker.validate({k:expected[k] for k in authority_checker.DERIVED_KEYS},authority)['ok'],
            'independent original namespace authority differs')
    if not certificates:
        require(not setup.get('_eligible'),'eligible source has no native certificate')
        _NAMESPACE_CASES.append({'case':str(case),'status':'REFUSED_NO_CERTIFICATE','eligible':False})
        return
    cert=next(iter(certificates.values()));env=cert['environment']
    selected=select_compiler_profile(setup,env,json.loads(_ARGS.compiler_runtimes.read_text()))
    interpreter=Path(selected['interpreter']);profile=selected['profile']
    payload={'sources':{},'profile':{k:profile[k] for k in ('python_version','pytest_version')}}
    for prefix,row in expected['namespace_certificate']['required_declarations'].items():
        raw=source['files'][row['path']]
        item=payload['sources'].setdefault(row['path'],{'source':base64.b64encode(raw).decode(),
            'source_sha256':sha(raw),'origins':{}})
        item['origins'][prefix]=row['origin']
    out=_ARGS.out/'namespace-compilations'/case.name;out.mkdir(parents=True,exist_ok=False)
    (out/'input.json').write_text(canonical(payload)+'\n')
    helper=HERE/'fresh_compile.py';command=[str(interpreter),'-I','-B',str(helper),str(out/'input.json'),str(out/'output.json')]
    event={'case':str(case),'command':command,'started':time.monotonic(),'status':'ATTEMPTED_PURE_COMPILE',
           'input_sha256':sha((out/'input.json').read_bytes()),'native_test_execution':False}
    _COMPILE_EVENTS.append(event)
    try:
        process=subprocess.run(command,env={'PATH':'/usr/bin:/bin','HOME':str(out),
            'PYTHONDONTWRITEBYTECODE':'1','PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1'},cwd=out,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
        (out/'stdout.log').write_bytes(process.stdout);(out/'stderr.log').write_bytes(process.stderr)
        require(process.returncode==0,'independent original declaration compiler failed')
        compiled=json.loads((out/'output.json').read_bytes())
        declaration_audit.validate_tooling(compiled,selected,helper)
        for certificate in certificates.values():
            declaration_audit.validate_collection(certificate['collection'],expected,source['files'])
            declaration_audit.compare_outer(certificate['collection'],expected,compiled)
        for receipt in receipts:
            value=a.js(Path(receipt['path']))
            if value['status'] in ('PASS_NATIVE','FAIL_NATIVE'):
                declaration_audit.compare_outer(value['execution'],expected,compiled)
                receipt['namespace_compilation']={'path':str(out/'output.json'),'sha256':sha((out/'output.json').read_bytes())}
            else:require(not setup.get('_eligible'),'UNKNOWN namespace cannot authorize eligible admission')
        event.update(status='PASS_INDEPENDENT_ORIGINAL_DECLARATION_BINDING',output_sha256=sha((out/'output.json').read_bytes()))
        _NAMESPACE_CASES.append({'case':str(case),'status':'PASS_INDEPENDENT_ORIGINAL_DECLARATION_BINDING',
            'eligible':bool(setup.get('_eligible')),'compiler_output':str(out/'output.json')})
        a.check('independent_v45_namespace:'+case.name,True)
    finally:
        event['seconds']=time.monotonic()-event.pop('started')
        (out/'ATTEMPT.json').write_text(json.dumps(event,sort_keys=True,indent=2)+'\n')


def audit_native(a,case,setup,source,archive,runner):
    certificates,receipts=old.audit_native(a,case,setup,source,archive,runner)
    _namespace(a,case,setup,source,certificates,receipts)
    return certificates,receipts


def require_closed_dossier(value):
    _raw.require_closed_dossier(value)
    require(value.get('namespace_authority_closed') is True and isinstance(value.get('declaration_compilations'),list),
            'independent V45 namespace closure missing')
    outputs={}
    for event in value['declaration_compilations']:
        command=event.get('command',[])
        require(len(command)==6 and command[1:3]==['-I','-B'] and command[3]==str(HERE/'fresh_compile.py')
            and event.get('status')=='PASS_INDEPENDENT_ORIGINAL_DECLARATION_BINDING'
            and event.get('native_test_execution') is False and previous.number(event.get('seconds')),
            'independent compiler attempt is incomplete or has another helper')
        for path,key in ((Path(command[4]),'input_sha256'),(Path(command[5]),'output_sha256')):
            require(path.is_absolute() and path.resolve()==path and path.is_file() and not path.is_symlink()
                and sha(path.read_bytes())==event.get(key),'missing or changed independent compiler artifact')
        outputs[command[5]]=event['output_sha256']
    for case in value.get('cases',[]):
        if case.get('eligible'):
            require(all(r.get('namespace_compilation') for r in case['identity']['native_receipts']),
                    'eligible native receipt lacks independent original declaration compilation')
            for row in case['identity']['native_receipts']:
                descriptor=row['namespace_compilation']
                require(outputs.get(descriptor['path'])==descriptor['sha256'],
                    'eligible native receipt has another independent compiler artifact')


def prepare_main_binding():
    """Compile the original supplied-run audit transport without accessing cases."""
    namespace=dict(vars(old),public_fields=public_fields,validate_meter=validate_meter,audit_metadata=audit_metadata,
        audit_ledger=audit_ledger,audit_native=audit_native,load_helper=load_helper,verify_freeze=verify_freeze,
        bootstrap_costs=bootstrap_costs,_audit_original_source_index=_audit_original_source_index)
    text=inspect.getsource(_raw.main)
    changes=[('a=Audit();result=None','verify_freeze();a=Audit();result=None'),
      ("snapshot=a.bound(controller['source_snapshot'])", "snapshot=a.bound(controller['source_snapshot']);_audit_original_source_index(a,controller,args.controller_manifest)"),
      ("parser=argparse.ArgumentParser(description=__doc__)","parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--compiler-runtimes',type=Path,required=True)"),
      ("for key in ('environment_gate','interface_gate','interface_archive_audit'):",
       "for key in ('environment_gate','interface_gate','interface_archive_audit','bootstrap_gate','bootstrap_archive_audit','namespace_gate','namespace_archive_audit'):"),
      ("'verification_attempts':sum(e['build_costs']['verification_attempts'] for e in envelopes),",
       "'verification_attempts':sum(e['build_costs']['verification_attempts'] for e in envelopes),\n                'metadata_backend_calls':sum(e['bootstrap_costs']['backend_calls'] for e in envelopes),\n                'metadata_backend_seconds':sum(e['bootstrap_costs']['backend_seconds'] for e in envelopes),"),
      ('No target interpreter, backend, pytest or native verifier executed by this audit. Runtime implementation/version claims retain offline evidence limits.',
       'No original tests, backend or native verifier execute in this audit. Exact selected interpreter imports authenticated pytest tooling for pure original-source compilation only. Runtime implementation/version claims retain declared offline limits.')]
    for before,after in changes:
        require(text.count(before)==1,'original main binding site differs: '+before);text=text.replace(before,after)
    exec(compile(text,str(HERE/'audit_retained_v45.py')+':original-supplied-run-binding','exec'),namespace)
    return bind(namespace['main'],namespace)


def main():
    global _ARGS,_CONTEXT_PROTOCOL
    parser=argparse.ArgumentParser(add_help=False)
    for name in ('repo','records','out','compiler-runtimes'):parser.add_argument('--'+name,type=Path,required=True)
    _ARGS,_=parser.parse_known_args();_CONTEXT_PROTOCOL=json.loads((_ARGS.records/'FRONTIER_PROTOCOL.json').read_text())
    verify_freeze();sys.path.insert(0,str(_ARGS.repo.resolve()))
    from research.unified_consequence_runtime.qualify_experiment_interface_v43 import index_interval
    try:
        with index_interval(_ARGS.repo,_ARGS.out.with_name(_ARGS.out.name+'.ROOT_INDEX_INTERVAL')):
            from research.unified_consequence_runtime import qualify_native_frontier_v45 as controller
            controller.require_environment_gate(_CONTEXT_PROTOCOL)
            prepare_main_binding()()
    except Exception as error:
        path=_ARGS.out/'RETAINED_CHECKS.json'
        if path.is_file():
            value=json.loads(path.read_text());value['status']='UNKNOWN_RETAINED_SCREENING_BINDINGS'
            value.setdefault('checks',[]).append({'check':'independent_auditor_source_index_interval',
                'pass':False,'detail':type(error).__name__+': '+str(error)})
            path.write_text(json.dumps(value,sort_keys=True,indent=2)+'\n')
        raise
    path=_ARGS.out/'RETAINED_CHECKS.json';value=json.loads(path.read_text())
    value.update(namespace_cases=_NAMESPACE_CASES,declaration_compilations=_COMPILE_EVENTS,
        namespace_authority_closed=all(c['status'] in ('REFUSED_NO_CERTIFICATE','PASS_INDEPENDENT_ORIGINAL_DECLARATION_BINDING') for c in _NAMESPACE_CASES),
        independent_compile_seconds=sum(row['seconds'] for row in _COMPILE_EVENTS),
        independent_compile_calls=len(_COMPILE_EVENTS),independent_compilation_test_execution=False)
    path.write_text(json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n')


if __name__=='__main__':main()
