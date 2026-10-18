"""Source-derived environment choice, then the unchanged v2 provisioning code.

The external catalog and runtime inventory are frozen by the independent caller.
Selection never supplies execution evidence or widens the research authority.
"""
from __future__ import annotations
import json
import importlib.metadata
from pathlib import Path
import sys
import time
import types

from . import native_environment_v2 as previous
from . import native_environment_selection_v3 as selection
from . import native_execution_v3 as execution
from .decisive_task_admission import _validate_spec
from .decisive_native_verify import _snapshot, canonical, fingerprint, sha256
from .qualify_recursive_frontier import _command

PREVIOUS_SHA256='33d6f2a8905d1e1bb054c0f105c9ef92aab3e15adac9f8eee3bb1423cd15732d'
_LOADED_SHA256=sha256(Path(__file__).read_bytes())


def _guard():
    if sha256(Path(previous.__file__).read_bytes())!=PREVIOUS_SHA256 or sha256(Path(__file__).read_bytes())!=_LOADED_SHA256:
        raise ValueError('UNKNOWN_ENVIRONMENT_OPERATION_SOURCE_CHANGED')
    execution._runner_hash()


def freeze_runtime(interpreter):
    _guard();path=Path(interpreter).absolute()
    if not path.is_file():raise ValueError('runtime interpreter unavailable')
    identity=execution.runtime_identity(str(path))
    result=execution.frozen.subprocess.run([str(path),'-I','-B','-c',
        "import json,sysconfig;print(json.dumps([sysconfig.get_path('stdlib'),sysconfig.get_path('platstdlib'),sysconfig.get_config_var('DESTSHARED')]))"],
        env=execution.frozen.original._env('/nonexistent'),capture_output=True,text=True,timeout=60)
    if result.returncode:raise ValueError('runtime identity import roots unavailable')
    roots=sorted({str(Path(p).resolve()) for p in json.loads(result.stdout) if p})
    record={'interpreter':str(path),'identity':identity,'import_roots':roots,'stdlib_files':_host_stdlib(roots)}
    _validate_host_runtime(record,path)
    return record


def _host_stdlib(roots):
    return execution.host_stdlib(roots)


def _validate_host_runtime(record,interpreter):
    if sha256(Path(interpreter).read_bytes())!=record['identity']['executable_sha256']:
        raise ValueError('frozen runtime identity executable differs from host bytes')
    files=_host_stdlib(record['import_roots'])
    if files!=record['stdlib_files'] or fingerprint(files)!=record['identity']['stdlib_manifest_sha256']:
        raise ValueError('frozen runtime identity differs from host standard-library bytes')


def validate_runtime(profile,record,*,interpreter=None):
    _guard()
    if not isinstance(record,dict) or set(record)!={'interpreter','identity','import_roots','stdlib_files'}:
        raise ValueError('wrong independently frozen runtime identity')
    path=record['interpreter'] if interpreter is None else interpreter
    _validate_host_runtime(record,path)
    actual=execution.runtime_identity(path)
    _validate_host_runtime(record,path)
    if actual!=record['identity']:raise ValueError('frozen runtime identity differs from executable or stdlib')
    version='.'.join(str(x) for x in actual['version_info'][:3])
    if version!=profile['python_version'] or actual['implementation'].lower()!=profile['python_implementation'].lower():
        raise ValueError('runtime version or implementation differs from profile')
    return actual


def installed_package_identity(interpreter,profile):
    """Independently inspect installed pinned files without importing child code."""
    venv=Path(interpreter).absolute().parent.parent
    site=venv/'lib'/('python'+'.'.join(profile['python_version'].split('.')[:2]))/'site-packages'
    expected={selection.canonicalize_name(selection.Requirement(pin).name):str(next(iter(selection.Requirement(pin).specifier)).version) for pin in profile['packages']}
    found={};rows=[]
    for dist in importlib.metadata.distributions(path=[str(site)]):
        name=selection.canonicalize_name(dist.metadata['Name'] or '')
        if name not in expected:continue
        if name in found or dist.version!=expected[name]:raise ValueError('pinned distribution version or uniqueness differs: '+name)
        found[name]=dist.version;files=[]
        if not dist.files:raise ValueError('pinned distribution file authority absent: '+name)
        for entry in sorted(dist.files,key=str):
            path=Path(dist.locate_file(entry)).absolute()
            if not path.resolve().is_relative_to(venv.resolve()) or not path.is_file():
                raise ValueError('pinned distribution file unavailable or outside environment: '+name)
            files.append([str(entry),sha256(path.read_bytes())])
        rows.append([name,dist.version,files])
    if found!=expected:raise ValueError('pinned distribution inventory differs from catalog')
    return sorted(rows)


def package_requirements(profile):
    artifacts=profile.get('package_artifacts',{});lines=[]
    names={selection.canonicalize_name(selection.Requirement(pin).name) for pin in profile['packages']}
    if set(artifacts)!=names:raise ValueError('exact independent package artifact inventory required')
    for pin in profile['packages']:
        name=selection.canonicalize_name(selection.Requirement(pin).name);digest=artifacts[name].get('sha256','')
        if not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('invalid independent package artifact digest')
        lines.append(pin+' --hash=sha256:'+digest)
    return '\n'.join(lines)+'\n'


def execution_policy(profile,*,collection_seconds=60,execution_seconds=600):
    return {'schema':execution.POLICY_SCHEMA,'collection_seconds':collection_seconds,
            'execution_seconds':execution_seconds,'pytest_version':profile['pytest_version'],
            'plugins':json.loads(canonical(profile['plugins']))}


def bound_provision(interpreter,*,profile=None,runtime_record=None,package_checkpoint=None,requirements_path=None):
    """Reuse exact previous function bytecode with isolated explicit dependencies."""
    _guard();namespace=dict(previous.__dict__)
    def no_bytecode(argv,out,**kwargs):
        if requirements_path is not None and Path(out).name=='fixed-packages.log':
            pins=profile['packages']
            if list(argv[-len(pins):])!=pins:raise ValueError('fixed package install invocation changed')
            argv=[*argv[:-len(pins)],'--require-hashes','--only-binary=:all:','-r',requirements_path]
        result=_command(['env','PYTHONDONTWRITEBYTECODE=1',*argv],out,**kwargs)
        if profile is not None and result['status']=='PASS' and Path(out).name=='fixed-packages.log':
            validate_runtime(profile,runtime_record,interpreter=argv[0])
            package_checkpoint['before']=installed_package_identity(argv[0],profile)
        return result
    def checked_identity(path):
        if profile is not None:validate_runtime(profile,runtime_record,interpreter=path)
        return execution.environment_identity(path)
    namespace.update(sys=types.SimpleNamespace(executable=str(interpreter)),execution=execution,
        environment_identity=checked_identity if profile is not None else execution.environment_identity,_command=no_bytecode)
    for name,value in previous.__dict__.items():
        if isinstance(value,types.FunctionType) and value.__module__==previous.__name__:
            rebound=types.FunctionType(value.__code__,namespace,value.__name__,value.__defaults__,value.__closure__)
            rebound.__kwdefaults__=value.__kwdefaults__;namespace[name]=rebound
    return namespace['provision']


def provision(spec,root,protocol_binding,*,catalog,runtimes,collection_seconds=60,execution_seconds=600):
    """Select from original base metadata; retain every refusal and setup cost."""
    started=time.monotonic();_guard()
    profiles={p['id']:p for p in selection._catalog(catalog)}
    if not isinstance(runtimes,dict) or set(runtimes)-set(profiles):raise ValueError('unknown external runtime inventory')
    # Validate externally supplied identities before any source transport or filesystem mutation.
    for ident,record in runtimes.items():validate_runtime(profiles[ident],record)
    repository,base,head,_=_validate_spec(spec)
    if not isinstance(protocol_binding,str) or len(protocol_binding)!=64 or any(c not in '0123456789abcdef' for c in protocol_binding):
        raise ValueError('exact frozen protocol binding required')
    root=Path(root).absolute()
    if root.resolve()!=root or root.exists():raise ValueError('new canonical environment selection directory required')
    root.mkdir(parents=True);costs=[{'phase':'external-runtime-preflight','seconds':time.monotonic()-started,'native_calls':0,'status':'PASS'}];receipt=None;source=root/'metadata-source'
    result={'schema':'UDM_SOURCE_ENVIRONMENT_ADMISSION_V3','status':'UNKNOWN','selection':None,
            'costs':costs,'runtime':None,'source_metadata_identity':None,'setup':None}
    def save(status,reason=None):
        result.update(status=status,total_wall_seconds=time.monotonic()-started)
        if reason:result['reason']=reason
        (root/'admission-v3.json').write_text(canonical(result)+'\n');return result
    def command(argv,label):
        before=time.monotonic();row=_command(['env','PYTHONDONTWRITEBYTECODE=1',*argv],root/(label+'.log'))
        costs.append({'phase':label,'argv':[str(x) for x in argv],**row})
        if row['status']!='PASS':raise ValueError('UNKNOWN_SOURCE_TRANSPORT:'+label)
    try:
        command(['git','init','-q',source],'metadata-init')
        command(['git','-C',source,'fetch','--depth=1','--no-tags','https://github.com/'+repository+'.git',base],'metadata-fetch')
        command(['git','-C',source,'checkout','-q','--detach',base],'metadata-checkout')
        identity,files,manifest=_snapshot(source,base);result['source_metadata_identity']=identity
        (root/'metadata-source.tar.gz').write_bytes(previous.tracked_archive(files,manifest))
        before=time.monotonic();chosen=selection.select_profile(files,catalog)
        selection.validate_selection(files,catalog,chosen)
        costs.append({'phase':'independent-metadata-selection','seconds':time.monotonic()-before,'native_calls':0,'status':chosen['status']})
        result['selection']=chosen;(root/'selection.json').write_text(canonical(chosen)+'\n')
        if chosen['status']!='CANDIDATE_SOURCE_ENVIRONMENT':return save('UNKNOWN_ENVIRONMENT_SELECTION',chosen['reason'])
        profile=chosen['selected_profile'];ident=profile['id']
        if ident not in runtimes:return save('UNKNOWN_INTERPRETER_UNAVAILABLE',ident)
        before=time.monotonic();result['runtime']=runtimes[ident]
        validate_runtime(profile,runtimes[ident]);policy=execution_policy(profile,collection_seconds=collection_seconds,execution_seconds=execution_seconds)
        costs.append({'phase':'independent-runtime-identity','seconds':time.monotonic()-before,'native_calls':0,'status':'PASS'})
        checkpoint={}
        requirements=root/'pinned-requirements.txt';requirements.write_text(package_requirements(profile))
        receipt=bound_provision(runtimes[ident]['interpreter'],profile=profile,runtime_record=runtimes[ident],package_checkpoint=checkpoint,requirements_path=requirements)(spec,root/'native',protocol_binding,policy=policy,packages=profile['packages'])
        result['setup']=receipt
        result['costs'].extend(receipt.get('costs',[]))
        # The original native materialization must be byte-identical to metadata used for choice.
        if receipt.get('source_boundaries',{}).get('base_identity')!=identity:
            return save('UNKNOWN_METADATA_SOURCE_CHANGED','native source differs from independently selected base')
        validate_runtime(profile,runtimes[ident]);_guard()
        if receipt['status']!='PREPARED':return save(receipt['status'],receipt.get('reason'))
        validate_runtime(profile,runtimes[ident],interpreter=receipt['contract']['interpreter'])
        installed=installed_package_identity(receipt['contract']['interpreter'],profile)
        if checkpoint.get('before')!=installed:return save('UNKNOWN_PINNED_ENVIRONMENT_CHANGED','project build or install changed externally pinned package bytes')
        result['pinned_packages_sha256']=fingerprint(installed)
        (root/'pinned-package-files.json').write_text(canonical(installed)+'\n')
        result.update({key:receipt[key] for key in ('contract','authority','policy','source_boundaries')})
        return save('PREPARED')
    except (ValueError,RuntimeError,OSError,KeyError) as error:
        return save('UNKNOWN_SOURCE_ENVIRONMENT',type(error).__name__+': '+str(error))
